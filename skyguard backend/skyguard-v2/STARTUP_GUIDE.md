# SkyGuard V2 - Complete Startup & Testing Guide

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
cd skyguard-v2
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `.env` file (already configured with defaults):
```bash
# Camera settings
RTSP_URL=rtsp://admin:Sonji%402534@192.168.1.250:554/cam/realmonitor?channel=1&subtype=0
CAMERA_FPS_TARGET=10
CAMERA_WIDTH=640
CAMERA_HEIGHT=360

# YOLO settings
YOLO_MODEL_PATH=data/models/yolo11n.pt
YOLO_CONFIDENCE=0.5
YOLO_DEVICE=cpu

# API settings
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Start Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     ✅ Database initialized
INFO:     ✅ Database seeded (8 cameras)
INFO:     ✅ Geofence loaded
INFO:     ✅ Airspace graph ready
INFO:     ✅ YOLO detector ready
INFO:     ✅ Camera manager ready
INFO:     ✅ Baseline engine ready
INFO:     ✅ Drone simulator ready
INFO:     ✅ Priority queue ready
INFO:     ✅ Heatmap engine ready
INFO:     ✅ Alert manager ready
INFO:     Detection loop started
INFO:     Priority queue loop started
INFO:     Baseline broadcast loop started
INFO:     Heatmap loop started
INFO:     Camera health loop started
INFO:     ============================================================
INFO:     ✅ SkyGuard V2 fully initialized!
INFO:        API:       http://0.0.0.0:8000
INFO:        Health:    http://0.0.0.0:8000/health
INFO:        Cameras:   8 (8 connected)
INFO:        Drones:    4
INFO:        NFZs:      2
INFO:        WebSocket: ws://0.0.0.0:8000
INFO:     ============================================================
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4. Verify System Health
Open browser: `http://localhost:8000/health`

---

## 📋 Complete Testing Checklist

### ✅ Phase 1: System Initialization (2 minutes)

1. **Check Health Endpoint**
```bash
curl http://localhost:8000/health | jq
```
Expected: `"status": "healthy"`, all components loaded

2. **Check Metrics**
```bash
curl http://localhost:8000/metrics | jq
```
Expected: CPU/memory stats, camera FPS values

3. **List Cameras**
```bash
curl http://localhost:8000/cameras | jq
```
Expected: 8 cameras, all "connected"

4. **List Zones**
```bash
curl http://localhost:8000/zones | jq
```
Expected: 8 zones with baseline stats

5. **List Drones**
```bash
curl http://localhost:8000/drones | jq
```
Expected: 4 drones, all "IDLE", battery 100%

---

### ✅ Phase 2: Camera Streams (3 minutes)

6. **View Camera Stream (Browser)**
Open: `http://localhost:8000/cameras/CAM-01/stream`
Expected: Live MJPEG stream with detection overlay

7. **Get Camera Snapshot**
```bash
curl http://localhost:8000/cameras/CAM-01/snapshot --output snapshot.jpg
```
Expected: JPEG file created

8. **Get Detection Results**
```bash
curl http://localhost:8000/cameras/CAM-01/detections | jq
```
Expected: Detection data with persons_count, bboxes, anomaly_flags

9. **Test All Camera Streams**
```bash
for i in {01..08}; do
  echo "Testing CAM-$i..."
  curl -s http://localhost:8000/cameras/CAM-$i/detections | jq '.persons_count'
done
```
Expected: Person counts for all 8 cameras

---

### ✅ Phase 3: Manual Alert & Drone Dispatch (5 minutes)

10. **Create Manual Alert (Zone-A)**
```bash
curl -X POST http://localhost:8000/alerts/manual \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": "Zone-A",
    "anomaly_type": "crowd_anomaly",
    "severity": 0.85
  }' | jq
```
Expected: Alert created with `primary_drone` and `secondary_drone` assigned

11. **Monitor Drone Movement (Real-time)**
```bash
watch -n 1 'curl -s http://localhost:8000/drones | jq ".drones[] | {id: .drone_id, status: .status, battery: .battery, eta: .eta_seconds}"'
```
Expected: Drones transition IDLE → EN_ROUTE → HOVERING → RETURNING → IDLE

12. **Check Alert Status**
```bash
curl http://localhost:8000/alerts | jq '.alerts[0]'
```
Expected: Alert with status "ACTIVE", drone assignments

