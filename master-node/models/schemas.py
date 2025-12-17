"""
Pydantic Schemas for API requests/responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


# Camera Schemas
class CameraBase(BaseModel):
    camera_id: str
    edge_node_id: Optional[str] = None
    location: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[float] = None


class CameraCreate(CameraBase):
    pass


class CameraResponse(CameraBase):
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Frame Schemas
class FrameBase(BaseModel):
    camera_id: str
    frame_id: int
    timestamp: datetime
    width: Optional[int] = None
    height: Optional[int] = None


class FrameCreate(FrameBase):
    frame_path: Optional[str] = None


class FrameResponse(FrameBase):
    id: int
    
    class Config:
        from_attributes = True


# Detection Schemas
class DetectionBase(BaseModel):
    bbox_x: float
    bbox_y: float
    bbox_width: float
    bbox_height: float
    confidence: float
    class_id: int = 0


class DetectionCreate(DetectionBase):
    frame_id: int
    camera_id: str
    track_id: Optional[int] = None
    timestamp: datetime


class DetectionResponse(DetectionBase):
    id: int
    track_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# Analytics Schemas
class FlowDirection(BaseModel):
    x: float
    y: float


class AnalyticsBase(BaseModel):
    people_count: int
    density: float
    avg_speed: Optional[float] = None
    flow_direction: Optional[FlowDirection] = None
    congestion_level: Optional[str] = None


class AnalyticsCreate(AnalyticsBase):
    camera_id: str
    timestamp: datetime


class AnalyticsResponse(AnalyticsBase):
    id: int
    camera_id: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class RealtimeMetricsResponse(BaseModel):
    camera_id: str
    timestamp: datetime
    people_count: int
    density: float
    avg_speed: Optional[float] = None
    flow_direction: Optional[FlowDirection] = None
    congestion_level: Optional[str] = None
    risk_score: float
    risk_level: str  # NORMAL/WARNING/CRITICAL


# Zone Schemas
class ZoneBase(BaseModel):
    camera_id: str
    zone_name: str
    zone_type: Optional[str] = None  # entry/exit/monitor/restricted
    polygon_coords: List[List[float]]  # [[x, y], ...]
    max_capacity: Optional[int] = None


class ZoneCreate(ZoneBase):
    pass


class ZoneResponse(ZoneBase):
    id: int
    current_occupancy: int
    status: str
    
    class Config:
        from_attributes = True


# Alert Schemas
class AlertBase(BaseModel):
    camera_id: str
    alert_type: str
    severity: str  # NORMAL/WARNING/CRITICAL
    risk_score: float
    message: Optional[str] = None


class AlertCreate(AlertBase):
    timestamp: datetime


class AlertResponse(AlertBase):
    id: int
    timestamp: datetime
    acknowledged: bool
    
    class Config:
        from_attributes = True


# Frame Upload Schemas
class FrameUploadResponse(BaseModel):
    status: str
    frame_id: int
    processing_time_ms: float


# WebSocket Schemas
class FrameWebSocketMessage(BaseModel):
    camera_id: str
    frame_id: int
    timestamp: str
    frame_data: str  # base64 encoded
    width: int
    height: int
    fps: Optional[float] = None


class MetricsWebSocketMessage(BaseModel):
    type: str = "metrics"
    camera_id: str
    data: Dict
    timestamp: datetime


class AlertWebSocketMessage(BaseModel):
    type: str = "alert"
    alert: Dict


# Cross-Camera Movement Schemas
class CrossCameraMovementResponse(BaseModel):
    id: int
    entry_camera_id: str
    entry_zone_id: Optional[int] = None
    entry_track_id: int
    entry_timestamp: datetime
    exit_camera_id: str
    exit_zone_id: Optional[int] = None
    exit_track_id: int
    exit_timestamp: datetime
    similarity_score: float
    match_confidence: str
    duration_seconds: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class CrossCameraMovementStatistics(BaseModel):
    total_movements: int
    unique_camera_pairs: int
    avg_duration_seconds: float
    avg_similarity: float
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int

