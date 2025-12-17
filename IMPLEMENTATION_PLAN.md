# VISION - Detailed Implementation Plan (MVP)

## Table of Contents
1. [Project Overview](#project-overview)
2. [Edge Node Implementation](#edge-node-implementation)
3. [Master Node (Server) Implementation](#master-node-server-implementation)
4. [Dashboard Implementation](#dashboard-implementation)
5. [Database Schema](#database-schema)
6. [API Endpoints Specification](#api-endpoints-specification)
7. [Dependencies & Libraries](#dependencies--libraries)
8. [Model Specifications](#model-specifications)
9. [File Structure](#file-structure)
10. [Implementation Phases](#implementation-phases)

---

## Project Overview

**VISION** is a 3-tier distributed system:
- **Edge Node**: Flask-based frame capture and forwarding
- **Master Node**: FastAPI-based AI processing, analytics, and risk assessment
- **Dashboard**: Next.js-based real-time monitoring interface

**Database**: SQLite (file-based)

---

## Edge Node Implementation

### Technology Stack
- **Framework**: Flask 2.3+
- **Video Capture**: OpenCV 4.8+
- **Image Encoding**: Pillow, base64
- **Communication**: WebSocket (python-socketio), HTTP POST
- **Async**: Threading, Queue

### Core Responsibilities
1. Capture video frames from camera (USB/IP/RTSP)
2. Encode frames to JPEG/WebP format
3. Forward frames to Master Node via WebSocket/HTTP
4. Handle reconnection logic
5. Monitor camera health

### File Structure
```
edge-node/
├── app.py                 # Main Flask application
├── camera/
│   ├── __init__.py
│   ├── capture.py        # Camera capture module
│   └── encoder.py        # Frame encoding utilities
├── config/
│   ├── __init__.py
│   └── settings.py       # Configuration management
├── utils/
│   ├── __init__.py
│   └── logger.py         # Logging utilities
├── requirements.txt
└── .env                  # Environment variables
```

### API Endpoints (Edge Node)

#### 1. Health Check
- **Endpoint**: `GET /health`
- **Response**:
```json
{
  "status": "healthy",
  "camera_status": "connected",
  "fps": 15.2,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 2. Camera Status
- **Endpoint**: `GET /camera/status`
- **Response**:
```json
{
  "camera_id": "edge_001",
  "is_connected": true,
  "resolution": "1920x1080",
  "fps": 30,
  "format": "MJPG"
}
```

#### 3. Start Streaming
- **Endpoint**: `POST /stream/start`
- **Body**:
```json
{
  "master_url": "ws://master-node:8000/ws/frames",
  "camera_id": "edge_001",
  "fps": 15,
  "quality": 85
}
```

#### 4. Stop Streaming
- **Endpoint**: `POST /stream/stop`
- **Response**:
```json
{
  "status": "stopped",
  "frames_sent": 1250
}
```

### Implementation Details

#### Camera Capture Module (`camera/capture.py`)
```python
# Key functions:
- initialize_camera(source, resolution, fps)
- capture_frame() -> np.ndarray
- release_camera()
- get_camera_info() -> dict
```

**Features**:
- Support USB cameras (device index)
- Support IP cameras (RTSP/HTTP URLs)
- Support Raspberry Pi Camera
- Automatic reconnection on failure
- Frame rate throttling

#### Frame Encoder (`camera/encoder.py`)
```python
# Key functions:
- encode_jpeg(frame, quality=85) -> bytes
- encode_webp(frame, quality=85) -> bytes
- compress_frame(frame, format='JPEG') -> bytes
```

**Features**:
- JPEG encoding with configurable quality
- WebP encoding (optional, better compression)
- Base64 encoding for HTTP transport
- Frame size optimization

#### WebSocket Client (`app.py`)
```python
# Key functions:
- connect_to_master(master_url, camera_id)
- send_frame(frame_data, metadata)
- handle_reconnection()
- maintain_heartbeat()
```

**Frame Payload Structure**:
```json
{
  "camera_id": "edge_001",
  "frame_id": 12345,
  "timestamp": "2024-01-01T12:00:00.123Z",
  "frame_data": "base64_encoded_jpeg",
  "width": 1920,
  "height": 1080,
  "fps": 15.2
}
```

### Configuration (`config/settings.py`)
```python
# Environment variables:
EDGE_NODE_ID=edge_001
MASTER_NODE_URL=ws://localhost:8000/ws/frames
CAMERA_SOURCE=0  # or RTSP URL
CAMERA_RESOLUTION=1920x1080
CAMERA_FPS=30
FRAME_QUALITY=85
ENCODING_FORMAT=JPEG
RECONNECT_DELAY=5
LOG_LEVEL=INFO
```

### Dependencies (`requirements.txt`)
```
Flask==3.0.0
opencv-python==4.8.1.78
Pillow==10.1.0
python-socketio==5.10.0
python-dotenv==1.0.0
numpy==1.24.3
requests==2.31.0
```

---

## Master Node (Server) Implementation

### Technology Stack
- **Framework**: FastAPI 0.104+
- **AI/ML**: Ultralytics YOLOv8, DeepSORT, ByteTrack
- **Computer Vision**: OpenCV, scikit-image
- **Analytics**: NumPy, SciPy, scikit-learn
- **Database**: SQLite (sqlite3, SQLAlchemy ORM)
- **Async**: asyncio, aiofiles
- **WebSocket**: python-socketio, fastapi-websocket
- **Video Streaming**: OpenCV, FFmpeg

### Core Responsibilities
1. Receive frames from Edge Nodes
2. Run AI pipeline (Detection → Tracking → Re-ID)
3. Perform real-time analytics
4. Calculate risk scores
5. Generate annotated video streams
6. Store data in SQLite
7. Serve API endpoints for Dashboard
8. Broadcast real-time metrics via WebSocket

### File Structure
```
master-node/
├── main.py                    # FastAPI application entry
├── config/
│   ├── __init__.py
│   ├── settings.py           # Configuration
│   └── database.py           # Database connection
├── models/
│   ├── __init__.py
│   ├── database.py           # SQLAlchemy models
│   └── schemas.py            # Pydantic schemas
├── services/
│   ├── __init__.py
│   ├── ingestion.py          # Frame ingestion service
│   ├── detection.py          # YOLO detection service
│   ├── tracking.py           # DeepSORT/ByteTrack service
│   ├── reid.py               # Re-identification service
│   ├── analytics.py          # Analytics engine
│   ├── risk_assessment.py    # Risk scoring engine
│   ├── streamer.py           # Video annotation & streaming
│   └── database_service.py   # Database operations
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── frames.py         # Frame ingestion endpoints
│   │   ├── analytics.py      # Analytics endpoints
│   │   ├── alerts.py         # Alerts endpoints
│   │   ├── zones.py          # Zone management
│   │   ├── cameras.py        # Camera management
│   │   └── dashboard.py      # Dashboard API
│   └── websocket.py          # WebSocket handlers
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   ├── image_processing.py
│   └── validators.py
├── ml/
│   ├── __init__.py
│   ├── detectors.py          # Detection model wrapper
│   ├── trackers.py           # Tracking algorithm wrapper
│   └── reid_model.py         # Re-ID model wrapper
├── database/
│   └── init_db.py            # Database initialization
├── requirements.txt
└── .env
```

### Database Schema (SQLite)

#### Tables

**1. cameras**
```sql
CREATE TABLE cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id TEXT UNIQUE NOT NULL,
    edge_node_id TEXT,
    location TEXT,
    resolution TEXT,
    fps REAL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**2. frames**
```sql
CREATE TABLE frames (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id TEXT NOT NULL,
    frame_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    frame_path TEXT,
    width INTEGER,
    height INTEGER,
    FOREIGN KEY (camera_id) REFERENCES cameras(camera_id)
);
CREATE INDEX idx_frames_camera_timestamp ON frames(camera_id, timestamp);
```

**3. detections**
```sql
CREATE TABLE detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    frame_id INTEGER NOT NULL,
    camera_id TEXT NOT NULL,
    track_id INTEGER,
    bbox_x REAL NOT NULL,
    bbox_y REAL NOT NULL,
    bbox_width REAL NOT NULL,
    bbox_height REAL NOT NULL,
    confidence REAL NOT NULL,
    class_id INTEGER DEFAULT 0,  -- 0 = person
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (frame_id) REFERENCES frames(id)
);
CREATE INDEX idx_detections_frame ON detections(frame_id);
CREATE INDEX idx_detections_track ON detections(track_id);
```

**4. tracks**
```sql
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_id INTEGER NOT NULL,
    camera_id TEXT NOT NULL,
    first_seen TIMESTAMP NOT NULL,
    last_seen TIMESTAMP NOT NULL,
    total_frames INTEGER DEFAULT 1,
    avg_confidence REAL,
    reid_embedding BLOB,  -- Serialized numpy array
    FOREIGN KEY (camera_id) REFERENCES cameras(camera_id)
);
CREATE INDEX idx_tracks_camera ON tracks(camera_id);
```

**5. analytics**
```sql
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    people_count INTEGER NOT NULL,
    density REAL NOT NULL,
    avg_speed REAL,
    flow_direction TEXT,  -- JSON: {"x": 0.5, "y": -0.3}
    congestion_level TEXT,  -- low/medium/high
    FOREIGN KEY (camera_id) REFERENCES cameras(camera_id)
);
CREATE INDEX idx_analytics_camera_timestamp ON analytics(camera_id, timestamp);
```

**6. zones**
```sql
CREATE TABLE zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id TEXT NOT NULL,
    zone_name TEXT NOT NULL,
    zone_type TEXT,  -- entry/exit/monitor/restricted
    polygon_coords TEXT NOT NULL,  -- JSON array of points
    max_capacity INTEGER,
    current_occupancy INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    FOREIGN KEY (camera_id) REFERENCES cameras(camera_id)
);
```

**7. alerts**
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,  -- density/high_density/stampede_risk/congestion
    severity TEXT NOT NULL,  -- NORMAL/WARNING/CRITICAL
    risk_score REAL NOT NULL,
    message TEXT,
    timestamp TIMESTAMP NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (camera_id) REFERENCES cameras(camera_id)
);
CREATE INDEX idx_alerts_camera_timestamp ON alerts(camera_id, timestamp);
CREATE INDEX idx_alerts_severity ON alerts(severity);
```

**8. entry_exit_logs**
```sql
CREATE TABLE entry_exit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id TEXT NOT NULL,
    zone_id INTEGER,
    track_id INTEGER,
    event_type TEXT NOT NULL,  -- entry/exit
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (camera_id) REFERENCES cameras(camera_id),
    FOREIGN KEY (zone_id) REFERENCES zones(id)
);
CREATE INDEX idx_entry_exit_camera ON entry_exit_logs(camera_id, timestamp);
```

### API Endpoints (Master Node)

#### Frame Ingestion

**1. WebSocket: Frame Reception**
- **Endpoint**: `WS /ws/frames`
- **Protocol**: WebSocket
- **Payload**:
```json
{
  "camera_id": "edge_001",
  "frame_id": 12345,
  "timestamp": "2024-01-01T12:00:00.123Z",
  "frame_data": "base64_encoded_jpeg",
  "width": 1920,
  "height": 1080
}
```
- **Response**: `{"status": "received", "frame_id": 12345}`

**2. HTTP: Frame Upload (Alternative)**
- **Endpoint**: `POST /api/v1/frames/upload`
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `camera_id`: string
  - `frame`: file (JPEG)
  - `timestamp`: ISO timestamp
- **Response**:
```json
{
  "status": "success",
  "frame_id": 12345,
  "processing_time_ms": 45
}
```

#### Analytics Endpoints

**3. Get Real-time Metrics**
- **Endpoint**: `GET /api/v1/analytics/{camera_id}/realtime`
- **Response**:
```json
{
  "camera_id": "edge_001",
  "timestamp": "2024-01-01T12:00:00Z",
  "people_count": 45,
  "density": 0.65,
  "avg_speed": 1.2,
  "flow_direction": {"x": 0.3, "y": -0.5},
  "congestion_level": "medium",
  "risk_score": 0.35,
  "risk_level": "NORMAL"
}
```

**4. Get Historical Analytics**
- **Endpoint**: `GET /api/v1/analytics/{camera_id}/history`
- **Query Parameters**:
  - `start_time`: ISO timestamp
  - `end_time`: ISO timestamp
  - `interval`: seconds (default: 60)
- **Response**:
```json
{
  "camera_id": "edge_001",
  "data": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "people_count": 45,
      "density": 0.65,
      "risk_score": 0.35
    }
  ]
}
```

**5. Get Heatmap Data**
- **Endpoint**: `GET /api/v1/analytics/{camera_id}/heatmap`
- **Query Parameters**:
  - `duration`: seconds (default: 300)
- **Response**:
```json
{
  "camera_id": "edge_001",
  "heatmap": "base64_encoded_image",
  "resolution": {"width": 1920, "height": 1080},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Alerts Endpoints

**6. Get Active Alerts**
- **Endpoint**: `GET /api/v1/alerts/active`
- **Query Parameters**:
  - `camera_id`: optional filter
  - `severity`: optional filter (NORMAL/WARNING/CRITICAL)
- **Response**:
```json
{
  "alerts": [
    {
      "id": 1,
      "camera_id": "edge_001",
      "alert_type": "high_density",
      "severity": "WARNING",
      "risk_score": 0.65,
      "message": "High crowd density detected",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ]
}
```

**7. Acknowledge Alert**
- **Endpoint**: `POST /api/v1/alerts/{alert_id}/acknowledge`
- **Response**:
```json
{
  "status": "acknowledged",
  "alert_id": 1
}
```

#### Zone Management

**8. Create Zone**
- **Endpoint**: `POST /api/v1/zones`
- **Body**:
```json
{
  "camera_id": "edge_001",
  "zone_name": "Main Entrance",
  "zone_type": "entry",
  "polygon_coords": [[100, 100], [500, 100], [500, 400], [100, 400]],
  "max_capacity": 50
}
```

**9. Get Zones**
- **Endpoint**: `GET /api/v1/zones/{camera_id}`
- **Response**:
```json
{
  "zones": [
    {
      "id": 1,
      "camera_id": "edge_001",
      "zone_name": "Main Entrance",
      "zone_type": "entry",
      "polygon_coords": [[100, 100], [500, 100], [500, 400], [100, 400]],
      "max_capacity": 50,
      "current_occupancy": 32
    }
  ]
}
```

**10. Update Zone**
- **Endpoint**: `PUT /api/v1/zones/{zone_id}`
- **Body**: Same as create

**11. Delete Zone**
- **Endpoint**: `DELETE /api/v1/zones/{zone_id}`

#### Camera Management

**12. Register Camera**
- **Endpoint**: `POST /api/v1/cameras/register`
- **Body**:
```json
{
  "camera_id": "edge_001",
  "edge_node_id": "edge_001",
  "location": "Building A - Main Entrance",
  "resolution": "1920x1080",
  "fps": 30
}
```

**13. Get Camera List**
- **Endpoint**: `GET /api/v1/cameras`
- **Response**:
```json
{
  "cameras": [
    {
      "camera_id": "edge_001",
      "location": "Building A - Main Entrance",
      "status": "active",
      "last_frame_time": "2024-01-01T12:00:00Z"
    }
  ]
}
```

**14. Get Camera Details**
- **Endpoint**: `GET /api/v1/cameras/{camera_id}`

#### Dashboard WebSocket

**15. Real-time Metrics Stream**
- **Endpoint**: `WS /ws/dashboard/{camera_id}`
- **Broadcasts**:
```json
{
  "type": "metrics",
  "camera_id": "edge_001",
  "data": {
    "people_count": 45,
    "density": 0.65,
    "risk_score": 0.35,
    "risk_level": "NORMAL"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**16. Alert Stream**
- **Endpoint**: `WS /ws/alerts`
- **Broadcasts**:
```json
{
  "type": "alert",
  "alert": {
    "id": 1,
    "camera_id": "edge_001",
    "severity": "WARNING",
    "message": "High crowd density detected"
  }
}
```

#### Video Streaming

**17. Annotated Video Stream**
- **Endpoint**: `GET /stream/{camera_id}`
- **Content-Type**: `multipart/x-mixed-replace; boundary=frame`
- **Format**: MJPEG stream with annotations

**18. Snapshot**
- **Endpoint**: `GET /api/v1/cameras/{camera_id}/snapshot`
- **Response**: JPEG image with annotations

### AI/ML Pipeline Implementation

#### Detection Service (`services/detection.py`)

**Model**: YOLOv8n (nano) for speed, YOLOv8m (medium) for accuracy
- **Library**: Ultralytics YOLOv8
- **Input**: Raw frame (numpy array)
- **Output**: List of detections
  ```python
  {
    "bbox": [x, y, w, h],
    "confidence": 0.95,
    "class_id": 0,  # person
    "class_name": "person"
  }
  ```

**Configuration**:
- Confidence threshold: 0.5
- NMS threshold: 0.4
- Model weights: Auto-download on first run
- Device: CUDA if available, else CPU

#### Tracking Service (`services/tracking.py`)

**Algorithm**: ByteTrack (preferred) or DeepSORT
- **Library**: `byte-track` or `deep-sort-realtime`
- **Input**: Detections from current frame + previous tracks
- **Output**: Tracked objects with IDs
  ```python
  {
    "track_id": 123,
    "bbox": [x, y, w, h],
    "confidence": 0.95,
    "age": 5,  # frames tracked
    "state": "confirmed"  # or "tentative"
  }
  ```

**Configuration**:
- Max age: 30 frames
- Min hits: 3 frames
- IOU threshold: 0.5
- Track buffer: 30 frames

#### Re-Identification Service (`services/reid.py`)

**Approach**: Multi-feature extraction
1. **ArcFace embeddings** (if face visible)
2. **Clothing color histogram** (HSV)
3. **CNN appearance features** (ResNet50-based)

**Library**: 
- `insightface` for ArcFace
- Custom ResNet50 for appearance features
- OpenCV for color histograms

**Output**: 512-dimensional feature vector per person

#### Analytics Engine (`services/analytics.py`)

**Functions**:

1. **Crowd Density Estimation**
   - Gaussian kernel density estimation
   - People count per unit area
   - Output: density value (0.0 - 1.0)

2. **Zone Occupancy**
   - Point-in-polygon test for each detection
   - Count people per zone
   - Compare with max capacity

3. **Movement Flow Vectors**
   - Track velocity vectors
   - Average direction per region
   - Optical flow (Lucas-Kanade) for validation

4. **Entry/Exit Counting**
   - Zone-based counting
   - Track crossing detection
   - Direction analysis

5. **Bottleneck Detection**
   - Identify low-velocity regions
   - Detect congestion patterns
   - Alert on flow stoppage

6. **Speed Estimation**
   - Calculate velocity from track positions
   - Average speed per person
   - Overall crowd velocity

#### Risk Assessment Engine (`services/risk_assessment.py`)

**Risk Score Formula**:
```python
risk_score = (
    0.3 * density_factor +
    0.25 * speed_variance_factor +
    0.2 * congestion_factor +
    0.15 * directional_conflict_factor +
    0.1 * sudden_movement_factor
)
```

**Risk Levels**:
- **NORMAL**: risk_score < 0.4
- **WARNING**: 0.4 <= risk_score < 0.7
- **CRITICAL**: risk_score >= 0.7

**Factors**:
1. **Density Factor**: Normalized density (0-1)
2. **Speed Variance**: High variance indicates panic
3. **Congestion**: Flow stoppage detection
4. **Directional Conflict**: Opposing flow vectors
5. **Sudden Movement**: Rapid acceleration detection

#### Streamer Service (`services/streamer.py`)

**Responsibilities**:
1. Draw bounding boxes with track IDs
2. Overlay people count
3. Draw heatmap overlay
4. Draw flow direction arrows
5. Display risk level indicator
6. Draw zone boundaries
7. Stream annotated frames

**Output Format**: MJPEG stream

### Dependencies (`requirements.txt`)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-socketio==5.10.0
python-multipart==0.0.6
sqlalchemy==2.0.23
aiosqlite==0.19.0
pydantic==2.5.0
pydantic-settings==2.1.0
opencv-python==4.8.1.78
ultralytics==8.1.0
numpy==1.24.3
scipy==1.11.4
scikit-learn==1.3.2
scikit-image==0.22.0
pillow==10.1.0
aiofiles==23.2.1
python-dotenv==1.0.0
```

---

## Dashboard Implementation

### Technology Stack
- **Framework**: Next.js 14+ (App Router)
- **UI Library**: React 18+
- **Styling**: Tailwind CSS 3+
- **Real-time**: Socket.io-client
- **Charts**: Recharts / Chart.js
- **Video**: HTML5 Video / HLS.js
- **State Management**: Zustand / React Context
- **HTTP Client**: Axios / Fetch API

### Core Responsibilities
1. Display live annotated video streams
2. Show real-time crowd metrics
3. Visualize heatmaps
4. Display alerts and notifications
5. Zone management interface
6. Historical analytics visualization
7. Camera management

### File Structure
```
dashboard/
├── app/
│   ├── layout.tsx
│   ├── page.tsx              # Main dashboard
│   ├── cameras/
│   │   ├── page.tsx          # Camera list
│   │   └── [cameraId]/
│   │       └── page.tsx      # Camera detail view
│   ├── analytics/
│   │   └── page.tsx          # Analytics page
│   ├── zones/
│   │   └── page.tsx          # Zone management
│   └── alerts/
│       └── page.tsx          # Alerts page
├── components/
│   ├── VideoStream.tsx       # Video player component
│   ├── MetricsCard.tsx      # Metrics display
│   ├── Heatmap.tsx          # Heatmap visualization
│   ├── AlertPanel.tsx       # Alert display
│   ├── ZoneEditor.tsx       # Zone drawing tool
│   ├── AnalyticsChart.tsx   # Charts
│   └── CameraGrid.tsx       # Camera grid view
├── lib/
│   ├── api.ts               # API client
│   ├── websocket.ts         # WebSocket client
│   └── utils.ts             # Utilities
├── hooks/
│   ├── useRealtimeMetrics.ts
│   ├── useAlerts.ts
│   └── useCameraStream.ts
├── types/
│   └── index.ts             # TypeScript types
├── public/
│   └── ...
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

### API Integration

#### API Client (`lib/api.ts`)
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Endpoints:
- GET /api/v1/cameras
- GET /api/v1/cameras/{camera_id}
- GET /api/v1/analytics/{camera_id}/realtime
- GET /api/v1/analytics/{camera_id}/history
- GET /api/v1/analytics/{camera_id}/heatmap
- GET /api/v1/alerts/active
- POST /api/v1/alerts/{alert_id}/acknowledge
- GET /api/v1/zones/{camera_id}
- POST /api/v1/zones
- PUT /api/v1/zones/{zone_id}
- DELETE /api/v1/zones/{zone_id}
```

#### WebSocket Client (`lib/websocket.ts`)
```typescript
// Connections:
- ws://localhost:8000/ws/dashboard/{camera_id}  // Real-time metrics
- ws://localhost:8000/ws/alerts                 // Alert stream
```

### Key Components

#### 1. VideoStream Component
- **Features**:
  - MJPEG stream display
  - Play/pause controls
  - Fullscreen mode
  - Snapshot capture
  - Quality selector

#### 2. MetricsCard Component
- **Displays**:
  - People count
  - Density percentage
  - Average speed
  - Risk level (color-coded)
  - Flow direction indicator

#### 3. Heatmap Component
- **Features**:
  - Overlay on video
  - Toggle visibility
  - Time range selector
  - Color intensity mapping

#### 4. AlertPanel Component
- **Features**:
  - Real-time alert list
  - Severity filtering
  - Acknowledge button
  - Sound notifications
  - Alert history

#### 5. ZoneEditor Component
- **Features**:
  - Draw polygons on video
  - Edit existing zones
  - Set zone properties
  - Visual feedback

#### 6. AnalyticsChart Component
- **Charts**:
  - People count over time
  - Density trends
  - Risk score history
  - Entry/exit counts

### Pages

#### Main Dashboard (`app/page.tsx`)
- Camera grid view
- Summary metrics
- Active alerts panel
- Quick actions

#### Camera Detail (`app/cameras/[cameraId]/page.tsx`)
- Live video stream
- Real-time metrics
- Heatmap overlay
- Zone visualization
- Historical charts

#### Analytics Page (`app/analytics/page.tsx`)
- Multi-camera comparison
- Time range selector
- Export functionality
- Custom reports

#### Zones Page (`app/zones/page.tsx`)
- Zone list per camera
- Create/edit zones
- Zone occupancy display
- Capacity management

#### Alerts Page (`app/alerts/page.tsx`)
- Alert history
- Filtering and search
- Acknowledge actions
- Alert statistics

### Dependencies (`package.json`)
```json
{
  "dependencies": {
    "next": "^14.0.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "socket.io-client": "^4.6.1",
    "axios": "^1.6.2",
    "recharts": "^2.10.3",
    "zustand": "^4.4.7",
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "@types/node": "^20.10.5",
    "@types/react": "^18.2.45",
    "typescript": "^5.3.3"
  }
}
```

---

## Model Specifications

### Detection Model: YOLOv8

**Recommended Models**:
1. **YOLOv8n** (nano) - Fastest, lower accuracy
   - Size: ~6 MB
   - Speed: ~100 FPS (GPU), ~20 FPS (CPU)
   - mAP50: ~0.50

2. **YOLOv8m** (medium) - Balanced
   - Size: ~50 MB
   - Speed: ~50 FPS (GPU), ~8 FPS (CPU)
   - mAP50: ~0.65

3. **YOLOv8x** (extra large) - Highest accuracy
   - Size: ~136 MB
   - Speed: ~25 FPS (GPU), ~3 FPS (CPU)
   - mAP50: ~0.70

**For MVP**: Use YOLOv8m for best balance

**Download**: Auto-downloaded by Ultralytics on first use

### Tracking Model: ByteTrack

**Library**: `byte-track` or `bytetrack` (PyPI)
- No additional model weights needed
- Uses detection confidence + IOU matching
- Handles occlusions well

**Alternative**: DeepSORT
- Requires Re-ID model weights
- More accurate but slower

**For MVP**: Use ByteTrack

### Re-ID Model

**Option 1: ArcFace (InsightFace)**
- Model: `arcface_r100_v1` (166 MB)
- Library: `insightface`
- Accuracy: High for face-based Re-ID

**Option 2: ResNet50-based Appearance**
- Pre-trained on Market-1501 dataset
- 512-dimensional embeddings
- Works without face visibility

**For MVP**: Use ResNet50-based (more robust)

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
1. Set up project structure
2. Initialize SQLite database
3. Create database models and schemas
4. Set up basic FastAPI server
5. Create basic Flask edge node
6. Implement health check endpoints

### Phase 2: Core AI Pipeline (Week 2)
1. Integrate YOLOv8 detection
2. Implement ByteTrack tracking
3. Build Re-ID service
4. Test detection → tracking → Re-ID flow
5. Store results in database

### Phase 3: Analytics & Risk Assessment (Week 3)
1. Implement density estimation
2. Build zone occupancy calculator
3. Create movement flow analyzer
4. Implement risk scoring algorithm
5. Build alert generation system

### Phase 4: Video Streaming & Annotation (Week 4)
1. Implement frame annotation service
2. Create MJPEG stream endpoint
3. Add heatmap overlay
4. Add zone visualization
5. Test streaming performance

### Phase 5: Dashboard (Week 5)
1. Set up Next.js project
2. Create API client
3. Implement WebSocket connections
4. Build video player component
5. Create metrics display components
6. Add charts and visualizations

### Phase 6: Integration & Testing (Week 6)
1. End-to-end testing
2. Performance optimization
3. Error handling improvements
4. Documentation
5. Deployment preparation

---

## Configuration Files

### Master Node `.env`
```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Database
DATABASE_URL=sqlite:///./vision.db

# AI Models
DETECTION_MODEL=yolov8m.pt
TRACKING_ALGORITHM=bytetrack
REID_MODEL=resnet50

# Detection Settings
DETECTION_CONFIDENCE=0.5
DETECTION_NMS_THRESHOLD=0.4

# Tracking Settings
TRACK_MAX_AGE=30
TRACK_MIN_HITS=3
TRACK_IOU_THRESHOLD=0.5

# Analytics
ANALYTICS_UPDATE_INTERVAL=1.0  # seconds
HEATMAP_DURATION=300  # seconds

# Risk Assessment
RISK_UPDATE_INTERVAL=1.0  # seconds
CRITICAL_THRESHOLD=0.7
WARNING_THRESHOLD=0.4

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/vision.log
```

### Edge Node `.env`
```env
EDGE_NODE_ID=edge_001
MASTER_NODE_URL=ws://localhost:8000/ws/frames
CAMERA_SOURCE=0
CAMERA_RESOLUTION=1920x1080
CAMERA_FPS=30
FRAME_QUALITY=85
ENCODING_FORMAT=JPEG
RECONNECT_DELAY=5
LOG_LEVEL=INFO
```

### Dashboard `.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## Performance Targets

- **Frame Processing Latency**: < 100ms (end-to-end)
- **Detection FPS**: 15-30 FPS (depending on model)
- **Dashboard Update Rate**: 1-2 Hz
- **Database Write Latency**: < 10ms
- **WebSocket Latency**: < 50ms

---

## Security Considerations

1. **Authentication**: Add JWT tokens for API access (future)
2. **CORS**: Configure CORS for dashboard domain
3. **Input Validation**: Validate all API inputs
4. **SQL Injection**: Use SQLAlchemy ORM (parameterized queries)
5. **File Upload**: Validate image formats and sizes
6. **Rate Limiting**: Implement rate limiting on APIs

---

## Deployment Notes

### Development
- Run all services locally
- Use SQLite file database
- No Docker required for MVP

### Production (Future)
- Docker containers for each service
- PostgreSQL instead of SQLite
- Redis for caching
- Nginx for reverse proxy
- GPU-enabled inference nodes

---

## Testing Strategy

1. **Unit Tests**: Test individual services
2. **Integration Tests**: Test API endpoints
3. **End-to-End Tests**: Test full pipeline
4. **Performance Tests**: Load testing
5. **Accuracy Tests**: Validate detection/tracking accuracy

---

This implementation plan provides a complete roadmap for building the VISION MVP system with all necessary details for professional implementation.