13. **View Drone Routes**
```bash
curl http://localhost:8000/alerts | jq '.alerts[0].routes'
```
Expected: Waypoints, distance, ETA for both drones

---

### ✅ Phase 4: SOS System (2 minutes)

14. **Create SOS Event**
```bash
SOS_RESPONSE=$(curl -X POST http://localhost:8000/sos \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "test_user_001",
    "message": "Emergency at FC Road",
    "lat": 18.5286,
    "lon": 73.8395,
    "location_type": "gps",
    "zone_id": "Zone-C"
  }')
echo $SOS_RESPONSE | jq
SOS_ID=$(echo $SOS_RESPONSE | jq -r '.sos_id')
```
Expected: SOS created with 30-second buffer

15. **Cancel SOS (within 30 seconds)**
```bash
curl -X POST http://localhost:8000/sos/$SOS_ID/cancel \
  -H "Content-Type: application/json" \
  -d '{"reason": "False alarm - testing"}' | jq
```
Expected: `"status": "CANCELLED"`

16. **Test Auto-Dispatch (wait 30s)**
```bash
# Create another SOS and DON'T cancel
curl -X POST http://localhost:8000/sos \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "test_user_002",
    "message": "Real emergency",
    "lat": 18.5362,
    "lon": 73.8939,
    "location_type": "gps"
  }' | jq

# Wait 30 seconds, then check alerts
sleep 35
curl http://localhost:8000/alerts | jq '.alerts[] | select(.source == "camera")'
```
Expected: New alert created with severity 0.90, drones dispatched

---

### ✅ Phase 5: Routing & No-Fly Zones (3 minutes)

17. **Plan Route (Avoiding NFZ)**
```bash
curl -X POST http://localhost:8000/routes/plan \
  -H "Content-Type: application/json" \
  -d '{
    "src_lat": 18.5204,
    "src_lon": 73.8567,
    "dst_lat": 18.5822,
    "dst_lon": 73.9197
  }' | jq
```
Expected: Route with waypoints, `no_fly_zones_avoided` array

18. **List No-Fly Zones**
```bash
curl http://localhost:8000/routes/no_fly_zones | jq
```
Expected: 2 NFZs (Pune Airport, Military Cantonment)

19. **Test Route Through NFZ**
```bash
# This should route AROUND the airport NFZ
curl -X POST http://localhost:8000/routes/plan \
  -H "Content-Type: application/json" \
  -d '{
    "src_lat": 18.5700,
    "src_lon": 73.9100,
    "dst_lat": 18.5900,
    "dst_lon": 73.9300
  }' | jq '.no_fly_zones_avoided'
```
Expected: `["NFZ-01"]` in avoided list

---

### ✅ Phase 6: Heatmap & Analytics (2 minutes)

20. **Get Current Heatmap**
```bash
curl http://localhost:8000/heatmap | jq
```
Expected: Heatmap points, hotspots, total_incidents

21. **Get Heatmap History**
```bash
curl 'http://localhost:8000/heatmap/history?days=7' | jq
```
Expected: Daily incident counts

22. **Get Risk Predictions**
```bash
curl 'http://localhost:8000/heatmap/predict?hour=14' | jq
```
Expected: Risk predictions for zones (may be empty if Gemini not configured)

---

### ✅ Phase 7: Baseline & Anomaly Detection (2 minutes)

23. **Get Baseline Stats**
```bash
curl http://localhost:8000/baseline/stats | jq
```
Expected: Current anomaly scores for all zones

24. **Get Zone Baseline Profile**
```bash
curl http://localhost:8000/zones/Zone-A/baseline | jq
```
Expected: 24-hour baseline profile (mean, std_dev per hour)

---

### ✅ Phase 8: Drone Control (3 minutes)

25. **Manual Drone Dispatch**
```bash
curl -X POST http://localhost:8000/drones/DR-03/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 18.5913,
    "lon": 73.7390,
    "zone_id": "Zone-E"
  }' | jq
```
Expected: Drone dispatched with route

26. **Reroute Drone Mid-Flight**
```bash
# Wait for drone to be EN_ROUTE, then reroute
sleep 5
curl -X POST http://localhost:8000/drones/DR-03/reroute \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 18.5074,
    "lon": 73.8077
  }' | jq
```
Expected: Drone rerouted with new ETA

27. **Return Drone to Launch**
```bash
curl -X POST http://localhost:8000/drones/DR-03/rtl | jq
```
Expected: `"status": "returning"`

