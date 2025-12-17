# Entry/Exit Zone Setup Guide

This guide explains how to configure and use entry/exit zones in the VISION system.

## Overview

Entry/exit zones allow you to track when people enter or exit specific areas in your camera feed. The system:
- Tracks objects as they move across zone boundaries
- Detects when objects enter or exit zones
- Logs entry/exit events to the database
- Displays counts in the dashboard

## Step 1: Create Entry/Exit Zones

### Using the API

Create zones via the Master Node API:

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

**Parameters**:
- `camera_id`: Your camera ID (e.g., "edge_001")
- `zone_name`: Name for the zone (e.g., "Main Entrance", "Exit Door")
- `zone_type`: `"entry"` or `"exit"` (or `"monitor"` for general monitoring)
- `polygon_coords`: Array of `[x, y]` coordinates defining the zone boundary
  - Coordinates are in pixels relative to the camera frame
  - Minimum 3 points (triangle), typically 4 points (rectangle)
  - Points should be in clockwise or counter-clockwise order
- `max_capacity`: Optional maximum occupancy for the zone

### Example: Creating Entry Zone

```bash
curl -X POST "http://localhost:8000/api/v1/zones" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### Example: Creating Exit Zone

```bash
curl -X POST "http://localhost:8000/api/v1/zones" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "edge_001",
    "zone_name": "Side Exit",
    "zone_type": "exit",
    "polygon_coords": [
      [1200, 200],
      [1800, 200],
      [1800, 600],
      [1200, 600]
    ]
  }'
```

## Step 2: Finding Zone Coordinates

To find the correct coordinates for your zones:

### Method 1: Using the Dashboard

1. Open the dashboard: `http://localhost:8000/dashboard/index.html`
2. View the video stream
3. Note the pixel coordinates where you want to define zones
4. Use those coordinates in the API request

### Method 2: Using Browser Developer Tools

1. Open the dashboard in your browser
2. Right-click on the video stream → "Inspect Element"
3. Use the browser's element inspector to find coordinates
4. Or use a screenshot tool that shows pixel coordinates

### Method 3: Using a Test Script

Create a simple script to capture frame coordinates:

```python
import cv2
import numpy as np

# Capture from camera
cap = cv2.VideoCapture(0)

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Point: [{x}, {y}]")

cv2.namedWindow('Frame')
cv2.setMouseCallback('Frame', mouse_callback)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    cv2.imshow('Frame', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

## Step 3: Zone Types

### Entry Zone (`zone_type: "entry"`)
- Tracks when objects **enter** the zone
- Counts people entering the area
- Useful for: entrances, checkpoints, doorways

### Exit Zone (`zone_type: "exit"`)
- Tracks when objects **exit** the zone
- Counts people leaving the area
- Useful for: exits, doorways, boundaries

### Monitor Zone (`zone_type: "monitor"`)
- General monitoring zone
- Tracks occupancy but not entry/exit events
- Useful for: general areas, waiting rooms

## Step 4: Viewing Entry/Exit Data

### Via API

**Get Entry/Exit Logs**:
```bash
GET /api/v1/analytics/entry-exit/{camera_id}?limit=100
```

**Response**:
```json
{
  "events": [
    {
      "id": 1,
      "camera_id": "edge_001",
      "zone_id": 1,
      "zone_name": "Main Entrance",
      "track_id": 123,
      "event_type": "entry",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "entry_count": 1,
  "exit_count": 0
}
```

### Via Dashboard

The dashboard automatically displays entry/exit counts for zones with `zone_type` of "entry" or "exit".

## Step 5: Zone Configuration Tips

### 1. Zone Size
- **Too small**: May miss detections
- **Too large**: May cause false positives
- **Recommended**: Cover the area where people typically cross

### 2. Zone Placement
- Place entry zones at actual entry points (doors, gates)
- Place exit zones at actual exit points
- Avoid overlapping zones if possible

### 3. Coordinate System
- Origin (0, 0) is at **top-left** of the frame
- X increases to the **right**
- Y increases **downward**
- Coordinates are in **pixels**

### 4. Polygon Shape
- **Rectangle**: Most common, 4 points
- **Triangle**: 3 points
- **Complex shapes**: Any number of points (minimum 3)

## Example: Complete Setup

```bash
# 1. Create Entry Zone
curl -X POST "http://localhost:8000/api/v1/zones" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "edge_001",
    "zone_name": "Front Door Entry",
    "zone_type": "entry",
    "polygon_coords": [[200, 150], [600, 150], [600, 450], [200, 450]],
    "max_capacity": 30
  }'

# 2. Create Exit Zone
curl -X POST "http://localhost:8000/api/v1/zones" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "edge_001",
    "zone_name": "Back Door Exit",
    "zone_type": "exit",
    "polygon_coords": [[1000, 200], [1600, 200], [1600, 500], [1000, 500]]
  }'

# 3. Verify Zones
curl "http://localhost:8000/api/v1/zones/edge_001"

# 4. View Entry/Exit Logs
curl "http://localhost:8000/api/v1/analytics/entry-exit/edge_001?limit=50"
```

## Troubleshooting

### No Entry/Exit Events Logged
1. **Check zone type**: Ensure `zone_type` is "entry" or "exit"
2. **Check zone coordinates**: Verify coordinates are within frame bounds
3. **Check camera feed**: Ensure camera is streaming and detecting people
4. **Check zone status**: Ensure zone `status` is "active"

### False Positives
- Reduce zone size
- Adjust zone position
- Check for camera movement/vibration

### Missing Events
- Increase zone size slightly
- Check detection confidence threshold
- Verify tracking is working correctly

## Next Steps

After setting up zones:
1. Monitor entry/exit counts in the dashboard
2. Set up alerts for high entry/exit rates
3. Analyze historical entry/exit patterns
4. Adjust zones based on actual usage

