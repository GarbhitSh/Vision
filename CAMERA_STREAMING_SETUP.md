# Complete Camera Streaming Setup

## Overview

The VISION system now supports complete camera streaming with real-time video feed, annotations, and analytics overlays.

## How It Works

### 1. **Edge Node → Master Node**
- Edge node captures frames from camera
- Encodes frames to JPEG
- Sends frames to Master Node via Socket.IO

### 2. **Master Node Processing**
- Receives frames via Socket.IO
- Processes through AI pipeline:
  - Detection (YOLOv8)
  - Tracking (ByteTrack)
  - Re-ID feature extraction
  - Analytics computation
  - Risk assessment
- **Caches frames** for streaming

### 3. **Streaming Endpoint**
- Serves MJPEG stream at `/stream/{camera_id}`
- Uses cached frames for real-time display
- Adds annotations:
  - Bounding boxes
  - Track IDs
  - Zone boundaries
  - Metrics overlay
  - Heatmap (optional)

## Setup Instructions

### 1. Start Master Node
```bash
cd master-node
python main.py
```

### 2. Start Edge Node
```bash
cd edge-node
python app.py
```

The edge node will:
- Initialize camera
- Register with master node
- Start streaming frames automatically

### 3. View Stream

**Option 1: Direct URL**
```
http://localhost:8000/stream/edge_001
```

**Option 2: HTML Dashboard**
Open `dashboard/index.html` in browser and select camera from dropdown.

**Option 3: Embed in HTML**
```html
<img src="http://localhost:8000/stream/edge_001" />
```

## Stream Parameters

### Query Parameters
- `show_heatmap` (bool): Show heatmap overlay (default: false)
- `show_zones` (bool): Show zone boundaries (default: true)
- `show_track_ids` (bool): Show track IDs (default: true)
- `show_metrics` (bool): Show metrics overlay (default: true)

### Examples

**Basic stream:**
```
http://localhost:8000/stream/edge_001
```

**With heatmap:**
```
http://localhost:8000/stream/edge_001?show_heatmap=true
```

**Minimal annotations:**
```
http://localhost:8000/stream/edge_001?show_zones=false&show_track_ids=false
```

## Stream Features

### 1. **Real-time Metrics Overlay**
- People count
- Density percentage
- Average speed
- Congestion level
- Risk score and level
- Timestamp

### 2. **Visual Annotations**
- **Bounding boxes**: Green boxes around detected people
- **Track IDs**: White labels showing track ID for each person
- **Zones**: Magenta polygons showing monitoring zones
- **Flow arrows**: Yellow arrows showing movement direction
- **Heatmap**: Color-coded density overlay (optional)

### 3. **Risk Indicator**
- Green bar: NORMAL risk
- Orange bar: WARNING risk
- Red bar: CRITICAL risk

## Troubleshooting

### Issue: "Waiting for frames..." message

**Possible causes:**
1. Edge node not running
2. Camera not initialized
3. Frames not being sent to master node
4. Frame cache empty

**Solutions:**

1. **Check edge node status:**
   ```bash
   curl http://localhost:5000/camera/status
   ```

2. **Check camera initialization:**
   ```bash
   curl http://localhost:5000/camera/test
   ```

3. **Reinitialize camera:**
   ```bash
   curl -X POST http://localhost:5000/camera/reinitialize
   ```

4. **Check master node logs:**
   - Look for Socket.IO connection messages
   - Check for frame processing errors

5. **Verify camera registration:**
   ```bash
   curl http://localhost:8000/api/v1/cameras
   ```

### Issue: Stream is slow or laggy

**Solutions:**
1. Reduce frame quality in edge node settings
2. Lower FPS in edge node settings
3. Check network bandwidth
4. Reduce annotation complexity (disable heatmap, zones, etc.)

### Issue: No annotations visible

**Check:**
1. Ensure detections are being made (check logs)
2. Verify zones are configured
3. Check that `show_*` parameters are set correctly

## Configuration

### Edge Node Settings (`edge-node/config/settings.py`)
```python
CAMERA_SOURCE = 0  # Camera index or URL
CAMERA_FPS = 30
FRAME_QUALITY = 85  # JPEG quality (1-100)
MASTER_NODE_URL = "http://localhost:8000"
```

### Frame Cache Settings (`master-node/services/frame_cache.py`)
```python
max_frames = 10  # Frames to cache per camera
ttl_seconds = 5  # Time to live for cached frames
```

### Stream Settings (`master-node/api/routes/streaming.py`)
- Frame rate: ~30 FPS (0.033s delay between frames)
- JPEG quality: 85 (for streaming)

## API Endpoints

### MJPEG Stream
```
GET /stream/{camera_id}
```
Returns: `multipart/x-mixed-replace` MJPEG stream

### Snapshot
```
GET /api/v1/cameras/{camera_id}/snapshot?annotated=true
```
Returns: JPEG image

## Performance Tips

1. **For best performance:**
   - Use GPU for detection/tracking
   - Reduce frame resolution if needed
   - Lower FPS for less CPU usage
   - Disable heatmap for faster processing

2. **For multiple cameras:**
   - Each camera has its own frame cache
   - Processing is independent per camera
   - Stream endpoints can handle multiple concurrent connections

3. **Network optimization:**
   - Use JPEG encoding (already implemented)
   - Adjust quality based on bandwidth
   - Consider WebP for better compression

## Example: Complete Setup

```bash
# Terminal 1: Start Master Node
cd master-node
python main.py

# Terminal 2: Start Edge Node
cd edge-node
python app.py

# Terminal 3: View Stream
# Open browser: http://localhost:8000/stream/edge_001
```

## Next Steps

1. **Multiple Cameras**: Add more edge nodes for multiple camera feeds
2. **Recording**: Implement frame recording for playback
3. **Alerts**: Set up alerts based on stream analytics
4. **Dashboard**: Enhance dashboard with multiple camera views