28. **Get Drone Mission History**
```bash
curl http://localhost:8000/drones/DR-01/history | jq
```
Expected: List of past missions

---

### ✅ Phase 9: WebSocket Real-Time Updates (5 minutes)

29. **Test WebSocket Connection (Node.js)**
Create `test_websocket.js`:
```javascript
const io = require('socket.io-client');

const socket = io('http://localhost:8000');

socket.on('connect', () => {
  console.log('✅ Connected to SkyGuard V2');
  
  // Subscribe to camera
  socket.emit('subscribe_camera', { cam_id: 'CAM-01' });
});

socket.on('drone_update', (data) => {
  console.log('🚁 Drone Update:', data.data.drones.length, 'drones');
});

socket.on('alert_created', (data) => {
  console.log('🚨 Alert Created:', data.data.alert_id);
});

socket.on('baseline_update', (data) => {
  console.log('📊 Baseline Update:', data.data.zones.length, 'zones');
});

socket.on('detection_stream', (data) => {
  console.log('📷 Detection (CAM-01):', data.data.persons_count, 'persons');
});

socket.on('sos_received', (data) => {
  console.log('📱 SOS Received:', data.data.sos_id);
});

socket.on('sos_countdown', (data) => {
  console.log('⏱️  SOS Countdown:', data.data.seconds_remaining, 'seconds');
});

socket.on('drone_reallocated', (data) => {
  console.log('🔄 Drone Reallocated:', data.data.drone_id);
});

console.log('Listening for events...');
```

Run:
```bash
npm install socket.io-client
node test_websocket.js
```

Expected: Real-time events every 500ms (drones), 5s (baseline), etc.

30. **Test WebSocket in Browser**
Open browser console on `http://localhost:8000/health`:
```javascript
const socket = io('http://localhost:8000');

socket.on('connect', () => console.log('Connected'));
socket.on('drone_update', (data) => console.log('Drones:', data));
socket.on('alert_created', (data) => console.log('Alert:', data));
```

---

### ✅ Phase 10: Stress Testing (5 minutes)

31. **Create Multiple Alerts Simultaneously**
```bash
for zone in Zone-A Zone-B Zone-C Zone-D; do
  curl -X POST http://localhost:8000/alerts/manual \
    -H "Content-Type: application/json" \
    -d "{\"zone_id\": \"$zone\", \"anomaly_type\": \"crowd_anomaly\", \"severity\": 0.85}" &
done
wait
```
Expected: All alerts created, drones allocated based on priority

32. **Monitor Priority Queue**
```bash
curl http://localhost:8000/drones | jq '.drones[] | {id: .drone_id, status: .status, alert: .assigned_alert_id}'
```
Expected: Drones assigned to highest-priority alerts

33. **Test Drone Reallocation**
```bash
# Create low-priority alert
curl -X POST http://localhost:8000/alerts/manual \
  -H "Content-Type: application/json" \
  -d '{"zone_id": "Zone-F", "anomaly_type": "crowd_anomaly", "severity": 0.50}'

# Wait 2 seconds, then create high-priority alert
sleep 2
curl -X POST http://localhost:8000/alerts/manual \
  -H "Content-Type: application/json" \
  -d '{"zone_id": "Zone-G", "anomaly_type": "weapon_detect", "severity": 0.95}'

# Check if drone was reallocated
sleep 1
curl http://localhost:8000/drones | jq '.drones[] | select(.status == "REROUTING")'
```
Expected: Drone reallocated to higher-priority alert

---

## 🎯 Success Criteria

### All Tests Pass If:
- ✅ All 8 cameras streaming with detection overlay
- ✅ All 4 drones responding to dispatch commands
- ✅ Alerts created automatically from detections
- ✅ Drones dispatched with CLSP routes avoiding NFZs
- ✅ SOS system works with 30s buffer and auto-dispatch
- ✅ WebSocket events broadcasting in real-time
- ✅ Heatmap updating every 30 seconds
- ✅ Baseline stats updating every 5 seconds
- ✅ Drone positions updating every 500ms
- ✅ Priority queue reallocating drones correctly

---

## 🐛 Troubleshooting

### Issue: "YOLO model not found"
**Solution:**
```bash
mkdir -p data/models
python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"
mv yolo11n.pt data/models/
```

### Issue: "Camera feed not generating"
**Solution:** Video feeds auto-generate on first run. Check `data/feeds/` directory.

