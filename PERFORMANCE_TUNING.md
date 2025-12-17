# Performance Tuning Guide

## Issue: Slow Frame Processing

The system is experiencing slow frame processing (~1.4-1.8 seconds per frame), which causes:
- Connection timeouts
- Frame queue buildup
- Disconnections

## Current Performance

- **Frame Processing Time**: ~1.4-1.8 seconds per frame
- **Edge Node Frame Rate**: 30 FPS (sending every ~33ms)
- **Problem**: Processing can't keep up with sending rate

## Solutions

### Option 1: Reduce Frame Rate (Implemented)

The edge node now sends frames at **0.5 FPS** (1 frame every 2 seconds) to match processing speed.

**To adjust:**
Edit `edge-node/app.py` in `streaming_worker()`:
```python
target_fps = 0.5  # 1 frame every 2 seconds
```

**Recommended FPS based on processing time:**
- Processing < 500ms: Use 1-2 FPS
- Processing 500-1000ms: Use 0.5-1 FPS  
- Processing > 1000ms: Use 0.2-0.5 FPS

### Option 2: Use GPU Acceleration

If you have a GPU available:

1. **Install CUDA-enabled PyTorch:**
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

2. **The system will automatically use GPU** if available (check logs for "on cuda" vs "on cpu")

### Option 3: Reduce Frame Resolution

Lower resolution = faster processing:

Edit `edge-node/config/settings.py`:
```python
CAMERA_RESOLUTION = "640x480"  # Instead of 1280x720
```

### Option 4: Reduce JPEG Quality

Lower quality = smaller frames = faster transmission:

Edit `edge-node/config/settings.py`:
```python
FRAME_QUALITY = 60  # Instead of 85 (1-100)
```

### Option 5: Use Lighter Models

For faster processing, use smaller YOLO models:

Edit `master-node/ml/detectors.py`:
```python
model_name = "yolov8n.pt"  # nano (fastest) instead of yolov8m.pt (medium)
```

Available models (fastest to slowest):
- `yolov8n.pt` - Nano (fastest, less accurate)
- `yolov8s.pt` - Small
- `yolov8m.pt` - Medium (current)
- `yolov8l.pt` - Large
- `yolov8x.pt` - Extra Large (slowest, most accurate)

## Monitoring Performance

### Check Processing Time

Master node logs show:
```
WARNING - Slow frame processing: 1453.3ms for frame 20
```

### Check Frame Rate

Edge node logs show:
```
INFO - Sent 10 frames (FPS: 0.5)
```

### Check Connection Stability

Monitor for:
- Frequent reconnections
- "Connection lost" messages
- Frame sending failures

## Recommended Settings

### For Development/Testing (CPU only):
- **FPS**: 0.5 (1 frame every 2 seconds)
- **Resolution**: 640x480
- **Quality**: 70
- **Model**: yolov8n.pt (nano)

### For Production (with GPU):
- **FPS**: 2-5 FPS
- **Resolution**: 1280x720
- **Quality**: 85
- **Model**: yolov8m.pt (medium)

### For Maximum Performance (GPU + optimized):
- **FPS**: 10-15 FPS
- **Resolution**: 1920x1080
- **Quality**: 85
- **Model**: yolov8s.pt (small)

## Troubleshooting

### Still Getting Disconnections?

1. **Reduce FPS further:**
   ```python
   target_fps = 0.2  # 1 frame every 5 seconds
   ```

2. **Check processing time** - if consistently > 2 seconds, reduce FPS or use GPU

3. **Check network** - ensure stable connection between edge and master nodes

### Processing Too Slow?

1. **Use GPU** if available
2. **Reduce resolution** to 640x480
3. **Use smaller model** (yolov8n.pt)
4. **Reduce quality** to 60

### Want Higher Frame Rate?

1. **Use GPU** - biggest performance boost
2. **Use smaller model** - yolov8n or yolov8s
3. **Reduce resolution** - 640x480 processes much faster
4. **Optimize code** - consider async processing or frame skipping

## Current Configuration

The system is now configured for **stable operation** with:
- **Frame Rate**: 0.5 FPS (1 frame every 2 seconds)
- **Auto-reconnection**: Enabled
- **Frame skipping**: Automatic (if connection lost)
- **Error handling**: Improved

This ensures stable connections even with slow processing.

