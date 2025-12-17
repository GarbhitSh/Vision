# Performance Fix for Frame Processing

## Problem
Frame processing is taking ~1.4 seconds per frame, but frames are arriving at 30 FPS (every 33ms). This creates a huge backlog and causes disconnections.

## Solution Implemented

### 1. **Asynchronous Frame Processing**
- Frames are now queued and processed in background threads
- Socket.IO handler returns immediately (non-blocking)
- Prevents connection timeouts

### 2. **Frame Queue Management**
- Queue size limited to 10 frames
- Older frames are automatically dropped if queue is full
- Keeps only the most recent frames

### 3. **Reduce Frame Rate (Recommended)**

Since processing takes ~1.4 seconds, you should reduce the frame rate to match:

**Option 1: Reduce to 1 FPS (1 frame per second)**
```bash
# In edge-node/.env or set environment variable
CAMERA_FPS=1
```

**Option 2: Reduce to 2 FPS (2 frames per second)**
```bash
CAMERA_FPS=2
```

**Option 3: Reduce to 5 FPS (5 frames per second)**
```bash
CAMERA_FPS=5
```

This will still give you real-time monitoring but at a rate the system can handle.

## Quick Fix

### Step 1: Reduce Frame Rate

Create or edit `edge-node/.env`:
```env
CAMERA_FPS=2
FRAME_QUALITY=70
```

Or set environment variable:
```bash
export CAMERA_FPS=2
```

### Step 2: Restart Edge Node

```bash
cd edge-node
python app.py
```

## Expected Results

After reducing FPS:
- Connection should stay stable
- No more "Slow frame processing" warnings
- Frames will process in real-time
- Stream will update smoothly

## Performance Optimization Tips

1. **Lower FPS**: Start with 1-2 FPS, increase if processing improves
2. **Lower Quality**: Reduce `FRAME_QUALITY` to 70-75 for faster processing
3. **Lower Resolution**: Use 640x480 or 1280x720 instead of 1920x1080
4. **GPU Acceleration**: If available, use GPU for YOLO detection (much faster)

## Monitoring

Watch the logs for:
- "Slow frame processing" warnings should disappear
- Connection should remain stable
- Frame processing time should be < 1000ms

## Future Improvements

1. **GPU Acceleration**: Use GPU for YOLO detection (10-50x faster)
2. **Frame Skipping**: Skip frames if processing queue is full
3. **Batch Processing**: Process multiple frames in parallel
4. **Optimized Models**: Use smaller/faster models (YOLOv8n instead of YOLOv8m)

