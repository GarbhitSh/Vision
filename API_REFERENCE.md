# VISION - API Reference

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: Configure via environment variable

## Authentication
Currently: None (add JWT in future)
Headers: `Content-Type: application/json`

---

## Frame Ingestion

### WebSocket: Frame Reception
**Endpoint**: `WS /ws/frames`

**Connection**:
```javascript
const socket = io('ws://localhost:8000/ws/frames');
```

**Send Frame**:
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

**Response**:
```json
{
  "status": "received",
  "frame_id": 12345,
  "processing_time_ms": 45
}
```

---

### HTTP: Frame Upload
**Endpoint**: `POST /api/v1/frames/upload`

**Content-Type**: `multipart/form-data`

**Form Data**:
- `camera_id` (string, required)
- `frame` (file, required) - JPEG image
- `timestamp` (string, optional) - ISO timestamp

**Response**:
```json
{
  "status": "success",
  "frame_id": 12345,
  "processing_time_ms": 45
}
```

**Error Response**:
```json
{
  "detail": "Invalid frame format"
}
```

---

## Analytics

### Get Real-time Metrics
**Endpoint**: `GET /api/v1/analytics/{camera_id}/realtime`

**Path Parameters**:
- `camera_id` (string, required)

**Response**:
```json
{
  "camera_id": "edge_001",
  "timestamp": "2024-01-01T12:00:00Z",
  "people_count": 45,
  "density": 0.65,
  "avg_speed": 1.2,
  "flow_direction": {
    "x": 0.3,
    "y": -0.5
  },
  "congestion_level": "medium",
  "risk_score": 0.35,
  "risk_level": "NORMAL"
}
```

**Status Codes**:
- `200` - Success
- `404` - Camera not found

---

### Get Historical Analytics
**Endpoint**: `GET /api/v1/analytics/{camera_id}/history`

**Path Parameters**:
- `camera_id` (string, required)

**Query Parameters**:
- `start_time` (string, optional) - ISO timestamp
- `end_time` (string, optional) - ISO timestamp
- `interval` (integer, optional) - Aggregation interval in seconds (default: 60)

**Example**:
```
GET /api/v1/analytics/edge_001/history?start_time=2024-01-01T10:00:00Z&end_time=2024-01-01T12:00:00Z&interval=60
```

**Response**:
```json
{
  "camera_id": "edge_001",
  "start_time": "2024-01-01T10:00:00Z",
  "end_time": "2024-01-01T12:00:00Z",
  "interval": 60,
  "data": [
    {
      "timestamp": "2024-01-01T10:00:00Z",
      "people_count": 45,
      "density": 0.65,
      "avg_speed": 1.2,
      "risk_score": 0.35
    },
    {
      "timestamp": "2024-01-01T10:01:00Z",
      "people_count": 48,
      "density": 0.68,
      "avg_speed": 1.3,
      "risk_score": 0.38
    }
  ]
}
```

---

### Get Heatmap Data
**Endpoint**: `GET /api/v1/analytics/{camera_id}/heatmap`

**Path Parameters**:
- `camera_id` (string, required)

**Query Parameters**:
- `duration` (integer, optional) - Duration in seconds (default: 300)

**Response**:
```json
{
  "camera_id": "edge_001",
  "heatmap": "base64_encoded_image",
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "duration": 300
}
```

---

## Alerts

### Get Active Alerts
**Endpoint**: `GET /api/v1/alerts/active`

**Query Parameters**:
- `camera_id` (string, optional) - Filter by camera
- `severity` (string, optional) - Filter by severity (NORMAL/WARNING/CRITICAL)
- `limit` (integer, optional) - Max results (default: 100)

