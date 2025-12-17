# Quick Fix Guide - Camera Feed Not Available

## Problem
- Camera is initialized but not registered with master node
- Edge node is not sending frames to master node
- Dashboard shows "No cameras registered"

## Solution

I've implemented the missing pieces:

### 1. WebSocket Client (Edge Node)
- Created `edge-node/utils/websocket_client.py`
- Implements Socket.IO client to send frames

### 2. Master Client (Edge Node)
- Created `edge-node/utils/master_client.py`
- Registers camera with master node automatically

### 3. Socket.IO Handler (Master Node)
- Created `master-node/api/socketio_handler.py`
- Handles Socket.IO connections from edge nodes

### 4. Auto-Registration & Streaming
- Edge node now auto-registers camera on startup
- Auto-starts streaming frames to master node

## Steps to Fix

### Step 1: Restart Master Node
```bash
cd master-node
python main.py
```

### Step 2: Restart Edge Node
```bash
cd edge-node
python app.py
```

The edge node will now:
1. Initialize camera ✅
2. Register with master node ✅
3. Start streaming frames automatically ✅

### Step 3: Check Dashboard
- Refresh the dashboard
- Camera should appear in the list
- Video stream should start showing frames

## Manual Registration (if auto-registration fails)

If auto-registration doesn't work, manually register:

```bash
curl -X POST http://localhost:8000/api/v1/cameras/register \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "edge_001",
    "edge_node_id": "edge_001",
    "location": "Test Location",
    "resolution": "1280x720",
    "fps": 30
  }'
```

Then start streaming manually:

```bash
curl -X POST http://localhost:5000/stream/start \
  -H "Content-Type: application/json" \
  -d '{
    "master_url": "http://localhost:8000/socket.io",
    "camera_id": "edge_001"
  }'
```

## Verify It's Working

1. **Check Master Node Logs**:
   - Should see "Socket.IO client connected"
   - Should see frame processing logs

2. **Check Edge Node Logs**:
   - Should see "Connected to master node"
   - Should see "Camera registered with master node"
   - Should see frame sending logs

3. **Check Dashboard**:
   - Camera should appear in list
   - Metrics should update
   - Video stream should show frames

## Troubleshooting

### Issue: "Failed to connect to master node"
- Make sure master node is running on port 8000
- Check firewall settings
- Verify Socket.IO URL is correct

### Issue: "Camera not registered"
- Check master node is running
- Verify API endpoint is accessible: `http://localhost:8000/api/v1/cameras`
- Check master node logs for errors

### Issue: "No frames being sent"
- Check camera is initialized: `curl http://localhost:5000/camera/status`
- Check streaming is active: Look for "Streaming worker started" in logs
- Verify WebSocket connection: Check for "Connected to master node" in logs

