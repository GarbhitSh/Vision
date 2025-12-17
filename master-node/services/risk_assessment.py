"""
Risk Assessment Engine
Calculates stampede risk scores based on multiple factors
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import numpy as np

from models.database import Alert
from config.settings import settings
from utils.logger import logger


class RiskAssessmentEngine:
    """Risk assessment engine for stampede prediction"""
    
    def __init__(self):
        """Initialize risk assessment engine"""
        self.critical_threshold = settings.CRITICAL_THRESHOLD
        self.warning_threshold = settings.WARNING_THRESHOLD
    
    def calculate_risk_score(
        self,
        analytics: Dict,
        previous_analytics: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Calculate risk score based on multiple factors
        
        Args:
            analytics: Current analytics data
            previous_analytics: Previous analytics for trend analysis
        
        Returns:
            Dictionary with risk_score and individual factors
        """
        # Factor 1: Density (0-1)
        density_factor = analytics.get("density", 0.0)
        
        # Factor 2: Speed variance (high variance = panic)
        avg_speed = analytics.get("avg_speed", 0.0)
        speed_factor = min(1.0, avg_speed / 100.0)  # Normalize speed
        
        # Factor 3: Congestion
        congestion_level = analytics.get("congestion_level", "low")
        congestion_map = {"low": 0.0, "medium": 0.5, "high": 1.0}
        congestion_factor = congestion_map.get(congestion_level, 0.0)
        
        # Factor 4: Directional conflict (opposing flows)
        flow_direction = analytics.get("flow_direction", {"x": 0.0, "y": 0.0})
        flow_magnitude = np.sqrt(flow_direction["x"]**2 + flow_direction["y"]**2)
        directional_conflict_factor = 0.0
        
        if previous_analytics:
            prev_flow = previous_analytics.get("flow_direction", {"x": 0.0, "y": 0.0})
            # Calculate angle between flows
            dot_product = flow_direction["x"] * prev_flow["x"] + flow_direction["y"] * prev_flow["y"]
            # If flows are opposite (dot product < 0), there's conflict
            if dot_product < 0:
                directional_conflict_factor = abs(dot_product)
        
        # Factor 5: Sudden movement (rapid acceleration)
        sudden_movement_factor = 0.0
        if previous_analytics:
            prev_speed = previous_analytics.get("avg_speed", 0.0)
            speed_change = abs(avg_speed - prev_speed)
            if speed_change > 50:  # Threshold for sudden movement
                sudden_movement_factor = min(1.0, speed_change / 100.0)
        
        # Weighted risk score
        risk_score = (
            0.3 * density_factor +
            0.25 * speed_factor +
            0.2 * congestion_factor +
            0.15 * directional_conflict_factor +
            0.1 * sudden_movement_factor
        )
        
        # Clamp to 0-1
        risk_score = max(0.0, min(1.0, risk_score))
        
        return {
            "risk_score": risk_score,
            "density_factor": density_factor,
            "speed_factor": speed_factor,
            "congestion_factor": congestion_factor,
            "directional_conflict_factor": directional_conflict_factor,
            "sudden_movement_factor": sudden_movement_factor
        }
    
    def get_risk_level(self, risk_score: float) -> str:
        """
        Get risk level from score
        
        Args:
            risk_score: Risk score (0-1)
        
        Returns:
            Risk level: "NORMAL", "WARNING", "CRITICAL"
        """
        if risk_score >= self.critical_threshold:
            return "CRITICAL"
        elif risk_score >= self.warning_threshold:
            return "WARNING"
        else:
            return "NORMAL"
    
    def generate_alert(
        self,
        camera_id: str,
        risk_score: float,
        risk_level: str,
        analytics: Dict,
        db: Session
    ) -> Optional[Alert]:
        """
        Generate alert if risk threshold is exceeded
        
        Args:
            camera_id: Camera identifier
            risk_score: Calculated risk score
            risk_level: Risk level
            analytics: Analytics data
            db: Database session
        
        Returns:
            Alert object if created, None otherwise
        """
        # Only generate alerts for WARNING or CRITICAL
        if risk_level == "NORMAL":
            return None
        
        # Determine alert type
        if risk_level == "CRITICAL":
            alert_type = "stampede_risk"
            message = f"CRITICAL: Stampede risk detected (score: {risk_score:.2f})"
        elif analytics.get("density", 0.0) > 0.7:
            alert_type = "high_density"
            message = f"High crowd density detected: {analytics.get('density', 0.0)*100:.1f}%"
        elif analytics.get("congestion_level") == "high":
            alert_type = "congestion"
            message = "High congestion detected - flow may be blocked"
        else:
            alert_type = "warning"
            message = f"Warning: Elevated risk detected (score: {risk_score:.2f})"
        
        # Create alert
        alert = Alert(
            camera_id=camera_id,
            alert_type=alert_type,
            severity=risk_level,
            risk_score=risk_score,
            message=message,
            timestamp=datetime.utcnow(),
            acknowledged=False
        )
        
        db.add(alert)
        db.flush()
        
        logger.warning(f"Alert generated: {alert_type} - {message}")
        
        return alert

