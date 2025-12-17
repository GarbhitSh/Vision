"""
Configuration settings for Master Node
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./vision.db"
    
    # AI Models
    DETECTION_MODEL: str = "yolov8m.pt"
    TRACKING_ALGORITHM: str = "bytetrack"
    REID_MODEL: str = "resnet50"
    
    # Detection Settings
    DETECTION_CONFIDENCE: float = 0.5
    DETECTION_NMS_THRESHOLD: float = 0.4
    
    # Tracking Settings
    TRACK_MAX_AGE: int = 5  # Remove tracks after 5 frames of not being detected (faster cleanup)
    TRACK_MIN_HITS: int = 3
    TRACK_IOU_THRESHOLD: float = 0.5
    
    # Analytics
    ANALYTICS_UPDATE_INTERVAL: float = 1.0  # seconds
    HEATMAP_DURATION: int = 300  # seconds
    
    # Risk Assessment
    RISK_UPDATE_INTERVAL: float = 1.0  # seconds
    CRITICAL_THRESHOLD: float = 0.7
    WARNING_THRESHOLD: float = 0.4
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/vision.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

