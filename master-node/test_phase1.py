"""
Test script for Phase 1 - Foundation
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import init_db, engine
from models.database import Camera, Frame, Detection, Track, Analytics, Zone, Alert, EntryExitLog
from sqlalchemy.orm import Session
from config.database import SessionLocal
from datetime import datetime


def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    try:
        db = SessionLocal()
        db.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_table_creation():
    """Test if all tables exist"""
    print("\nTesting table creation...")
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = [
        "cameras", "frames", "detections", "tracks",
        "analytics", "zones", "alerts", "entry_exit_logs"
    ]
    
    missing_tables = [t for t in required_tables if t not in tables]
    
    if missing_tables:
        print(f"❌ Missing tables: {missing_tables}")
        return False
    else:
        print("✅ All tables created successfully")
        return True


def test_camera_model():
    """Test Camera model"""
    print("\nTesting Camera model...")
    try:
        db = SessionLocal()
        
        # Create test camera
        test_camera = Camera(
            camera_id="test_001",
            edge_node_id="edge_001",
            location="Test Location",
            resolution="1920x1080",
            fps=30.0
        )
        
        db.add(test_camera)
        db.commit()
        db.refresh(test_camera)
        
        # Retrieve camera
        retrieved = db.query(Camera).filter(Camera.camera_id == "test_001").first()
        
        if retrieved and retrieved.camera_id == "test_001":
            print("✅ Camera model works correctly")
            
            # Cleanup
            db.delete(retrieved)
            db.commit()
            db.close()
            return True
        else:
            print("❌ Camera model test failed")
            db.close()
            return False
    except Exception as e:
        print(f"❌ Camera model test failed: {e}")
        if 'db' in locals():
            db.close()
        return False


def test_imports():
    """Test all imports"""
    print("\nTesting imports...")
    try:
        from config.settings import settings
        from models.schemas import CameraCreate, CameraResponse
        from api.routes import cameras
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


def main():
    """Run all Phase 1 tests"""
    print("=" * 50)
    print("VISION Phase 1 - Foundation Tests")
    print("=" * 50)
    
    # Initialize database
    print("\nInitializing database...")
    init_db()
    
    tests = [
        test_imports,
        test_database_connection,
        test_table_creation,
        test_camera_model,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All Phase 1 tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

