"""
Re-Identification model wrapper
Uses ResNet50-based appearance features + color histograms
"""
import numpy as np
import cv2
from typing import List, Dict, Optional
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from utils.logger import logger


class ReIDModel:
    """Re-identification model using appearance features"""
    
    def __init__(self, device: Optional[str] = None):
        """
        Initialize Re-ID model
        
        Args:
            device: Device to use ('cuda' or 'cpu')
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.transform = None
        self.embedding_dim = 512
        
        self._load_model()
    
    def _load_model(self):
        """Load ResNet50 model for feature extraction"""
        try:
            logger.info(f"Loading Re-ID model on {self.device}")
            
            # Load pre-trained ResNet50
            resnet = models.resnet50(pretrained=True)
            # Remove final classification layer
            self.model = nn.Sequential(*list(resnet.children())[:-1])
            self.model.eval()
            self.model.to(self.device)
            
            # Image preprocessing
            self.transform = transforms.Compose([
                transforms.Resize((256, 128)),  # Standard Re-ID input size
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                    std=[0.229, 0.224, 0.225])
            ])
            
            logger.info("Re-ID model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Re-ID model: {e}")
            raise
    
    def _extract_color_histogram(self, frame: np.ndarray, bbox: List[float]) -> np.ndarray:
        """
        Extract color histogram from bounding box region
        
        Args:
            frame: Input frame (BGR)
            bbox: [x, y, w, h]
        
        Returns:
            256-dimensional color histogram feature
        """
        x, y, w, h = [int(v) for v in bbox]
        h, w_frame = frame.shape[:2]
        
        # Clamp coordinates
        x = max(0, min(x, w_frame - 1))
        y = max(0, min(y, h - 1))
        w = max(1, min(w, w_frame - x))
        h = max(1, min(h, h - y))
        
        # Extract region
        region = frame[y:y+h, x:x+w]
        
        if region.size == 0:
            return np.zeros(256, dtype=np.float32)
        
        # Convert to HSV
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        
        # Calculate histogram for each channel
        hist_h = cv2.calcHist([hsv], [0], None, [256], [0, 256])
        hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        # Normalize
        hist_h = hist_h / (hist_h.sum() + 1e-8)
        hist_s = hist_s / (hist_s.sum() + 1e-8)
        hist_v = hist_v / (hist_v.sum() + 1e-8)
        
        # Concatenate (256*3 = 768 dims, but we'll use 256)
        # Use H channel as primary feature
        return hist_h.flatten().astype(np.float32)
    
    def _extract_appearance_features(self, frame: np.ndarray, bbox: List[float]) -> np.ndarray:
        """
        Extract appearance features using ResNet50
        
        Args:
            frame: Input frame (BGR)
            bbox: [x, y, w, h]
        
        Returns:
            2048-dimensional feature vector
        """
        x, y, w, h = [int(v) for v in bbox]
        h_frame, w_frame = frame.shape[:2]
        
        # Clamp coordinates
        x = max(0, min(x, w_frame - 1))
        y = max(0, min(y, h_frame - 1))
        w = max(1, min(w, w_frame - x))
        h = max(1, min(h, h_frame - y))
        
        # Extract region
        region = frame[y:y+h, x:x+w]
        
        if region.size == 0:
            return np.zeros(2048, dtype=np.float32)
        
        # Convert BGR to RGB
        region_rgb = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(region_rgb)
        
        # Preprocess
        img_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        
        # Extract features
        with torch.no_grad():
            features = self.model(img_tensor)
            features = features.squeeze().cpu().numpy()
        
        # Normalize
        features = features / (np.linalg.norm(features) + 1e-8)
        
        return features.flatten()
    
    def extract_features(self, frame: np.ndarray, bbox: List[float]) -> np.ndarray:
        """
        Extract combined Re-ID features
        
        Args:
            frame: Input frame (BGR)
            bbox: [x, y, w, h]
        
        Returns:
            512-dimensional feature vector
        """
        # Extract appearance features
        appearance_feat = self._extract_appearance_features(frame, bbox)
        
        # Extract color histogram
        color_feat = self._extract_color_histogram(frame, bbox)
        
        # Combine features (reduce dimensions)
        # Use PCA-like reduction: take first 256 from appearance, 256 from color
        if len(appearance_feat) > 256:
            appearance_feat = appearance_feat[:256]
        
        if len(color_feat) > 256:
            color_feat = color_feat[:256]
        
        # Pad if needed
        if len(appearance_feat) < 256:
            appearance_feat = np.pad(appearance_feat, (0, 256 - len(appearance_feat)))
        if len(color_feat) < 256:
            color_feat = np.pad(color_feat, (0, 256 - len(color_feat)))
        
        # Concatenate
        combined_feat = np.concatenate([appearance_feat, color_feat])
        
        # Normalize
        combined_feat = combined_feat / (np.linalg.norm(combined_feat) + 1e-8)
        
        return combined_feat[:self.embedding_dim]  # Ensure 512 dims
    
    def compute_similarity(self, feat1: np.ndarray, feat2: np.ndarray) -> float:
        """
        Compute cosine similarity between two feature vectors
        
        Args:
            feat1: First feature vector
            feat2: Second feature vector
        
        Returns:
            Similarity score (0-1)
        """
        return float(np.dot(feat1, feat2) / (np.linalg.norm(feat1) * np.linalg.norm(feat2) + 1e-8))