**Response**:
```json
{
  "alerts": [
    {
      "id": 1,
      "camera_id": "edge_001",
      "alert_type": "high_density",
      "severity": "WARNING",
      "risk_score": 0.65,
      "message": "High crowd density detected: 65%",
      "timestamp": "2024-01-01T12:00:00Z",
      "acknowledged": false
    },
    {
      "id": 2,
      "camera_id": "edge_001",
      "alert_type": "stampede_risk",
      "severity": "CRITICAL",
      "risk_score": 0.85,
      "message": "CRITICAL: Stampede risk detected",
      "timestamp": "2024-01-01T12:01:00Z",
      "acknowledged": false
    }
  ],
  "total": 2
}
```

---

### Acknowledge Alert
**Endpoint**: `POST /api/v1/alerts/{alert_id}/acknowledge`

**Path Parameters**:
- `alert_id` (integer, required)

**Response**:
```json
{
  "status": "acknowledged",
  "alert_id": 1,
  "acknowledged_at": "2024-01-01T12:05:00Z"
}
```

**Error Response**:
```json
{
  "detail": "Alert not found"
}
```

---

## Zones

### Create Zone
**Endpoint**: `POST /api/v1/zones`

**Request Body**:
```json
{
  "camera_id": "edge_001",
  "zone_name": "Main Entrance",
  "zone_type": "entry",
  "polygon_coords": [
    [100, 100],
    [500, 100],
    [500, 400],
    [100, 400]
  ],
  "max_capacity": 50
}
```

