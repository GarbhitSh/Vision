"""
Test script for Phase 2 - Core AI Pipeline
"""
import sys
import os
import numpy as np
import cv2
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml.detectors import YOLODetector
from ml.trackers import ByteTracker
from ml.reid_model import ReIDModel
from services.detection import DetectionService
from services.tracking import TrackingService
from services.reid import ReIDService
from utils.logger import logger


def create_test_frame(width=640, height=480):
    """Create a test frame with some shapes"""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # Draw some rectangles to simulate people
    cv2.rectangle(frame, (100, 100), (200, 300), (255, 255, 255), -1)
    cv2.rectangle(frame, (300, 150), (400, 350), (255, 255, 255), -1)
    cv2.rectangle(frame, (500, 100), (600, 300), (255, 255, 255), -1)
    return frame


def test_detection_service():
    """Test detection service"""
    print("\n" + "="*50)
    print("Testing Detection Service")
    print("="*50)
    
    try:
        service = DetectionService()
        print("✅ Detection service initialized")
        
        # Create test frame
        frame = create_test_frame()
        print("✅ Test frame created")
        
        # Run detection (may not detect anything on synthetic frame)
        detections = service.detect(frame)
        print(f"✅ Detection completed: {len(detections)} detections")
        
        return True
    except Exception as e:
        print(f"❌ Detection service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tracking_service():
    """Test tracking service"""
    print("\n" + "="*50)
    print("Testing Tracking Service")
    print("="*50)
    
    try:
        service = TrackingService()
        print("✅ Tracking service initialized")
        
        # Create mock detections
        detections = [
            {"bbox": [100, 100, 100, 200], "confidence": 0.9, "class_id": 0},
            {"bbox": [300, 150, 100, 200], "confidence": 0.85, "class_id": 0},
        ]
        
        # Update tracker
        tracked = service.update("test_camera", detections)
        print(f"✅ Tracking update 1: {len(tracked)} tracks")
        
        # Update again with slightly moved detections
        detections2 = [
            {"bbox": [105, 105, 100, 200], "confidence": 0.9, "class_id": 0},
            {"bbox": [305, 155, 100, 200], "confidence": 0.85, "class_id": 0},
        ]
        tracked2 = service.update("test_camera", detections2)
        print(f"✅ Tracking update 2: {len(tracked2)} tracks")
        
        return True
    except Exception as e:
        print(f"❌ Tracking service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reid_service():
    """Test Re-ID service"""
    print("\n" + "="*50)
    print("Testing Re-ID Service")
    print("="*50)
    
    try:
        service = ReIDService()
        print("✅ Re-ID service initialized")
        
        # Create test frame
        frame = create_test_frame()
        bbox = [100, 100, 100, 200]
        
        # Extract features
        features = service.extract_features(frame, bbox)
        print(f"✅ Feature extraction completed: shape {features.shape}")
        
        # Test similarity
        features2 = service.extract_features(frame, bbox)
        similarity = service.compute_similarity(features, features2)
        print(f"✅ Similarity computation: {similarity:.4f}")
        
        return True
    except Exception as e:
        print(f"❌ Re-ID service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline():
    """Test full detection -> tracking -> Re-ID pipeline"""
    print("\n" + "="*50)
    print("Testing Full Pipeline")
    print("="*50)
    
    try:
        detection_service = DetectionService()
        tracking_service = TrackingService()
        reid_service = ReIDService()
        
        print("✅ All services initialized")
        
        # Create test frame
        frame = create_test_frame()
        print("✅ Test frame created")
        
        # Step 1: Detection
        detections = detection_service.detect(frame)
        print(f"✅ Detection: {len(detections)} detections")
        
        # Step 2: Tracking
        tracked = tracking_service.update("test_camera", detections)
        print(f"✅ Tracking: {len(tracked)} tracks")
        
        # Step 3: Re-ID
        for track in tracked[:2]:  # Limit to first 2 for testing
            bbox = track["bbox"]
            features = reid_service.extract_features(frame, bbox)
            print(f"✅ Re-ID: Track {track['track_id']} features extracted")
        
        print("✅ Full pipeline test completed")
        return True
    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 2 tests"""
    print("="*50)
    print("VISION Phase 2 - Core AI Pipeline Tests")
    print("="*50)
    
    tests = [
        ("Detection Service", test_detection_service),
        ("Tracking Service", test_tracking_service),
        ("Re-ID Service", test_reid_service),
        ("Full Pipeline", test_full_pipeline),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append(False)
    
    print("\n" + "="*50)
    print("Test Results Summary")
    print("="*50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("✅ All Phase 2 tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

