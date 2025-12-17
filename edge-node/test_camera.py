"""
Test script to check camera availability and help diagnose issues
"""
import cv2
import sys


def test_camera(source):
    """Test if a camera source is available"""
    print(f"\nTesting camera source: {source}")
    print("-" * 50)
    
    try:
        # Try to open camera
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            # Try with DirectShow backend on Windows
            print("Trying DirectShow backend...")
            cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        
        if not cap.isOpened():
            print(f"❌ Failed to open camera source: {source}")
            return False
        
        print(f"✅ Camera opened successfully")
        
        # Try to read a frame
        ret, frame = cap.read()
        if not ret or frame is None:
            print(f"❌ Camera opened but cannot read frames")
            cap.release()
            return False
        
        print(f"✅ Frame captured successfully")
        print(f"   Frame shape: {frame.shape}")
        
        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"   Resolution: {width}x{height}")
        print(f"   FPS: {fps}")
        
        cap.release()
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Test multiple camera sources"""
    print("=" * 50)
    print("VISION Edge Node - Camera Test")
    print("=" * 50)
    
    # Test common camera indices
    sources_to_test = [0, 1, 2]
    
    print("\nTesting USB camera indices...")
    available_cameras = []
    
    for source in sources_to_test:
        if test_camera(source):
            available_cameras.append(source)
    
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    if available_cameras:
        print(f"✅ Found {len(available_cameras)} available camera(s):")
        for cam in available_cameras:
            print(f"   - Camera index: {cam}")
        print(f"\n💡 Use CAMERA_SOURCE={available_cameras[0]} in your .env file")
    else:
        print("❌ No cameras found")
        print("\nTroubleshooting:")
        print("1. Check if camera is connected")
        print("2. Check if camera is being used by another application")
        print("3. Try different camera indices (0, 1, 2, etc.)")
        print("4. On Windows, check Device Manager for camera status")
        print("5. Try running as administrator")
    
    return 0 if available_cameras else 1


if __name__ == "__main__":
    sys.exit(main())

