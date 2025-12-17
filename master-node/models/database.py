"""
SQLAlchemy Database Models
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class Camera(Base):
    """Camera model"""
    __tablename__ = "cameras"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, unique=True, nullable=False, index=True)
    edge_node_id = Column(String)
    location = Column(String)
    resolution = Column(String)
    fps = Column(Float)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    frames = relationship("Frame", back_populates="camera")
    tracks = relationship("Track", back_populates="camera")
    analytics = relationship("Analytics", back_populates="camera")
    zones = relationship("Zone", back_populates="camera")
    alerts = relationship("Alert", back_populates="camera")


class Frame(Base):
    """Frame model"""
    __tablename__ = "frames"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, ForeignKey("cameras.camera_id"), nullable=False, index=True)
    frame_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    frame_path = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    
    # Relationships
    camera = relationship("Camera", back_populates="frames")
    detections = relationship("Detection", back_populates="frame")


class Detection(Base):
    """Detection model"""
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    frame_id = Column(Integer, ForeignKey("frames.id"), nullable=False, index=True)
    camera_id = Column(String, nullable=False, index=True)
    track_id = Column(Integer, index=True)
    bbox_x = Column(Float, nullable=False)
    bbox_y = Column(Float, nullable=False)
    bbox_width = Column(Float, nullable=False)
    bbox_height = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    class_id = Column(Integer, default=0)  # 0 = person
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    frame = relationship("Frame", back_populates="detections")


class Track(Base):
    """Track model"""
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, nullable=False, index=True)
    camera_id = Column(String, ForeignKey("cameras.camera_id"), nullable=False, index=True)
    first_seen = Column(DateTime(timezone=True), nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=False)
    total_frames = Column(Integer, default=1)
    avg_confidence = Column(Float)
    reid_embedding = Column(BLOB)  # Serialized numpy array
    
    # Relationships
    camera = relationship("Camera", back_populates="tracks")


class Analytics(Base):
    """Analytics model"""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, ForeignKey("cameras.camera_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    people_count = Column(Integer, nullable=False)
    density = Column(Float, nullable=False)
    avg_speed = Column(Float)
    flow_direction = Column(Text)  # JSON: {"x": 0.5, "y": -0.3}
    congestion_level = Column(String)  # low/medium/high
    
    # Relationships
    camera = relationship("Camera", back_populates="analytics")


class Zone(Base):
    """Zone model"""
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, ForeignKey("cameras.camera_id"), nullable=False)
    zone_name = Column(String, nullable=False)
    zone_type = Column(String)  # entry/exit/monitor/restricted
    polygon_coords = Column(Text, nullable=False)  # JSON array of points
    max_capacity = Column(Integer)
    current_occupancy = Column(Integer, default=0)
    status = Column(String, default="active")
    
    # Relationships
    camera = relationship("Camera", back_populates="zones")
    entry_exit_logs = relationship("EntryExitLog", back_populates="zone")


class Alert(Base):
    """Alert model"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, ForeignKey("cameras.camera_id"), nullable=False, index=True)
    alert_type = Column(String, nullable=False)  # density/high_density/stampede_risk/congestion
    severity = Column(String, nullable=False, index=True)  # NORMAL/WARNING/CRITICAL
    risk_score = Column(Float, nullable=False)
    message = Column(Text)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    acknowledged = Column(Boolean, default=False)
    
    # Relationships
    camera = relationship("Camera", back_populates="alerts")


class EntryExitLog(Base):
    """Entry/Exit log model"""
    __tablename__ = "entry_exit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String, nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    track_id = Column(Integer)
    event_type = Column(String, nullable=False)  # entry/exit
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Relationships
    zone = relationship("Zone", back_populates="entry_exit_logs")


class CrossCameraMovement(Base):
    """Cross-camera movement mapping model"""
    __tablename__ = "cross_camera_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_camera_id = Column(String, nullable=False, index=True)
    entry_zone_id = Column(Integer, ForeignKey("zones.id"))
    entry_track_id = Column(Integer, nullable=False)
    entry_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    exit_camera_id = Column(String, nullable=False, index=True)
    exit_zone_id = Column(Integer, ForeignKey("zones.id"))
    exit_track_id = Column(Integer, nullable=False)
    exit_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    similarity_score = Column(Float)  # Re-ID similarity score (0-1)
    match_confidence = Column(String)  # high/medium/low
    duration_seconds = Column(Float)  # Time between entry and exit
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    entry_zone = relationship("Zone", foreign_keys=[entry_zone_id])
    exit_zone = relationship("Zone", foreign_keys=[exit_zone_id])

