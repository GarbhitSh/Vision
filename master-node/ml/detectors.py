"""
Detection model wrapper - YOLOv8
"""
import numpy as np
from typing import List, Dict, Optional
from ultralytics import YOLO
import torch
from config.settings import settings
from utils.logger import logger


class YOLODetector:
    """YOLOv8 detector wrapper"""
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize YOLO detector
        
        Args:
            model_path: Path to model weights (default: yolov8m.pt)
            device: Device to use ('cuda' or 'cpu')
        """
        self.model_path = model_path or settings.DETECTION_MODEL
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.confidence_threshold = settings.DETECTION_CONFIDENCE
        self.nms_threshold = settings.DETECTION_NMS_THRESHOLD
        
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model"""
        try:
            logger.info(f"Loading YOLO model: {self.model_path} on {self.device}")
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect objects in frame
        
        Args:
            frame: Input frame (BGR format from OpenCV)
        
        Returns:
            List of detections with bbox, confidence, class_id
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            # Run inference
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                iou=self.nms_threshold,
                classes=[0],  # Only detect person class (class 0)
                verbose=False
            )
            
            detections = []
            
            if len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                
                for i in range(len(boxes)):
                    # Get box coordinates (xyxy format)
                    box = boxes.xyxy[i].cpu().numpy()
                    confidence = float(boxes.conf[i].cpu().numpy())
                    class_id = int(boxes.cls[i].cpu().numpy())
                    
                    # Convert to (x, y, w, h) format
                    x1, y1, x2, y2 = box
                    x = float(x1)
                    y = float(y1)
                    w = float(x2 - x1)
                    h = float(y2 - y1)
                    
                    detections.append({
                        "bbox": [x, y, w, h],
                        "confidence": confidence,
                        "class_id": class_id,
                        "class_name": "person"
                    })
            
            return detections
        
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []
    
    def detect_batch(self, frames: List[np.ndarray]) -> List[List[Dict]]:
        """
        Detect objects in batch of frames
        
        Args:
            frames: List of input frames
        
        Returns:
            List of detection lists
        """
        results = []
        for frame in frames:
            results.append(self.detect(frame))
        return results

