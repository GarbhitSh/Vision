"""
Configuration settings for Edge Node
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings"""
    
    # Edge Node
    EDGE_NODE_ID: str = os.getenv("EDGE_NODE_ID", "edge_001")
    
    # Master Node
    MASTER_NODE_URL: str = os.getenv("MASTER_NODE_URL", "http://localhost:8000")
    
    # Camera
    CAMERA_SOURCE: str = os.getenv("CAMERA_SOURCE", "0")
    CAMERA_RESOLUTION: str = os.getenv("CAMERA_RESOLUTION", "1920x1080")
    CAMERA_FPS: int = int(os.getenv("CAMERA_FPS", "30"))
    
    # Encoding
    FRAME_QUALITY: int = int(os.getenv("FRAME_QUALITY", "85"))
    ENCODING_FORMAT: str = os.getenv("ENCODING_FORMAT", "JPEG")
    
    # Connection
    RECONNECT_DELAY: int = int(os.getenv("RECONNECT_DELAY", "5"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"


settings = Settings()

