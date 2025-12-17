# Setup Camera Feed - Quick Guide

## Problem
Camera feed not showing in dashboard because:
1. Camera not registered with master node
2. Edge node not sending frames

## Solution Implemented

I've added:
1. ✅ **WebSocket Client** (`edge-node/utils/websocket_client.py`) - Sends frames via Socket.IO
2. ✅ **Master Client** (`edge-node/utils/master_client.py`) - Registers camera automatically
3. ✅ **Socket.IO Handler** (`master-node/api/socketio_handler.py`) - Receives frames
4. ✅ **Auto-registration** - Camera registers and starts streaming automatically

## Quick Fix Steps

### 1. Update Edge Node Configuration

Edit `edge-node/.env`:
```env
MASTER_NODE_URL=http://localhost:8000
```

Or create `.env` file:
```bash
cd edge-node
cp .env.example .env
# Edit .env and set MASTER_NODE_URL=http://localhost:8000
```

### 2. Restart Both Services

**Master Node** (Terminal 1):
```bash
cd master-node
python main.py
```

**Edge Node** (Terminal 2):
```bash
cd edge-node
python app.py
```

### 3. What Should Happen

**Edge Node Logs Should Show**:
```
Camera initialized successfully from source: 0
Camera registered with master node
Connected to master node: http://localhost:8000
Streaming worker started
```

**Master Node Logs Should Show**:
```
Socket.IO client connected: <session_id>
```

### 4. Verify in Dashboard

1. Open dashboard: `dashboard/index.html`
2. Camera should appear in list
3. Select camera
4. Video stream should show frames
5. Metrics should update

## Manual Testing

### Test Camera Registration
```bash
curl http://localhost:8000/api/v1/cameras
```

Should show `edge_001` in the list.

### Test Frame Sending
Check edge node logs - should see frames being sent.

### Test Stream Endpoint
```bash
# In browser, open:
http://localhost:8000/stream/edge_001
```

Should show MJPEG stream.

## Troubleshooting

### Issue: "Failed to connect to master node"
- **Check**: Master node running on port 8000?
- **Check**: Firewall blocking connection?
- **Fix**: Verify `MASTER_NODE_URL=http://localhost:8000` in `.env`

### Issue: "Camera not registered"
- **Check**: Master node API accessible?
- **Test**: `curl http://localhost:8000/health`
- **Fix**: Make sure master node is running

### Issue: "No frames in stream"
- **Check**: Edge node logs show "Streaming worker started"?
- **Check**: Master node logs show "Socket.IO client connected"?
- **Fix**: Restart both services

### Issue: Dashboard shows "No cameras registered"
- **Check**: Camera registered? `curl http://localhost:8000/api/v1/cameras`
- **Fix**: Restart edge node to trigger auto-registration

## Expected Flow

```
Edge Node Startup
    ↓
Initialize Camera ✅
    ↓
Register with Master Node ✅
    ↓
Connect Socket.IO ✅
    ↓
Start Streaming Frames ✅
    ↓
Master Node Processes Frames ✅
    ↓
Dashboard Shows Data ✅
```

## Configuration Files

**edge-node/.env**:
```env
EDGE_NODE_ID=edge_001
MASTER_NODE_URL=http://localhost:8000  # Important: Use http:// not ws://
CAMERA_SOURCE=0
CAMERA_RESOLUTION=1920x1080
CAMERA_FPS=30
FRAME_QUALITY=85
```

After updating `.env`, restart the edge node!

