# SkyGuard V2 - Complete API Documentation

## Base URL
```
http://localhost:8000
```

## WebSocket Connection
```
ws://localhost:8000/socket.io/
```

---

## 🏥 Health & Metrics

### GET /health
Get complete system health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime_seconds": 3600.5,
  "components": {
    "database": "connected",
    "yolo": {
      "status": "loaded",
      "device": "cpu",
      "fps": 8.5,
      "last_inference_ms": 120.3
    },
    "cameras": {
      "total": 8,
      "connected": 8
    },
    "drones": {
      "total": 4,
      "statuses": {
        "IDLE": 2,
        "EN_ROUTE": 1,
        "HOVERING": 1
      }
    },
    "baseline": "loaded"
  }
}
```

### GET /metrics
Get system performance metrics.

**Response:**
```json
{
  "cpu_percent": 45.2,
  "memory_percent": 62.8,
  "memory_used_mb": 2048.5,
  "per_camera_fps": {
    "CAM-01": 9.8,
    "CAM-02": 10.1,
    "CAM-03": 9.5
  },
  "detector_fps": 8.5,
  "queue_depth": 2
}
```

---

## 📷 Cameras

### GET /cameras
List all camera statuses.

**Response:**
```json
{
  "cameras": [
    {
      "cam_id": "CAM-01",
      "zone_id": "Zone-A",
      "type": "rtsp",
      "status": "connected",
      "fps": 9.8,
      "resolution": "640x360"
    }
  ]
}
```

### GET /cameras/{cam_id}/stream
Get MJPEG video stream with detection overlay.

**Response:** `multipart/x-mixed-replace` MJPEG stream

**Example:**
```html
<img src="http://localhost:8000/cameras/CAM-01/stream" />
```

### GET /cameras/{cam_id}/snapshot
Get latest JPEG snapshot.

**Response:** `image/jpeg`

### GET /cameras/{cam_id}/detections
Get latest detection result for camera.

**Response:**
```json
{
  "cam_id": "CAM-01",
  "zone_id": "Zone-A",
  "persons_count": 12,
  "detections": [
    {
      "bbox": [100, 150, 180, 320],
      "confidence": 0.92,
      "class": "person",
      "track_id": 5
    }
  ],
  "anomaly_flags": [
    {
      "type": "crowd_anomaly",
      "confidence": 0.85,
      "description": "12 persons detected"
    }
  ],
  "processing_ms": 120.5
}
```

---

## 🗺️ Zones

### GET /zones
List all zones with current stats.

**Response:**
```json
{
  "zones": [
    {
      "zone_id": "Zone-A",
      "name": "MG Road",
      "cam_id": "CAM-01",
      "polygon": [[18.5204, 73.8567], [18.5206, 73.8567]],
      "centroid_lat": 18.5204,
      "centroid_lon": 73.8567,
      "baseline_mean": 8.5,
      "baseline_std": 2.3,
      "current_stats": {
        "zone_id": "Zone-A",
        "current": 12,
        "mean": 8.5,
        "std_dev": 2.3,
        "anomaly_score": 0.85,
        "severity": 0.85
      }
    }
  ]
}
```

### GET /zones/{zone_id}/baseline
Get hourly baseline profile for zone.

**Response:**
```json
{
  "zone_id": "Zone-A",
  "baselines": [
    {
      "hour": 0,
      "day_of_week": 0,
      "mean": 2.5,
      "std_dev": 1.5,
      "sample_count": 150
    }
  ]
}
```

---

## 🚨 Alerts

### GET /alerts
List alerts with filtering.

**Query Parameters:**
- `status` (optional): Filter by status (ACTIVE, RESOLVED, CANCELLED)
- `zone_id` (optional): Filter by zone
- `limit` (default: 50): Max results
- `offset` (default: 0): Pagination offset

**Response:**
```json
{
  "alerts": [
    {
      "alert_id": "AL-20260405-143022-001",
      "zone_id": "Zone-A",
      "zone_name": "MG Road",
      "cam_id": "CAM-01",
      "anomaly_type": "crowd_anomaly",
      "severity": 0.85,
      "current_count": 12,
      "baseline_mean": 8.5,
      "z_score": 1.52,
      "location": {"lat": 18.5204, "lon": 73.8567},
      "primary_drone": "DR-01",
      "secondary_drone": "DR-02",
      "primary_eta": 45.2,
      "secondary_eta": 52.8,
      "status": "ACTIVE",
      "source": "camera",
      "timestamp": "2026-04-05T14:30:22.123456Z"
    }
  ],
  "count": 1
}
```

### POST /alerts/manual
Create manual alert for testing.

**Request Body:**
```json
{
  "zone_id": "Zone-A",
  "anomaly_type": "crowd_anomaly",
  "severity": 0.85
}
```

**Response:**
```json
{
  "alert_id": "AL-20260405-143022-001",
  "zone_id": "Zone-A",
  "zone_name": "MG Road",
  "severity": 0.85,
  "primary_drone": "DR-01",
  "secondary_drone": "DR-02",
  "primary_eta": 45.2,
  "secondary_eta": 52.8,
  "status": "ACTIVE",
  "timestamp": "2026-04-05T14:30:22.123456Z"
}
```

### GET /alerts/{alert_id}
Get single alert details.

**Response:** Same as alert object above.

### PATCH /alerts/{alert_id}/resolve
Resolve an alert.

**Response:**
```json
{
  "alert_id": "AL-20260405-143022-001",
  "status": "RESOLVED",
  "resolved_at": "2026-04-05T14:35:22.123456Z"
}
```

---

## 🚁 Drones

### GET /drones
List all drone states.

**Response:**
```json
{
  "drones": [
    {
      "drone_id": "DR-01",
      "position": {"lat": 18.5204, "lon": 73.8567, "alt": 50.0},
      "home_base": {"lat": 18.5204, "lon": 73.8567},
      "battery": 85,
      "status": "EN_ROUTE",
      "target_zone": "Zone-B",
      "target_location": {"lat": 18.5308, "lon": 73.8474},
      "eta_seconds": 45.2,
      "speed_ms": 15.0,
      "distance_remaining_m": 678.5,
      "mission_id": "MSN-DR-01-20260405143022",
      "assigned_alert_id": "AL-20260405-143022-001",
      "can_be_reassigned": true
    }
  ]
}
```

### GET /drones/{drone_id}
Get single drone state.

**Response:** Same as drone object above.

### POST /drones/{drone_id}/dispatch
Manual dispatch drone to location.

**Request Body:**
```json
{
  "lat": 18.5308,
  "lon": 73.8474,
  "zone_id": "Zone-B"
}
```

**Response:**
```json
{
  "status": "dispatched",
  "drone_id": "DR-01",
  "route": {
    "waypoints": [
      {"lat": 18.5204, "lon": 73.8567},
      {"lat": 18.5256, "lon": 73.8521},
      {"lat": 18.5308, "lon": 73.8474}
    ],
    "total_distance_m": 678.5,
    "estimated_time_s": 45.2,
    "no_fly_zones_avoided": [],
    "computation_ms": 12.3
  }
}
```

### POST /drones/{drone_id}/rtl
Return drone to launch (home base).

**Response:**
```json
{
  "status": "returning",
  "drone_id": "DR-01"
}
```

### POST /drones/{drone_id}/reroute
Reroute drone to new target.

**Request Body:**
```json
{
  "lat": 18.5362,
  "lon": 73.8939,
  "alert_id": "AL-20260405-143500-002"
}
```

**Response:**
```json
{
  "status": "rerouted",
  "drone_id": "DR-01",
  "route": {
    "waypoints": [...],
    "total_distance_m": 523.8,
    "estimated_time_s": 34.9
  }
}
```

### GET /drones/{drone_id}/history
Get past missions for drone.

**Response:**
```json
{
  "drone_id": "DR-01",
  "missions": [
    {
      "mission_id": "MSN-DR-01-20260405143022",
      "alert_id": "AL-20260405-143022-001",
      "role": "primary",
      "total_distance_m": 678.5,
      "planned_eta_s": 45.2,
      "actual_duration_s": 48.5,
      "status": "COMPLETED",
      "created_at": "2026-04-05T14:30:22Z",
      "completed_at": "2026-04-05T14:31:10Z"
    }
  ]
}
```

---

## 🛣️ Routes

### POST /routes/plan
Compute CLSP route between two points.

**Request Body:**
```json
{
  "src_lat": 18.5204,
  "src_lon": 73.8567,
  "dst_lat": 18.5308,
  "dst_lon": 73.8474
}
```

**Response:**
```json
{
  "waypoints": [
    {"lat": 18.5204, "lon": 73.8567},
    {"lat": 18.5256, "lon": 73.8521},
    {"lat": 18.5308, "lon": 73.8474}
  ],
  "total_distance_m": 678.5,
  "estimated_time_s": 45.2,
  "no_fly_zones_avoided": ["NFZ-01"],
  "cluster_path": [0, 1, 2],
  "computation_ms": 12.3
}
```

### GET /routes/no_fly_zones
Get active no-fly zones.

**Response:**
```json
{
  "no_fly_zones": [
    {
      "nfz_id": "NFZ-01",
      "name": "Pune Airport",
      "center": {"lat": 18.5822, "lon": 73.9197},
      "radius_m": 2000,
      "polygon": [[18.5822, 73.9197], ...]
    },
    {
      "nfz_id": "NFZ-02",
      "name": "Military Cantonment",
      "center": {"lat": 18.5200, "lon": 73.8700},
      "radius_m": 1500,
      "polygon": [[18.5200, 73.8700], ...]
    }
  ]
}
```

---

## 📱 SOS

### POST /sos
Create SOS event with 30-second cancellation buffer.

**Request Body:**
```json
{
  "sender_id": "user_12345",
  "message": "Emergency at FC Road",
  "lat": 18.5286,
  "lon": 73.8395,
  "location_type": "gps",
  "zone_id": "Zone-C"
}
```

**Response:**
```json
{
  "sos_id": "SOS-20260405-143500-001",
  "status": "PENDING",
  "confirmation_deadline": "2026-04-05T14:35:30.000000Z",
  "buffer_seconds": 30,
  "message": "SOS received. Cancel within 30 seconds to abort dispatch."
}
```

### POST /sos/{sos_id}/cancel
Cancel SOS within buffer window.

**Request Body:**
```json
{
  "reason": "False alarm"
}
```

**Response:**
```json
{
  "sos_id": "SOS-20260405-143500-001",
  "status": "CANCELLED",
  "reason": "False alarm"
}
```

**Error Response (409 if too late):**
```json
{
  "detail": "SOS already dispatched or not found"
}
```

### GET /sos
List SOS events.

**Query Parameters:**
- `status` (optional): Filter by status (PENDING, CONFIRMED, CANCELLED, DISPATCHED)
- `limit` (default: 50): Max results

**Response:**
```json
{
  "sos_events": [
    {
      "sos_id": "SOS-20260405-143500-001",
      "sender_id": "user_12345",
      "message": "Emergency at FC Road",
      "location": {"lat": 18.5286, "lon": 73.8395},
      "location_type": "gps",
      "zone_id": "Zone-C",
      "status": "DISPATCHED",
      "alert_id": "AL-20260405-143530-002",
      "created_at": "2026-04-05T14:35:00Z"
    }
  ],
  "count": 1
}
```

### GET /sos/{sos_id}
Get single SOS event details.

**Response:** Same as SOS object above.

---

## 🔥 Heatmap

### GET /heatmap
Get current KDE heatmap with hotspots.

**Response:**
```json
{
  "points": [
    {"lat": 18.5204, "lon": 73.8567, "intensity": 0.85},
    {"lat": 18.5206, "lon": 73.8569, "intensity": 0.72}
  ],
  "hotspots": [
    {
      "zone_id": "Zone-A",
      "zone_name": "MG Road",
      "lat": 18.5204,
      "lon": 73.8567,
      "intensity": 0.85,
      "incident_count": 15
    }
  ],
  "predictions": [],
  "computed_at": "2026-04-05T14:35:00.000000Z",
  "total_incidents": 42
}
```

### GET /heatmap/predict
Get Gemini AI risk predictions for next 2 hours.

**Query Parameters:**
- `hour` (optional): Hour to predict for (0-23, default: current hour)

**Response:**
```json
{
  "hour": 14,
  "predictions": [
    {
      "zone_id": "Zone-A",
      "risk_score": 0.78,
      "reasoning": "High historical incident rate during afternoon hours",
      "recommended_action": "Increase monitoring"
    }
  ]
}
```

### GET /heatmap/history
Get historical incident counts.

**Query Parameters:**
- `zone_id` (optional): Filter by zone
- `days` (default: 7): Number of days to look back

**Response:**
```json
{
  "history": [
    {"date": "2026-04-05", "count": 8},
    {"date": "2026-04-04", "count": 12},
    {"date": "2026-04-03", "count": 6}
  ]
}
```

---

## 📊 Baseline

### GET /baseline/stats
Get current anomaly scores for all zones.

**Response:**
```json
{
  "zones": [
    {
      "zone_id": "Zone-A",
      "current": 12,
      "mean": 8.5,
      "std_dev": 2.3,
      "anomaly_score": 0.85,
      "severity": 0.85
    }
  ]
}
```

---

## 🎮 QGC (H12 Controller)

### GET /qgc/fleet_status
Get compact fleet summary for H12 overlay.

**Response:**
```json
{
  "drones": [
    {
      "id": "DR-01",
      "status": "EN_ROUTE",
      "battery": 85,
      "eta": 45,
      "lat": 18.5204,
      "lon": 73.8567,
      "alert": "AL-20260405-143022-001"
    }
  ]
}
```

### POST /qgc/dispatch
Dispatch from H12 controller.

**Request Body:**
```json
{
  "alert_id": "AL-20260405-143022-001",
  "drone_ids": ["DR-01", "DR-02"]
}
```

### POST /qgc/reroute/{drone_id}
Reroute from H12.

**Query Parameters:**
- `lat`: Target latitude
- `lon`: Target longitude

### POST /qgc/rtl/{drone_id}
Return to launch from H12.

### POST /qgc/emergency_land/{drone_id}
Emergency land (immediate hover + RTL).

### GET /qgc/overlay
Serve QGC overlay HTML page.

---

## 🔌 WebSocket Events

### Client → Server Events

#### subscribe_camera
Subscribe to per-camera detection stream.

```javascript
socket.emit('subscribe_camera', { cam_id: 'CAM-01' });
```

### Server → Client Events

#### drone_update (every 500ms)
Real-time drone position updates.

```json
{
  "data": {
    "drones": [...]
  }
}
```

#### alert_created
New alert created.

```json
{
  "data": {
    "alert_id": "AL-20260405-143022-001",
    "zone_id": "Zone-A",
    "severity": 0.85,
    ...
  }
}
```

#### alert_updated
Alert status changed.

```json
{
  "data": {
    "alert_id": "AL-20260405-143022-001",
    "status": "RESOLVED",
    ...
  }
}
```

#### baseline_update (every 5s)
Baseline statistics for all zones.

```json
{
  "data": {
    "zones": [...]
  }
}
```

#### heatmap_update (every 30s)
Updated heatmap data.

```json
{
  "data": {
    "points": [...],
    "hotspots": [...],
    ...
  }
}
```

#### sos_received
New SOS event created.

```json
{
  "data": {
    "sos_id": "SOS-20260405-143500-001",
    "status": "PENDING",
    ...
  }
}
```

#### sos_countdown (every 1s during buffer)
SOS countdown timer.

```json
{
  "data": {
    "sos_id": "SOS-20260405-143500-001",
    "seconds_remaining": 25
  }
}
```

#### sos_dispatched
SOS auto-dispatched after buffer.

```json
{
  "data": {
    "sos": {...},
    "alert": {...}
  }
}
```

#### sos_cancelled
SOS cancelled by user.

```json
{
  "data": {
    "sos_id": "SOS-20260405-143500-001",
    "status": "CANCELLED"
  }
}
```

#### drone_reallocated
Drone reassigned mid-flight.

```json
{
  "data": {
    "drone_id": "DR-01",
    "from_alert_id": "AL-20260405-143022-001",
    "to_alert_id": "AL-20260405-143500-002",
    "reason": "Severity diff: 0.25",
    "old_eta": 45.2,
    "new_eta": 34.9
  }
}
```

#### camera_offline
Camera disconnected.

```json
{
  "data": {
    "cam_id": "CAM-01"
  }
}
```

#### camera_online
Camera reconnected.

```json
{
  "data": {
    "cam_id": "CAM-01"
  }
}
```

#### detection_stream (per-camera room)
Real-time detection results (only for subscribed cameras).

```json
{
  "data": {
    "cam_id": "CAM-01",
    "zone_id": "Zone-A",
    "persons_count": 12,
    "detections": [...],
    "anomaly_flags": [...]
  }
}
```

#### system_error
System error notification.

```json
{
  "data": {
    "message": "Detection error: ..."
  }
}
```

---

## 🧪 Testing Workflow

### 1. Start System
```bash
cd skyguard-v2
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Check Health
```bash
curl http://localhost:8000/health
```

