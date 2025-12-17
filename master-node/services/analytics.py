"""
Analytics Engine
Computes crowd density, zone occupancy, movement flow, speed, and congestion
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from scipy.spatial import distance
from scipy.ndimage import gaussian_filter
import json

from models.database import Detection, Track, Zone, Analytics
from utils.logger import logger


class AnalyticsEngine:
    """Analytics engine for crowd monitoring"""
    
    def __init__(self):
        """Initialize analytics engine"""
        self.frame_width = 1920
        self.frame_height = 1080
    
    def estimate_density(
        self,
        detections: List[Dict],
        frame_width: int,
        frame_height: int
    ) -> float:
        """
        Estimate crowd density using Gaussian kernel density estimation
        
        Args:
            detections: List of detections with bbox
            frame_width: Frame width
            frame_height: Frame height
        
        Returns:
            Density value (0.0 - 1.0)
        """
        if len(detections) == 0:
            return 0.0
        
        # Create density map
        density_map = np.zeros((frame_height, frame_width), dtype=np.float32)
        
        # Place Gaussian kernels at detection centers
        for det in detections:
            bbox = det["bbox"]
            x, y, w, h = bbox
            
            # Center point
            cx = int(x + w / 2)
            cy = int(y + h / 2)
            
            # Clamp to frame bounds
            cx = max(0, min(cx, frame_width - 1))
            cy = max(0, min(cy, frame_height - 1))
            
            # Create Gaussian kernel (size based on bounding box)
            kernel_size = max(int(w), int(h))
            kernel_size = min(kernel_size, 100)  # Limit kernel size
            
            if kernel_size > 0:
                # Create Gaussian kernel
                y_coords, x_coords = np.ogrid[:kernel_size, :kernel_size]
                center = kernel_size // 2
                sigma = kernel_size / 3.0
                kernel = np.exp(-((x_coords - center)**2 + (y_coords - center)**2) / (2 * sigma**2))
                
                # Place kernel on density map
                y_start = max(0, cy - kernel_size // 2)
                y_end = min(frame_height, cy + kernel_size // 2)
                x_start = max(0, cx - kernel_size // 2)
                x_end = min(frame_width, cx + kernel_size // 2)
                
                kernel_y_start = max(0, kernel_size // 2 - cy)
                kernel_y_end = kernel_y_start + (y_end - y_start)
                kernel_x_start = max(0, kernel_size // 2 - cx)
                kernel_x_end = kernel_x_start + (x_end - x_start)
                
                if y_end > y_start and x_end > x_start:
                    density_map[y_start:y_end, x_start:x_end] += kernel[
                        kernel_y_start:kernel_y_end,
                        kernel_x_start:kernel_x_end
                    ]
        
        # Normalize density map
        max_density = density_map.max()
        if max_density > 0:
            density_map = density_map / max_density
        
        # Apply Gaussian smoothing
        density_map = gaussian_filter(density_map, sigma=10)
        
        # Calculate average density
        avg_density = np.mean(density_map)
        
        # Normalize to 0-1 range (can be > 1 if many overlapping detections)
        density = min(1.0, avg_density)
        
        return float(density)
    
    def calculate_zone_occupancy(
        self,
        detections: List[Dict],
        zones: List[Dict],
        frame_width: int,
        frame_height: int
    ) -> Dict[int, int]:
        """
        Calculate occupancy for each zone
        
        Args:
            detections: List of detections
            zones: List of zone dictionaries with polygon_coords
            frame_width: Frame width
            frame_height: Frame height
        
        Returns:
            Dictionary mapping zone_id -> occupancy count
        """
        occupancy = {}
        
        for zone in zones:
            zone_id = zone.get("id")
            polygon_coords = zone.get("polygon_coords", [])
            
            if not polygon_coords or not zone_id:
                continue
            
            # Convert polygon to numpy array
            polygon = np.array(polygon_coords, dtype=np.int32)
            
            count = 0
            for det in detections:
                bbox = det["bbox"]
                x, y, w, h = bbox
                
                # Check if center point is in polygon
                cx = int(x + w / 2)
                cy = int(y + h / 2)
                
                if self._point_in_polygon(cx, cy, polygon):
                    count += 1
            
            occupancy[zone_id] = count
        
        return occupancy
    
    def _point_in_polygon(self, x: int, y: int, polygon: np.ndarray) -> bool:
        """Check if point is inside polygon using ray casting algorithm"""
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def calculate_movement_flow(
        self,
        current_tracks: List[Dict],
        previous_tracks: Dict[int, Dict],
        frame_width: int,
        frame_height: int
    ) -> Dict[str, float]:
        """
        Calculate movement flow vectors
        
        Args:
            current_tracks: Current frame tracks
            previous_tracks: Previous frame tracks (track_id -> track info)
            frame_width: Frame width
            frame_height: Frame height
        
        Returns:
            Flow direction vector {"x": float, "y": float}
        """
        if len(current_tracks) == 0:
            return {"x": 0.0, "y": 0.0}
        
        flow_vectors = []
        
        for track in current_tracks:
            track_id = track["track_id"]
            current_bbox = track["bbox"]
            cx_current = current_bbox[0] + current_bbox[2] / 2
            cy_current = current_bbox[1] + current_bbox[3] / 2
            
            if track_id in previous_tracks:
                prev_bbox = previous_tracks[track_id]["bbox"]
                cx_prev = prev_bbox[0] + prev_bbox[2] / 2
                cy_prev = prev_bbox[1] + prev_bbox[3] / 2
                
                # Calculate velocity vector
                dx = cx_current - cx_prev
                dy = cy_current - cy_prev
                
                # Normalize by frame dimensions
                dx_norm = dx / frame_width
                dy_norm = dy / frame_height
                
                flow_vectors.append([dx_norm, dy_norm])
        
        if len(flow_vectors) == 0:
            return {"x": 0.0, "y": 0.0}
        
        # Average flow direction
        avg_flow = np.mean(flow_vectors, axis=0)
        
        # Normalize
        norm = np.linalg.norm(avg_flow)
        if norm > 0:
            avg_flow = avg_flow / norm
        
        return {"x": float(avg_flow[0]), "y": float(avg_flow[1])}
    
    def estimate_speed(
        self,
        current_tracks: List[Dict],
        previous_tracks: Dict[int, Dict],
        frame_width: int,
        frame_height: int,
        fps: float = 30.0
    ) -> float:
        """
        Estimate average speed of crowd
        
        Args:
            current_tracks: Current frame tracks
            previous_tracks: Previous frame tracks
            frame_width: Frame width
            frame_height: Frame height
            fps: Frames per second
        
        Returns:
            Average speed (pixels per second)
        """
        if len(current_tracks) == 0:
            return 0.0
        
        speeds = []
        
        for track in current_tracks:
            track_id = track["track_id"]
            current_bbox = track["bbox"]
            cx_current = current_bbox[0] + current_bbox[2] / 2
            cy_current = current_bbox[1] + current_bbox[3] / 2
            
            if track_id in previous_tracks:
                prev_bbox = previous_tracks[track_id]["bbox"]
                cx_prev = prev_bbox[0] + prev_bbox[2] / 2
                cy_prev = prev_bbox[1] + prev_bbox[3] / 2
                
                # Calculate distance
                dx = cx_current - cx_prev
                dy = cy_current - cy_prev
                distance_pixels = np.sqrt(dx**2 + dy**2)
                
                # Convert to pixels per second
                speed = distance_pixels * fps
                speeds.append(speed)
        
        if len(speeds) == 0:
            return 0.0
        
        return float(np.mean(speeds))
    
    def detect_congestion(
        self,
        tracks: List[Dict],
        frame_width: int,
        frame_height: int,
        speed_threshold: float = 0.5
    ) -> str:
        """
        Detect congestion level
        
        Args:
            tracks: List of tracked objects
            frame_width: Frame width
            frame_height: Frame height
            speed_threshold: Speed threshold for congestion (pixels/sec)
        
        Returns:
            Congestion level: "low", "medium", "high"
        """
        if len(tracks) == 0:
            return "low"
        
        # Calculate average speed (would need previous frame data)
        # For now, use density as proxy
        density = len(tracks) / (frame_width * frame_height / 10000)  # Normalized
        
        if density > 0.7:
            return "high"
        elif density > 0.4:
            return "medium"
        else:
            return "low"
    
    def calculate_analytics(
        self,
        detections: List[Dict],
        tracks: List[Dict],
        previous_tracks: Dict[int, Dict],
        zones: List[Dict],
        frame_width: int,
        frame_height: int,
        fps: float = 30.0
    ) -> Dict:
        """
        Calculate all analytics metrics
        
        Args:
            detections: Current detections
            tracks: Current tracks
            previous_tracks: Previous frame tracks
            zones: List of zones
            frame_width: Frame width
            frame_height: Frame height
            fps: Frames per second
        
        Returns:
            Analytics dictionary
        """
        # Density
        density = self.estimate_density(detections, frame_width, frame_height)
        
        # Zone occupancy
        zone_occupancy = self.calculate_zone_occupancy(detections, zones, frame_width, frame_height)
        
        # Movement flow
        flow_direction = self.calculate_movement_flow(tracks, previous_tracks, frame_width, frame_height)
        
        # Speed
        avg_speed = self.estimate_speed(tracks, previous_tracks, frame_width, frame_height, fps)
        
        # Congestion
        congestion_level = self.detect_congestion(tracks, frame_width, frame_height)
        
        return {
            "people_count": len(detections),
            "density": density,
            "avg_speed": avg_speed,
            "flow_direction": flow_direction,
            "congestion_level": congestion_level,
            "zone_occupancy": zone_occupancy
        }

