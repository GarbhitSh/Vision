# Entry/Exit Zones - Quick Start

## Quick Setup (3 Steps)

### 1. Create an Entry Zone

```bash
curl -X POST "http://localhost:8000/api/v1/zones" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "edge_001",
    "zone_name": "Main Entrance",
    "zone_type": "entry",
    "polygon_coords": [[100, 100], [500, 100], [500, 400], [100, 400]]
  }'
```

### 2. Create an Exit Zone

```bash
curl -X POST "http://localhost:8000/api/v1/zones" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "edge_001",
    "zone_name": "Side Exit",
    "zone_type": "exit",
    "polygon_coords": [[1200, 200], [1800, 200], [1800, 600], [1200, 600]]
  }'
```

### 3. View Entry/Exit Logs

```bash
curl "http://localhost:8000/api/v1/analytics/entry-exit/edge_001?limit=50"
```

## Finding Zone Coordinates

**Method 1: Use Dashboard**
1. Open `http://localhost:8000/dashboard/index.html`
2. View video stream
3. Note pixel coordinates where you want zones

**Method 2: Use Browser DevTools**
1. Right-click video → Inspect Element
2. Use element inspector to find coordinates

**Method 3: Test Script**
```python
import cv2

cap = cv2.VideoCapture(0)
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"[{x}, {y}]")

cv2.namedWindow('Frame')
cv2.setMouseCallback('Frame', mouse_callback)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow('Frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

## Coordinate System

- Origin (0, 0) = **Top-left** corner
- X increases → **Right**
- Y increases → **Down**
- Units = **Pixels**

## Zone Types

- `"entry"` - Tracks when objects **enter** the zone
- `"exit"` - Tracks when objects **exit** the zone
- `"monitor"` - General monitoring (no entry/exit tracking)

## Example: Rectangle Zone

For a rectangle from (100, 100) to (500, 400):
```json
"polygon_coords": [
  [100, 100],  // Top-left
  [500, 100],  // Top-right
  [500, 400],  // Bottom-right
  [100, 400]   // Bottom-left
]
```

## Viewing Results

### API Response
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

### Dashboard
Entry/exit counts automatically appear in the dashboard for zones with `zone_type` of "entry" or "exit".

## Troubleshooting

**No events logged?**
- Check zone `zone_type` is "entry" or "exit"
- Verify coordinates are within frame bounds
- Ensure camera is streaming and detecting people

**False positives?**
- Reduce zone size
- Adjust zone position

**Missing events?**
- Increase zone size slightly
- Check detection confidence

## Full Documentation

See `ENTRY_EXIT_SETUP.md` for complete documentation.

