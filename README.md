# VISION - Virtual Intelligent System for Individual Oversight & Navigation

A Distributed, AI-Powered Smart Crowd Monitoring & Safety System

## Project Status: Phase 1 - Foundation ✅

Phase 1 implementation is complete! The foundation includes:
- ✅ Project structure for all modules
- ✅ SQLite database schema and models
- ✅ Basic FastAPI server with health check
- ✅ Basic Flask edge node with health check
- ✅ Configuration files and requirements

## Project Structure

```
VISION/
├── master-node/          # FastAPI-based AI processing server
│   ├── main.py          # Application entry point
│   ├── config/          # Configuration
│   ├── models/          # Database models and schemas
│   ├── api/             # API routes and WebSocket handlers
│   ├── database/        # Database initialization
│   └── utils/           # Utilities
├── edge-node/           # Flask-based frame capture service
│   ├── app.py           # Flask application
│   ├── camera/          # Camera capture and encoding
│   ├── config/          # Configuration
│   └── utils/           # Utilities
├── dashboard/           # Next.js dashboard (Phase 5)
└── docs/                # Documentation
    ├── IMPLEMENTATION_PLAN.md
    ├── QUICK_START.md
    └── API_REFERENCE.md
```

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+ (for dashboard in Phase 5)
- Camera (USB/IP/RTSP) for edge node

### 1. Master Node Setup

```bash
cd master-node
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env if needed

# Initialize database
python database/init_db.py

# Run server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### 2. Edge Node Setup

```bash
cd edge-node
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your camera settings

# Run edge node
python app.py
```

The edge node will be available at:
- Health: http://localhost:5000/health
- Camera Status: http://localhost:5000/camera/status

## Testing Phase 1

### Test Master Node

```bash
# Health check
curl http://localhost:8000/health

# Register a camera
curl -X POST http://localhost:8000/api/v1/cameras/register \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "edge_001",
    "edge_node_id": "edge_001",
    "location": "Building A - Main Entrance",
    "resolution": "1920x1080",
    "fps": 30
  }'

# List cameras
curl http://localhost:8000/api/v1/cameras
```

### Test Edge Node

```bash
# Health check
curl http://localhost:5000/health

# Camera status
curl http://localhost:5000/camera/status
```

## Next Steps

- **Phase 2**: Core AI Pipeline (Detection, Tracking, Re-ID)
- **Phase 3**: Analytics & Risk Assessment
- **Phase 4**: Video Streaming & Annotation
- **Phase 5**: Dashboard Implementation
- **Phase 6**: Integration & Testing

## Documentation

- [Implementation Plan](IMPLEMENTATION_PLAN.md)
- [Quick Start Guide](QUICK_START.md)
- [API Reference](API_REFERENCE.md)
- [SRS Document](srs.md)

## License

[Your License Here]