**Response**:
```json
{
  "id": 1,
  "camera_id": "edge_001",
  "zone_name": "Main Entrance",
  "zone_type": "entry",
  "polygon_coords": [[100, 100], [500, 100], [500, 400], [100, 400]],
  "max_capacity": 50,
  "current_occupancy": 0,
  "status": "active",
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

### Get Zones
**Endpoint**: `GET /api/v1/zones/{camera_id}`

**Path Parameters**:
- `camera_id` (string, required)

**Response**:
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
      "current_occupancy": 32,
      "status": "active",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

---

### Update Zone
**Endpoint**: `PUT /api/v1/zones/{zone_id}`

**Path Parameters**:
- `zone_id` (integer, required)

**Request Body**: Same as Create Zone

**Response**: Same as Create Zone

---

### Delete Zone
**Endpoint**: `DELETE /api/v1/zones/{zone_id}`

**Path Parameters**:
- `zone_id` (integer, required)

**Response**:
```json
{
  "status": "deleted",
  "zone_id": 1
}
```

---

## Cameras

### Register Camera
**Endpoint**: `POST /api/v1/cameras/register`

**Request Body**:
```json
{
  "camera_id": "edge_001",
  "edge_node_id": "edge_001",
  "location": "Building A - Main Entrance",
  "resolution": "1920x1080",
  "fps": 30
}
```

**Response**:
```json
{
  "camera_id": "edge_001",
  "edge_node_id": "edge_001",
  "location": "Building A - Main Entrance",
  "resolution": "1920x1080",
  "fps": 30,
  "status": "active",
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

### Get Camera List
**Endpoint**: `GET /api/v1/cameras`

**Query Parameters**:
- `status` (string, optional) - Filter by status (active/inactive)

**Response**:
```json
{
  "cameras": [
    {
      "camera_id": "edge_001",
      "edge_node_id": "edge_001",
      "location": "Building A - Main Entrance",
      "resolution": "1920x1080",
      "fps": 30,
      "status": "active",
      "last_frame_time": "2024-01-01T12:00:00Z",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Get Camera Details
**Endpoint**: `GET /api/v1/cameras/{camera_id}`

**Path Parameters**:
- `camera_id` (string, required)

**Response**:
```json
{
  "camera_id": "edge_001",
  "edge_node_id": "edge_001",
  "location": "Building A - Main Entrance",
  "resolution": "1920x1080",
  "fps": 30,
  "status": "active",
  "last_frame_time": "2024-01-01T12:00:00Z",
  "total_frames_processed": 12500,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

---

## Video Streaming

### Annotated Video Stream
**Endpoint**: `GET /stream/{camera_id}`

**Path Parameters**:
- `camera_id` (string, required)

**Content-Type**: `multipart/x-mixed-replace; boundary=frame`

**Usage**: Use in `<img>` tag or video player supporting MJPEG

**Example**:
```html
<img src="http://localhost:8000/stream/edge_001" />
```

---

### Snapshot
**Endpoint**: `GET /api/v1/cameras/{camera_id}/snapshot`

**Path Parameters**:
- `camera_id` (string, required)

**Query Parameters**:
- `annotated` (boolean, optional) - Include annotations (default: true)

**Response**: JPEG image

**Content-Type**: `image/jpeg`

---

## WebSocket Streams

### Real-time Metrics Stream
**Endpoint**: `WS /ws/dashboard/{camera_id}`

**Path Parameters**:
- `camera_id` (string, required)

**Connection**:
```javascript
const socket = io('ws://localhost:8000/ws/dashboard/edge_001');
```

**Received Messages**:
```json
{
  "type": "metrics",
  "camera_id": "edge_001",
  "data": {
    "people_count": 45,
    "density": 0.65,
    "avg_speed": 1.2,
    "flow_direction": {"x": 0.3, "y": -0.5},
    "congestion_level": "medium",
    "risk_score": 0.35,
    "risk_level": "NORMAL"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Update Frequency**: ~1-2 Hz

---

### Alert Stream
**Endpoint**: `WS /ws/alerts`

**Connection**:
```javascript
const socket = io('ws://localhost:8000/ws/alerts');
```

**Received Messages**:
```json
{
  "type": "alert",
  "alert": {
    "id": 1,
    "camera_id": "edge_001",
    "alert_type": "high_density",
    "severity": "WARNING",
    "risk_score": 0.65,
    "message": "High crowd density detected: 65%",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

---

## Health & Status

### Health Check
**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

### API Documentation
**Endpoint**: `GET /docs`

Swagger UI documentation (auto-generated by FastAPI)

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

**Common Status Codes**:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

---

## Rate Limiting

Currently: None (implement in production)

Future: 100 requests/minute per IP

---

## WebSocket Reconnection

Clients should implement automatic reconnection with exponential backoff:
- Initial delay: 1 second
- Max delay: 30 seconds
- Max retries: Unlimited

---

## Data Types

### Timestamp Format
ISO 8601: `YYYY-MM-DDTHH:mm:ss.sssZ`

Example: `2024-01-01T12:00:00.123Z`

### Polygon Coordinates
Array of `[x, y]` points in pixel coordinates relative to frame dimensions.

Example: `[[100, 100], [500, 100], [500, 400], [100, 400]]`

### Flow Direction
Normalized vector `{x: float, y: float}` where:
- `x`: Horizontal component (-1 to 1, positive = right)
- `y`: Vertical component (-1 to 1, positive = down)

### Risk Levels
- `NORMAL`: risk_score < 0.4
- `WARNING`: 0.4 <= risk_score < 0.7
- `CRITICAL`: risk_score >= 0.7

---

## Example Usage

### Python (requests)
```python
import requests

# Get real-time metrics
response = requests.get('http://localhost:8000/api/v1/analytics/edge_001/realtime')
metrics = response.json()
print(f"People count: {metrics['people_count']}")
print(f"Risk level: {metrics['risk_level']}")
```

### JavaScript (fetch)
```javascript
// Get active alerts
fetch('http://localhost:8000/api/v1/alerts/active')
  .then(res => res.json())
  .then(data => {
    console.log('Active alerts:', data.alerts);
  });
```

### JavaScript (Socket.io)
```javascript
import io from 'socket.io-client';

// Connect to metrics stream
const socket = io('ws://localhost:8000/ws/dashboard/edge_001');

socket.on('connect', () => {
  console.log('Connected to metrics stream');
});

socket.on('metrics', (data) => {
  console.log('People count:', data.data.people_count);
  console.log('Risk level:', data.data.risk_level);
});
```