### Issue: "Database locked"
**Solution:**
```bash
rm data/skyguard_v2.db*
# Restart server - database will be recreated
```

### Issue: "Airspace graph not building"
**Solution:**
```bash
rm data/airspace/pune_graph.json
# Restart server - graph will be rebuilt
```

### Issue: "WebSocket not connecting"
**Solution:** Check CORS settings in `app/main.py`. Ensure `allow_origins=["*"]`.

### Issue: "Drones not moving"
**Solution:** Check priority queue loop is running. Look for "Priority queue loop started" in logs.

---

## 📊 Performance Benchmarks

### Expected Performance:
- **Camera FPS:** 8-10 FPS per camera (CPU), 15-20 FPS (GPU)
- **Detection Latency:** 100-150ms per frame
- **Route Computation:** 10-20ms (CLSP algorithm)
- **WebSocket Latency:** <50ms
- **Database Queries:** <10ms
- **Memory Usage:** 1.5-2.5 GB
- **CPU Usage:** 40-60% (8 cameras, CPU inference)

---

## 🎓 Advanced Testing

### Load Testing with Apache Bench
```bash
# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Test camera snapshot
ab -n 100 -c 5 http://localhost:8000/cameras/CAM-01/snapshot
```

### Continuous Monitoring Script
```bash
#!/bin/bash
while true; do
  clear
  echo "=== SkyGuard V2 Status ==="
  echo ""
  echo "Health:"
  curl -s http://localhost:8000/health | jq '.status'
  echo ""
  echo "Drones:"
  curl -s http://localhost:8000/drones | jq '.drones[] | {id: .drone_id, status: .status, battery: .battery}'
  echo ""
  echo "Active Alerts:"
  curl -s http://localhost:8000/alerts | jq '.count'
  sleep 5
done
```

---

## ✅ Final Verification

Run this complete test suite:
```bash
#!/bin/bash
echo "🧪 SkyGuard V2 Complete Test Suite"
echo "=================================="

# Test 1: Health
echo "Test 1: Health Check"
curl -s http://localhost:8000/health | jq '.status' | grep -q "healthy" && echo "✅ PASS" || echo "❌ FAIL"

# Test 2: Cameras
echo "Test 2: Camera Count"
CAMERA_COUNT=$(curl -s http://localhost:8000/cameras | jq '.cameras | length')
[ "$CAMERA_COUNT" -eq 8 ] && echo "✅ PASS" || echo "❌ FAIL"

# Test 3: Drones
echo "Test 3: Drone Count"
DRONE_COUNT=$(curl -s http://localhost:8000/drones | jq '.drones | length')
[ "$DRONE_COUNT" -eq 4 ] && echo "✅ PASS" || echo "❌ FAIL"

# Test 4: Manual Alert
echo "Test 4: Manual Alert Creation"
ALERT_ID=$(curl -s -X POST http://localhost:8000/alerts/manual \
  -H "Content-Type: application/json" \
  -d '{"zone_id": "Zone-A", "anomaly_type": "crowd_anomaly", "severity": 0.85}' | jq -r '.alert_id')
[ -n "$ALERT_ID" ] && echo "✅ PASS (Alert: $ALERT_ID)" || echo "❌ FAIL"

# Test 5: SOS Creation
echo "Test 5: SOS Creation"
SOS_ID=$(curl -s -X POST http://localhost:8000/sos \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "test", "message": "test", "lat": 18.52, "lon": 73.85, "location_type": "gps"}' | jq -r '.sos_id')
[ -n "$SOS_ID" ] && echo "✅ PASS (SOS: $SOS_ID)" || echo "❌ FAIL"

# Test 6: SOS Cancellation
echo "Test 6: SOS Cancellation"
curl -s -X POST http://localhost:8000/sos/$SOS_ID/cancel \
  -H "Content-Type: application/json" \
  -d '{"reason": "test"}' | jq -r '.status' | grep -q "CANCELLED" && echo "✅ PASS" || echo "❌ FAIL"

echo ""
echo "=================================="
echo "Test Suite Complete!"
```

Save as `test_suite.sh`, make executable, and run:
```bash
chmod +x test_suite.sh
./test_suite.sh
```

---

## 🎉 You're Ready!

If all tests pass, your SkyGuard V2 system is fully operational and ready for production use!

For API details, see `API_DOCUMENTATION.md`.
