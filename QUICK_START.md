# VISION - Quick Start Guide

## Project Structure Overview

```
VISION/
├── edge-node/          # Flask-based frame capture service
├── master-node/        # FastAPI-based AI processing server
├── dashboard/          # Next.js-based monitoring dashboard
└── docs/              # Documentation
```

## Quick Setup Commands

### 1. Master Node Setup

```bash
cd master-node
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
python database/init_db.py

# Run server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Edge Node Setup

```bash
cd edge-node
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure .env file
cp .env.example .env
# Edit .env with your settings

# Run edge node
python app.py
```

### 3. Dashboard Setup

```bash
cd dashboard
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local with API URL

# Run development server
npm run dev
```

## Database Schema Quick Reference

### Key Tables
- `cameras` - Registered camera information
- `frames` - Processed frame metadata
- `detections` - Person detections with bounding boxes
- `tracks` - Tracked person IDs and embeddings
- `analytics` - Real-time analytics data
- `zones` - Defined monitoring zones
- `alerts` - Generated alerts and warnings
- `entry_exit_logs` - Entry/exit event logs

## API Endpoints Quick Reference

### Frame Ingestion
- `WS /ws/frames` - WebSocket for frame upload
- `POST /api/v1/frames/upload` - HTTP frame upload

### Analytics
- `GET /api/v1/analytics/{camera_id}/realtime` - Real-time metrics
- `GET /api/v1/analytics/{camera_id}/history` - Historical data
- `GET /api/v1/analytics/{camera_id}/heatmap` - Heatmap data

### Alerts
- `GET /api/v1/alerts/active` - Active alerts
- `POST /api/v1/alerts/{alert_id}/acknowledge` - Acknowledge alert

### Zones
- `GET /api/v1/zones/{camera_id}` - Get zones
- `POST /api/v1/zones` - Create zone
- `PUT /api/v1/zones/{zone_id}` - Update zone
- `DELETE /api/v1/zones/{zone_id}` - Delete zone

### Cameras
- `GET /api/v1/cameras` - List cameras
- `POST /api/v1/cameras/register` - Register camera
- `GET /api/v1/cameras/{camera_id}` - Camera details

### Streaming
- `GET /stream/{camera_id}` - MJPEG video stream
- `GET /api/v1/cameras/{camera_id}/snapshot` - Snapshot image

### WebSocket
- `WS /ws/dashboard/{camera_id}` - Real-time metrics stream
- `WS /ws/alerts` - Alert stream

## Model Files Required

### Detection
- YOLOv8m weights: Auto-downloaded on first run
- Location: `~/.ultralytics/weights/yolov8m.pt`

### Tracking
- ByteTrack: No weights needed (algorithm-based)

### Re-ID
- ResNet50 weights: Download separately or use pre-trained
- Location: `master-node/ml/models/resnet50_reid.pth`

## Configuration Checklist

### Master Node (.env)
- [ ] Database path configured
- [ ] Detection model selected (yolov8m.pt)
- [ ] Confidence thresholds set
- [ ] Risk thresholds configured
- [ ] Log level set

### Edge Node (.env)
- [ ] Edge node ID set
- [ ] Master node URL configured
- [ ] Camera source specified
- [ ] Frame quality set
- [ ] FPS configured

### Dashboard (.env.local)
- [ ] API URL configured
- [ ] WebSocket URL configured

## Testing Checklist

### Edge Node
- [ ] Camera connects successfully
- [ ] Frames are captured
- [ ] Frames are encoded correctly
- [ ] WebSocket connection to master established
- [ ] Frames are sent successfully

### Master Node
- [ ] Database initialized
- [ ] API endpoints respond
- [ ] Detection model loads
- [ ] Tracking works
- [ ] Analytics calculate correctly
- [ ] Risk scores generate
- [ ] Video stream works

### Dashboard
- [ ] Connects to API
- [ ] WebSocket connections work
- [ ] Video displays
- [ ] Metrics update in real-time
- [ ] Alerts display
- [ ] Zones can be created

## Common Issues & Solutions

### Issue: Camera not detected
**Solution**: Check camera source index or RTSP URL

### Issue: Detection too slow
**Solution**: Use YOLOv8n instead of YOLOv8m, or enable GPU

### Issue: WebSocket connection fails
**Solution**: Check master node URL and firewall settings

### Issue: Database locked
**Solution**: Ensure only one process accesses SQLite at a time

### Issue: Dashboard not updating
**Solution**: Check WebSocket connection and API URL

## Performance Optimization Tips

1. **Use GPU** for detection (10x faster)
2. **Reduce frame rate** if CPU-bound (15 FPS instead of 30)
3. **Lower resolution** for faster processing
4. **Batch database writes** instead of per-frame
5. **Use connection pooling** for database
6. **Enable caching** for static data

## Next Steps After MVP

1. Add authentication/authorization
2. Implement multi-camera load balancing
3. Add PostgreSQL for production
4. Implement Redis caching
5. Add Docker containerization
6. Set up CI/CD pipeline
7. Add comprehensive testing
8. Implement monitoring and logging

