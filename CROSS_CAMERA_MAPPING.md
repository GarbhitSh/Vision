# Cross-Camera Entry/Exit Mapping

## Overview

The VISION system can track people as they move between different edge nodes (cameras). When a person enters one edge node and exits another, the system uses Re-ID (Re-identification) features to match them across cameras.

## How It Works

### 1. **Entry/Exit Detection**
- Each edge node detects when people enter or exit designated zones
- Entry/exit events are logged in the `entry_exit_logs` table

### 2. **Re-ID Feature Extraction**
- When a person is detected, their appearance features are extracted using:
  - ResNet50-based appearance features
  - Color histogram features
  - Combined into a 512-dimensional feature vector
- These features are stored in the `tracks` table

### 3. **Cross-Camera Matching**
- When an **entry** event occurs at one edge node:
  - The system searches for **exit** events from other cameras within a time window (default: 10 minutes)
  - Compares Re-ID features using cosine similarity
  - If similarity ≥ 0.7, creates a cross-camera movement record

- When an **exit** event occurs at one edge node:
  - The system searches for **entry** events from other cameras within a time window
  - Matches using Re-ID features
  - Creates a cross-camera movement record if match found

### 4. **Movement Records**
- Stored in `cross_camera_movements` table with:
  - Entry camera ID and zone
  - Exit camera ID and zone
  - Entry/exit timestamps
  - Re-ID similarity score (0-1)
  - Match confidence (high/medium/low)
  - Duration between entry and exit

## API Endpoints

### Get Cross-Camera Movements
```http
GET /api/v1/movements
```

**Query Parameters:**
- `entry_camera_id` (optional): Filter by entry camera
- `exit_camera_id` (optional): Filter by exit camera
- `start_time` (optional): Filter by start time (ISO format)
- `end_time` (optional): Filter by end time (ISO format)
- `limit` (default: 100): Maximum results

**Example:**
```bash
curl "http://localhost:8000/api/v1/movements?entry_camera_id=edge_001&limit=50"
```

### Get Movements for a Specific Camera
```http
GET /api/v1/movements/camera/{camera_id}
```

**Query Parameters:**
- `direction`: "entry" (where people entered), "exit" (where people exited), or "both"
- `hours` (default: 24): Hours to look back
- `limit` (default: 100): Maximum results

**Example:**
```bash
# Get all movements where people entered edge_001
curl "http://localhost:8000/api/v1/movements/camera/edge_001?direction=entry&hours=24"

# Get all movements where people exited edge_002
curl "http://localhost:8000/api/v1/movements/camera/edge_002?direction=exit&hours=12"
```

### Get Movements Between Two Cameras
```http
GET /api/v1/movements/pair/{camera1_id}/{camera2_id}
```

**Query Parameters:**
- `hours` (default: 24): Hours to look back
- `limit` (default: 100): Maximum results

**Example:**
```bash
# Get movements between edge_001 and edge_002
curl "http://localhost:8000/api/v1/movements/pair/edge_001/edge_002?hours=24"
```

### Get Movement Statistics
```http
GET /api/v1/movements/statistics
```

**Query Parameters:**
- `start_time` (optional): Filter by start time
- `end_time` (optional): Filter by end time

**Example:**
```bash
curl "http://localhost:8000/api/v1/movements/statistics"
```

**Response:**
```json
{
  "total_movements": 150,
  "unique_camera_pairs": 5,
  "avg_duration_seconds": 45.2,
  "avg_similarity": 0.82,
  "high_confidence_count": 120,
  "medium_confidence_count": 25,
  "low_confidence_count": 5
}
```

## Configuration

### Similarity Threshold
- Default: **0.7** (70% similarity required for matching)
- Can be adjusted in `services/cross_camera_matching.py`:
  ```python
  self.similarity_threshold = 0.7
  ```

### Time Window
- Default: **10 minutes** (max time between entry and exit)
- Can be adjusted in `services/cross_camera_matching.py`:
  ```python
  self.max_time_window = timedelta(minutes=10)
  ```

### Confidence Levels
- **High**: Similarity ≥ 0.85
- **Medium**: Similarity ≥ 0.75
- **Low**: Similarity ≥ 0.70

## Database Schema

### `cross_camera_movements` Table
```sql
CREATE TABLE cross_camera_movements (
    id INTEGER PRIMARY KEY,
    entry_camera_id VARCHAR NOT NULL,
    entry_zone_id INTEGER,
    entry_track_id INTEGER NOT NULL,
    entry_timestamp DATETIME NOT NULL,
    exit_camera_id VARCHAR NOT NULL,
    exit_zone_id INTEGER,
    exit_track_id INTEGER NOT NULL,
    exit_timestamp DATETIME NOT NULL,
    similarity_score FLOAT,
    match_confidence VARCHAR,  -- high/medium/low
    duration_seconds FLOAT,
    created_at DATETIME
);
```

## Usage Examples

### Example 1: Find where people entered edge_001 and exited
```python
import requests

# Get movements where people entered edge_001
response = requests.get(
    "http://localhost:8000/api/v1/movements",
    params={
        "entry_camera_id": "edge_001",
        "limit": 100
    }
)

movements = response.json()
for movement in movements:
    print(f"Person entered {movement['entry_camera_id']} "
          f"and exited {movement['exit_camera_id']} "
          f"after {movement['duration_seconds']:.1f} seconds "
          f"(similarity: {movement['similarity_score']:.2f})")
```

### Example 2: Get movement statistics
```python
import requests

response = requests.get("http://localhost:8000/api/v1/movements/statistics")
stats = response.json()

print(f"Total movements: {stats['total_movements']}")
print(f"Unique camera pairs: {stats['unique_camera_pairs']}")
print(f"Average duration: {stats['avg_duration_seconds']:.1f} seconds")
print(f"Average similarity: {stats['avg_similarity']:.2f}")
```

### Example 3: Track movement between two specific cameras
```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/movements/pair/edge_001/edge_002",
    params={"hours": 24}
)

movements = response.json()
print(f"Found {len(movements)} movements between edge_001 and edge_002")
```

## Dashboard Integration

You can display cross-camera movements in your dashboard:

```javascript
// Fetch cross-camera movements
async function fetchCrossCameraMovements(entryCameraId) {
    const response = await fetch(
        `http://localhost:8000/api/v1/movements?entry_camera_id=${entryCameraId}&limit=50`
    );
    const movements = await response.json();
    
    // Display in table
    movements.forEach(movement => {
        console.log(
            `Entry: ${movement.entry_camera_id} -> Exit: ${movement.exit_camera_id} ` +
            `(${movement.duration_seconds}s, similarity: ${movement.similarity_score})`
        );
    });
}
```

## Notes

1. **Re-ID Accuracy**: Matching accuracy depends on:
   - Lighting conditions
   - Camera angles
   - Person's appearance (clothing, etc.)
   - Time between entry and exit

2. **False Positives**: Lower similarity scores may indicate false matches. Use `match_confidence` to filter results.

3. **Performance**: Cross-camera matching runs automatically when entry/exit events are detected. For large deployments, consider:
   - Adjusting time windows
   - Filtering by camera pairs
   - Using background tasks for matching

4. **Zone Configuration**: Make sure entry/exit zones are properly configured for each camera to enable accurate tracking.

