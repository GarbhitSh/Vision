"""
Analytics Service - Orchestrates analytics computation and storage
"""
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from services.analytics import AnalyticsEngine
from services.risk_assessment import RiskAssessmentEngine
from services.tracking import TrackingService
from models.database import Analytics as AnalyticsModel, Camera, Zone
from utils.logger import logger


class AnalyticsService:
    """Service for computing and managing analytics"""
    
    def __init__(self):
        """Initialize analytics service"""
        self.analytics_engine = AnalyticsEngine()
        self.risk_engine = RiskAssessmentEngine()
        self.tracking_service = TrackingService()
        
        # Store previous analytics per camera
        self.previous_analytics = {}  # camera_id -> analytics dict
        self.previous_tracks = {}  # camera_id -> tracks dict
    
    def compute_analytics(
        self,
        camera_id: str,
        detections: List[Dict],
        tracks: List[Dict],
        frame_width: int,
        frame_height: int,
        fps: float = 30.0,
        db: Optional[Session] = None
    ) -> Dict:
        """
        Compute analytics for current frame
        
        Args:
            camera_id: Camera identifier
            detections: List of detections
            tracks: List of tracked objects
            frame_width: Frame width
            frame_height: Frame height
            fps: Frames per second
            db: Database session (optional)
        
        Returns:
            Analytics dictionary with risk score
        """
        # Get zones for camera
        zones = []
        if db:
            db_zones = db.query(Zone).filter(
                Zone.camera_id == camera_id,
                Zone.status == "active"
            ).all()
            zones = [
                {
                    "id": z.id,
                    "polygon_coords": json.loads(z.polygon_coords) if isinstance(z.polygon_coords, str) else z.polygon_coords,
                    "max_capacity": z.max_capacity
                }
                for z in db_zones
            ]
        
        # Get previous tracks for flow calculation
        prev_tracks_dict = {}
        if camera_id in self.previous_tracks:
            for track in self.previous_tracks[camera_id]:
                prev_tracks_dict[track["track_id"]] = track
        
        # Calculate analytics
        analytics = self.analytics_engine.calculate_analytics(
            detections=detections,
            tracks=tracks,
            previous_tracks=prev_tracks_dict,
            zones=zones,
            frame_width=frame_width,
            frame_height=frame_height,
            fps=fps
        )
        
        # Calculate risk score
        previous_analytics = self.previous_analytics.get(camera_id)
        risk_data = self.risk_engine.calculate_risk_score(
            analytics=analytics,
            previous_analytics=previous_analytics
        )
        
        # Add risk data to analytics
        analytics["risk_score"] = risk_data["risk_score"]
        analytics["risk_level"] = self.risk_engine.get_risk_level(risk_data["risk_score"])
        
        # Store current analytics as previous
        self.previous_analytics[camera_id] = analytics.copy()
        self.previous_tracks[camera_id] = tracks.copy()
        
        # Store in database if session provided
        if db:
            self._store_analytics(db, camera_id, analytics)
        
        return analytics
    
    def _store_analytics(self, db: Session, camera_id: str, analytics: Dict):
        """Store analytics in database"""
        try:
            flow_direction = analytics.get("flow_direction", {})
            
            db_analytics = AnalyticsModel(
                camera_id=camera_id,
                timestamp=datetime.utcnow(),
                people_count=analytics.get("people_count", 0),
                density=analytics.get("density", 0.0),
                avg_speed=analytics.get("avg_speed"),
                flow_direction=json.dumps(flow_direction),
                congestion_level=analytics.get("congestion_level", "low")
            )
            
            db.add(db_analytics)
            db.flush()
        except Exception as e:
            logger.error(f"Failed to store analytics: {e}")
    
    def get_realtime_analytics(
        self,
        camera_id: str,
        db: Session
    ) -> Dict:
        """
        Get real-time analytics for camera
        
        Args:
            camera_id: Camera identifier
            db: Database session
        
        Returns:
            Real-time analytics dictionary
        """
        # Get latest analytics from database
        latest = db.query(AnalyticsModel).filter(
            AnalyticsModel.camera_id == camera_id
        ).order_by(AnalyticsModel.timestamp.desc()).first()
        
        if latest:
            flow_direction = json.loads(latest.flow_direction) if isinstance(latest.flow_direction, str) else latest.flow_direction
            
            return {
                "camera_id": camera_id,
                "timestamp": latest.timestamp.isoformat(),
                "people_count": latest.people_count,
                "density": latest.density,
                "avg_speed": latest.avg_speed,
                "flow_direction": flow_direction,
                "congestion_level": latest.congestion_level,
                "risk_score": 0.0,  # Would need to recalculate
                "risk_level": "NORMAL"
            }
        else:
            # Return defaults if no analytics yet
            return {
                "camera_id": camera_id,
                "timestamp": datetime.utcnow().isoformat(),
                "people_count": 0,
                "density": 0.0,
                "avg_speed": 0.0,
                "flow_direction": {"x": 0.0, "y": 0.0},
                "congestion_level": "low",
                "risk_score": 0.0,
                "risk_level": "NORMAL"
            }
    
    def get_historical_analytics(
        self,
        camera_id: str,
        start_time: datetime,
        end_time: datetime,
        interval_seconds: int = 60,
        db: Session = None
    ) -> List[Dict]:
        """
        Get historical analytics data
        
        Args:
            camera_id: Camera identifier
            start_time: Start timestamp
            end_time: End timestamp
            interval_seconds: Aggregation interval
            db: Database session
        
        Returns:
            List of analytics dictionaries
        """
        if not db:
            return []
        
        # Query analytics in time range
        analytics_list = db.query(AnalyticsModel).filter(
            AnalyticsModel.camera_id == camera_id,
            AnalyticsModel.timestamp >= start_time,
            AnalyticsModel.timestamp <= end_time
        ).order_by(AnalyticsModel.timestamp).all()
        
        # Aggregate by interval
        result = []
        current_interval_start = start_time
        
        while current_interval_start < end_time:
            current_interval_end = current_interval_start + timedelta(seconds=interval_seconds)
            
            # Get analytics in this interval
            interval_analytics = [
                a for a in analytics_list
                if current_interval_start <= a.timestamp < current_interval_end
            ]
            
            if interval_analytics:
                # Average values
                avg_density = sum(a.density for a in interval_analytics) / len(interval_analytics)
                avg_speed = sum(a.avg_speed or 0 for a in interval_analytics) / len(interval_analytics)
                avg_people = sum(a.people_count for a in interval_analytics) / len(interval_analytics)
                
                result.append({
                    "timestamp": current_interval_start.isoformat(),
                    "people_count": int(avg_people),
                    "density": float(avg_density),
                    "avg_speed": float(avg_speed),
                    "risk_score": 0.0  # Would need to recalculate
                })
            
            current_interval_start = current_interval_end
        
        return result

