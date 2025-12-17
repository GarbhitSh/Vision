"""
Video Streaming and Annotation Service
Annotates frames with bounding boxes, track IDs, metrics, heatmaps, and zones
"""
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json

from models.database import Zone, Detection, Track
from services.analytics import AnalyticsEngine
from utils.logger import logger


class StreamerService:
    """Service for annotating and streaming video frames"""
    
    def __init__(self):
        """Initialize streamer service"""
        self.analytics_engine = AnalyticsEngine()
        
        # Colors for visualization
        self.colors = {
            "bbox": (0, 255, 0),  # Green
            "track_id": (255, 255, 255),  # White
            "risk_normal": (0, 255, 0),  # Green
            "risk_warning": (0, 165, 255),  # Orange
            "risk_critical": (0, 0, 255),  # Red
            "zone": (255, 0, 255),  # Magenta
            "text": (255, 255, 255),  # White
            "background": (0, 0, 0),  # Black
        }
    
    def annotate_frame(
        self,
        frame: np.ndarray,
        detections: List[Dict],
        tracks: List[Dict],
        analytics: Optional[Dict] = None,
        zones: Optional[List[Dict]] = None,
        show_heatmap: bool = False,
        show_zones: bool = True,
        show_track_ids: bool = True,
        show_metrics: bool = True
    ) -> np.ndarray:
        """
        Annotate frame with all visualizations
        
        Args:
            frame: Input frame (BGR)
            detections: List of detections
            tracks: List of tracked objects
            analytics: Analytics data dictionary
            zones: List of zone dictionaries
            show_heatmap: Whether to show heatmap overlay
            show_zones: Whether to draw zones
            show_track_ids: Whether to show track IDs
            show_metrics: Whether to show metrics overlay
        
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        
        # Draw zones first (so they're behind other annotations)
        if show_zones and zones:
            annotated = self._draw_zones(annotated, zones)
        
        # Draw heatmap overlay
        if show_heatmap and detections:
            annotated = self._draw_heatmap_overlay(annotated, detections)
        
        # Draw bounding boxes and track IDs
        if tracks:
            annotated = self._draw_tracks(annotated, tracks, show_track_ids)
        elif detections:
            annotated = self._draw_detections(annotated, detections)
        
        # Draw flow direction arrows
        if analytics and analytics.get("flow_direction"):
            annotated = self._draw_flow_arrows(annotated, analytics["flow_direction"], tracks)
        
        # Draw metrics overlay
        if show_metrics and analytics:
            annotated = self._draw_metrics_overlay(annotated, analytics)
        
        return annotated
    
    def _draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw detection bounding boxes"""
        for det in detections:
            bbox = det["bbox"]
            x, y, w, h = [int(v) for v in bbox]
            confidence = det.get("confidence", 0.0)
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), self.colors["bbox"], 2)
            
            # Draw confidence
            label = f"{confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(
                frame,
                (x, y - label_size[1] - 5),
                (x + label_size[0], y),
                self.colors["bbox"],
                -1
            )
            cv2.putText(
                frame,
                label,
                (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                self.colors["text"],
                1
            )
        
        return frame
    
    def _draw_tracks(self, frame: np.ndarray, tracks: List[Dict], show_ids: bool = True) -> np.ndarray:
        """Draw tracked objects with IDs"""
        for track in tracks:
            bbox = track["bbox"]
            track_id = track.get("track_id", 0)
            x, y, w, h = [int(v) for v in bbox]
            confidence = track.get("confidence", 0.0)
            
            # Choose color based on track age or state
            color = self.colors["bbox"]
            if track.get("state") == "tentative":
                color = (128, 128, 128)  # Gray for tentative
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw track ID
            if show_ids:
                label = f"ID:{track_id}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                
                # Background for text
                cv2.rectangle(
                    frame,
                    (x, y - label_size[1] - 5),
                    (x + label_size[0] + 5, y),
                    color,
                    -1
                )
                
                cv2.putText(
                    frame,
                    label,
                    (x + 2, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    self.colors["text"],
                    2
                )
        
        return frame
    
    def _draw_zones(self, frame: np.ndarray, zones: List[Dict]) -> np.ndarray:
        """Draw zone boundaries"""
        for zone in zones:
            polygon_coords = zone.get("polygon_coords", [])
            zone_name = zone.get("zone_name", "")
            max_capacity = zone.get("max_capacity")
            current_occupancy = zone.get("current_occupancy", 0)
            
            if not polygon_coords:
                continue
            
            # Convert to numpy array
            polygon = np.array(polygon_coords, dtype=np.int32)
            
            # Draw polygon
            cv2.polylines(frame, [polygon], True, self.colors["zone"], 2)
            
            # Fill with semi-transparent overlay
            overlay = frame.copy()
            cv2.fillPoly(overlay, [polygon], self.colors["zone"])
            cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
            
            # Draw zone label
            if polygon_coords:
                # Get center of polygon
                center_x = int(np.mean([p[0] for p in polygon_coords]))
                center_y = int(np.mean([p[1] for p in polygon_coords]))
                
                label = zone_name
                if max_capacity is not None:
                    label += f" ({current_occupancy}/{max_capacity})"
                
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                
                # Background for text
                cv2.rectangle(
                    frame,
                    (center_x - label_size[0] // 2 - 5, center_y - label_size[1] - 5),
                    (center_x + label_size[0] // 2 + 5, center_y + 5),
                    self.colors["zone"],
                    -1
                )
                
                cv2.putText(
                    frame,
                    label,
                    (center_x - label_size[0] // 2, center_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    self.colors["text"],
                    2
                )
        
        return frame
    
    def _draw_heatmap_overlay(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw heatmap overlay on frame"""
        if len(detections) == 0:
            return frame
        
        h, w = frame.shape[:2]
        heatmap = np.zeros((h, w), dtype=np.float32)
        
        # Create heatmap from detections
        for det in detections:
            bbox = det["bbox"]
            x, y, w_box, h_box = bbox
            
            cx = int(x + w_box / 2)
            cy = int(y + h_box / 2)
            
            # Clamp to frame bounds
            cx = max(0, min(cx, w - 1))
            cy = max(0, min(cy, h - 1))
            
            # Create Gaussian kernel
            kernel_size = min(max(int(w_box), int(h_box)), 100)
            if kernel_size > 0:
                y_coords, x_coords = np.ogrid[:kernel_size, :kernel_size]
                center = kernel_size // 2
                sigma = kernel_size / 3.0
                kernel = np.exp(-((x_coords - center)**2 + (y_coords - center)**2) / (2 * sigma**2))
                
                y_start = max(0, cy - kernel_size // 2)
                y_end = min(h, cy + kernel_size // 2)
                x_start = max(0, cx - kernel_size // 2)
                x_end = min(w, cx + kernel_size // 2)
                
                if y_end > y_start and x_end > x_start:
                    heatmap[y_start:y_end, x_start:x_end] += kernel[
                        :y_end-y_start, :x_end-x_start
                    ]
        
        # Normalize heatmap
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()
        
        # Apply colormap
        heatmap_colored = cv2.applyColorMap(
            (heatmap * 255).astype(np.uint8),
            cv2.COLORMAP_JET
        )
        
        # Blend with original frame
        overlay = cv2.addWeighted(frame, 0.6, heatmap_colored, 0.4, 0)
        
        return overlay
    
    def _draw_flow_arrows(
        self,
        frame: np.ndarray,
        flow_direction: Dict[str, float],
        tracks: List[Dict]
    ) -> np.ndarray:
        """Draw flow direction arrows"""
        if len(tracks) == 0:
            return frame
        
        h, w = frame.shape[:2]
        
        # Draw arrows at track centers
        for track in tracks[:10]:  # Limit to first 10 for performance
            bbox = track["bbox"]
            cx = int(bbox[0] + bbox[2] / 2)
            cy = int(bbox[1] + bbox[3] / 2)
            
            # Scale flow direction to pixel space
            dx = int(flow_direction["x"] * 50)
            dy = int(flow_direction["y"] * 50)
            
            # Draw arrow
            end_x = cx + dx
            end_y = cy + dy
            
            cv2.arrowedLine(
                frame,
                (cx, cy),
                (end_x, end_y),
                (255, 255, 0),  # Yellow
                2,
                tipLength=0.3
            )
        
        return frame
    
    def _draw_metrics_overlay(self, frame: np.ndarray, analytics: Dict) -> np.ndarray:
        """Draw metrics overlay on frame"""
        h, w = frame.shape[:2]
        
        # Create overlay panel
        panel_height = 150
        overlay = np.zeros((panel_height, w, 3), dtype=np.uint8)
        
        # Get risk level color
        risk_level = analytics.get("risk_level", "NORMAL")
        if risk_level == "CRITICAL":
            risk_color = self.colors["risk_critical"]
        elif risk_level == "WARNING":
            risk_color = self.colors["risk_warning"]
        else:
            risk_color = self.colors["risk_normal"]
        
        # Draw metrics
        y_offset = 25
        line_height = 25
        
        metrics = [
            f"People Count: {analytics.get('people_count', 0)}",
            f"Density: {analytics.get('density', 0.0)*100:.1f}%",
            f"Speed: {analytics.get('avg_speed', 0.0):.1f} px/s",
            f"Congestion: {analytics.get('congestion_level', 'low')}",
            f"Risk: {analytics.get('risk_level', 'NORMAL')} ({analytics.get('risk_score', 0.0):.2f})"
        ]
        
        for i, metric in enumerate(metrics):
            color = risk_color if "Risk" in metric else self.colors["text"]
            cv2.putText(
                overlay,
                metric,
                (10, y_offset + i * line_height),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )
        
        # Draw timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        cv2.putText(
            overlay,
            timestamp,
            (w - 250, panel_height - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.colors["text"],
            1
        )
        
        # Blend overlay with frame
        frame[:panel_height, :] = cv2.addWeighted(
            frame[:panel_height, :],
            0.7,
            overlay,
            0.3,
            0
        )
        
        # Draw risk indicator bar at top
        risk_score = analytics.get("risk_score", 0.0)
        bar_width = int(w * risk_score)
        cv2.rectangle(frame, (0, 0), (bar_width, 5), risk_color, -1)
        
        return frame
    
    def encode_frame_jpeg(self, frame: np.ndarray, quality: int = 85) -> bytes:
        """
        Encode frame to JPEG
        
        Args:
            frame: Frame to encode (BGR)
            quality: JPEG quality (1-100)
        
        Returns:
            JPEG encoded bytes
        """
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        success, encoded_image = cv2.imencode('.jpg', frame, encode_params)
        
        if not success:
            raise ValueError("Failed to encode frame to JPEG")
        
        return encoded_image.tobytes()

