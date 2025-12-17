"""
Frame encoding utilities
"""
import cv2
import numpy as np
import base64
from typing import Optional
from PIL import Image
import io


class FrameEncoder:
    """Frame encoder for JPEG/WebP encoding"""
    
    @staticmethod
    def encode_jpeg(frame: np.ndarray, quality: int = 85) -> bytes:
        """
        Encode frame to JPEG
        
        Args:
            frame: NumPy array (BGR format from OpenCV)
            quality: JPEG quality (1-100)
        
        Returns:
            JPEG encoded bytes
        """
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        success, encoded_image = cv2.imencode('.jpg', frame, encode_params)
        
        if not success:
            raise Exception("Failed to encode frame to JPEG")
        
        return encoded_image.tobytes()
    
    @staticmethod
    def encode_webp(frame: np.ndarray, quality: int = 85) -> bytes:
        """
        Encode frame to WebP
        
        Args:
            frame: NumPy array (BGR format from OpenCV)
            quality: WebP quality (1-100)
        
        Returns:
            WebP encoded bytes
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        
        # Encode to WebP
        buffer = io.BytesIO()
        pil_image.save(buffer, format='WEBP', quality=quality)
        
        return buffer.getvalue()
    
    @staticmethod
    def compress_frame(frame: np.ndarray, format: str = 'JPEG', quality: int = 85) -> bytes:
        """
        Compress frame in specified format
        
        Args:
            frame: NumPy array
            format: 'JPEG' or 'WEBP'
            quality: Compression quality (1-100)
        
        Returns:
            Compressed frame bytes
        """
        if format.upper() == 'WEBP':
            return FrameEncoder.encode_webp(frame, quality)
        else:
            return FrameEncoder.encode_jpeg(frame, quality)
    
    @staticmethod
    def encode_base64(frame_bytes: bytes) -> str:
        """
        Encode frame bytes to base64 string
        
        Args:
            frame_bytes: Encoded frame bytes
        
        Returns:
            Base64 encoded string
        """
        return base64.b64encode(frame_bytes).decode('utf-8')

