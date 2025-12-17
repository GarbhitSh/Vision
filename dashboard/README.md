# VISION Dashboard

Simple HTML dashboard for VISION crowd monitoring system.

## Features

- 📊 **Real-time Metrics**: People count, density, speed, congestion, risk level
- 👥 **Detection Summary**: Total detections and active tracks
- 🚪 **Entry/Exit Logs**: Zone-based entry/exit counts
- 📹 **Live Video Stream**: MJPEG stream with annotations
- ⚠️ **Active Alerts**: Real-time alert notifications
- 📷 **Camera Management**: List and select cameras

## Usage

1. **Open the dashboard**:
   - Simply open `index.html` in a web browser
   - Or serve it using a web server:
     ```bash
     # Python
     python -m http.server 8080
     
     # Node.js
     npx http-server -p 8080
     ```

2. **Configure API URL**:
   - Default: `http://localhost:8000`
   - Change in the dashboard if your API is on a different host/port

3. **Select a Camera**:
   - Cameras are automatically loaded
   - Select from dropdown or click on camera card
   - Dashboard will start showing real-time data

4. **Auto-Refresh**:
   - Click "Start Auto-Refresh" to enable automatic updates (every 2 seconds)
   - Click "Stop Auto-Refresh" to disable

## API Endpoints Used

- `GET /api/v1/cameras` - List all cameras
- `GET /api/v1/analytics/{camera_id}/realtime` - Real-time metrics
- `GET /api/v1/zones/{camera_id}` - Get zones (for entry/exit)
- `GET /api/v1/alerts/active` - Get active alerts
- `GET /stream/{camera_id}` - MJPEG video stream

## Browser Compatibility

Works in all modern browsers:
- Chrome/Edge ✅
- Firefox ✅
- Safari ✅
- Mobile browsers ✅

## Notes

- Entry/Exit counts are shown for zones with `zone_type` of "entry" or "exit"
- Video stream requires camera to be actively sending frames
- All data updates automatically when auto-refresh is enabled

