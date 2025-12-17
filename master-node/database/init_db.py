"""
Database initialization script
Creates all tables and indexes
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import init_db, engine
from models.database import Base
import sqlalchemy


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def create_indexes():
    """Create additional indexes for performance"""
    from sqlalchemy import text
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_frames_camera_timestamp ON frames(camera_id, timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_detections_frame ON detections(frame_id);",
        "CREATE INDEX IF NOT EXISTS idx_detections_track ON detections(track_id);",
        "CREATE INDEX IF NOT EXISTS idx_tracks_camera ON tracks(camera_id);",
        "CREATE INDEX IF NOT EXISTS idx_analytics_camera_timestamp ON analytics(camera_id, timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_alerts_camera_timestamp ON alerts(camera_id, timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);",
        "CREATE INDEX IF NOT EXISTS idx_entry_exit_camera ON entry_exit_logs(camera_id, timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_cross_camera_entry ON cross_camera_movements(entry_camera_id, entry_timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_cross_camera_exit ON cross_camera_movements(exit_camera_id, exit_timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_cross_camera_pair ON cross_camera_movements(entry_camera_id, exit_camera_id);",
    ]
    
    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                conn.commit()
            except Exception as e:
                print(f"Warning: Could not create index: {e}")


if __name__ == "__main__":
    print("Initializing VISION database...")
    create_tables()
    create_indexes()
    print("Database initialization complete!")