### 3. View Camera Stream
Open browser: `http://localhost:8000/cameras/CAM-01/stream`

### 4. Create Manual Alert
```bash
curl -X POST http://localhost:8000/alerts/manual \
  -H "Content-Type: application/json" \
  -d '{"zone_id": "Zone-A", "anomaly_type": "crowd_anomaly", "severity": 0.85}'
```

### 5. Monitor Drones
```bash
curl http://localhost:8000/drones
```

### 6. Create SOS
```bash
curl -X POST http://localhost:8000/sos \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "test_user",
    "message": "Test emergency",
    "lat": 18.5286,
    "lon": 73.8395,
    "location_type": "gps"
  }'
```

### 7. Cancel SOS (within 30s)
```bash
curl -X POST http://localhost:8000/sos/SOS-20260405-143500-001/cancel \
  -H "Content-Type: application/json" \
  -d '{"reason": "Test cancelled"}'
```

### 8. WebSocket Connection (JavaScript)
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:8000');

socket.on('connect', () => {
  console.log('Connected to SkyGuard V2');
  
  // Subscribe to camera
  socket.emit('subscribe_camera', { cam_id: 'CAM-01' });
});

socket.on('drone_update', (data) => {
  console.log('Drones:', data.data.drones);
});

socket.on('alert_created', (data) => {
  console.log('New alert:', data.data);
});

socket.on('detection_stream', (data) => {
  console.log('Detection:', data.data);
});
```

---

## 🐛 Common Issues & Solutions

### Issue: Cameras not connecting
**Solution:** Check RTSP URL in `.env` file. Video feeds will auto-generate if missing.

### Issue: YOLO model not loading
**Solution:** Model auto-downloads on first run. Ensure internet connection.

### Issue: Drones not dispatching
**Solution:** Check airspace graph is built (`data/airspace/pune_graph.json`). Rebuilds automatically if missing.

### Issue: WebSocket not connecting
**Solution:** Ensure CORS is enabled. Check browser console for errors.

### Issue: Database locked
**Solution:** SQLite WAL mode is enabled. Restart server if persistent.

---

## 📝 Notes

- All timestamps are in UTC ISO 8601 format
- All distances are in meters
- All speeds are in meters/second
- Battery levels are 0-100 integer percentages
- Severity scores are 0.0-1.0 floats
- Alert IDs format: `AL-YYYYMMDD-HHMMSS-NNN`
- SOS IDs format: `SOS-YYYYMMDD-HHMMSS-NNN`
- Mission IDs format: `MSN-{drone_id}-YYYYMMDDHHMMSS`
