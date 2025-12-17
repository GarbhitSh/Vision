# Socket.IO Connection Fix

## Issue
The edge node is failing to connect to the master node via Socket.IO with the error:
```
websocket-client package not installed, only polling transport is available
Failed to connect to master node: One or more namespaces failed to connect
```

## Solution

### Step 1: Install Missing Dependency

Install the `websocket-client` package in the edge node virtual environment:

```bash
cd edge-node
pip install websocket-client
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### Step 2: Verify Master Node is Running

Make sure the master node is running and accessible:

```bash
# In master-node directory
python main.py
```

You should see:
```
INFO: Uvicorn running on http://0.0.0.0:8000
Socket.IO handler setup complete
```

### Step 3: Test Connection

Restart the edge node:

```bash
cd edge-node
python app.py
```

You should now see:
```
Connected to master node: http://localhost:8000
Streaming started to http://localhost:8000 for camera edge_001
```

## What Was Fixed

1. **Added `websocket-client` to requirements.txt**
   - Enables WebSocket transport (faster than polling)
   - Falls back to polling if WebSocket unavailable

2. **Improved Connection Handling**
   - Better error messages
   - Proper connection state checking
   - Waits for connection confirmation
   - Handles connection errors gracefully

3. **Transport Selection**
   - Tries WebSocket first (faster)
   - Falls back to polling if needed
   - Both transports work, WebSocket is preferred

## Troubleshooting

### Still Getting Connection Errors?

1. **Check Master Node URL:**
   ```python
   # In edge-node/config/settings.py or .env
   MASTER_NODE_URL = "http://localhost:8000"  # Must be http:// not ws://
   ```

2. **Check Master Node is Accessible:**
   ```bash
   curl http://localhost:8000/api/v1/cameras
   ```

3. **Check Firewall/Ports:**
   - Master node should be listening on port 8000
   - Edge node should be able to reach it

4. **Check Socket.IO Endpoint:**
   - Master node mounts Socket.IO at `/socket.io/`
   - Client automatically uses this path

5. **View Detailed Logs:**
   - Check master node logs for Socket.IO connection messages
   - Check edge node logs for connection attempts

### Connection Works But No Frames?

1. **Check Camera:**
   ```bash
   curl http://localhost:5000/camera/status
   ```

2. **Check Streaming Status:**
   ```bash
   curl http://localhost:5000/stream/status
   ```

3. **Manually Start Streaming:**
   ```bash
   curl -X POST http://localhost:5000/stream/start
   ```

## Expected Behavior

### Successful Connection:
```
2025-12-17 23:42:05,987 - websocket_client - INFO - Connecting to Socket.IO server: http://localhost:8000
2025-12-17 23:42:06,123 - websocket_client - INFO - Connected to master node: http://localhost:8000
2025-12-17 23:42:06,124 - websocket_client - INFO - Socket.IO connection confirmed
2025-12-17 23:42:06,125 - edge_node - INFO - Streaming started to http://localhost:8000 for camera edge_001
```

### Master Node Should Show:
```
INFO: Socket.IO client connected: <session_id>
```

## Next Steps

Once connected:
1. Frames will automatically stream from edge node to master node
2. Master node will process frames through AI pipeline
3. Stream will be available at: `http://localhost:8000/stream/edge_001`
4. Check dashboard for real-time metrics

