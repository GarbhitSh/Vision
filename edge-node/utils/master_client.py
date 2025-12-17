"""
HTTP client for communicating with master node
"""
import requests
from typing import Optional, Dict
from utils.logger import setup_logger

logger = setup_logger("master_client")


class MasterClient:
    """HTTP client for master node API"""
    
    def __init__(self, master_api_url: str):
        """
        Initialize master client
        
        Args:
            master_api_url: Master node API URL (e.g., http://localhost:8000)
        """
        self.master_api_url = master_api_url.rstrip('/')
    
    def register_camera(
        self,
        camera_id: str,
        edge_node_id: str,
        location: str,
        resolution: str,
        fps: float
    ) -> bool:
        """
        Register camera with master node
        
        Args:
            camera_id: Camera identifier
            edge_node_id: Edge node identifier
            location: Camera location
            resolution: Camera resolution
            fps: Frames per second
        
        Returns:
            True if registered successfully
        """
        try:
            url = f"{self.master_api_url}/api/v1/cameras/register"
            payload = {
                "camera_id": camera_id,
                "edge_node_id": edge_node_id,
                "location": location,
                "resolution": resolution,
                "fps": fps
            }
            
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"Camera {camera_id} registered successfully")
                return True
            elif response.status_code == 400:
                # Camera already registered
                logger.info(f"Camera {camera_id} already registered")
                return True
            else:
                logger.error(f"Failed to register camera: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error registering camera: {e}")
            return False
    
    def check_health(self) -> bool:
        """Check if master node is healthy"""
        try:
            response = requests.get(f"{self.master_api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

