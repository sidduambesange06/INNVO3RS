# SKYGUARD V2 — COMPLETE BACKEND SPECIFICATION
**Version**: 2.0 | **City**: Pune Smart City | **Role**: Police Drone Office  
**Stack**: FastAPI · Python 3.11 · python-socketio · YOLO11n · OpenCV · SQLite · Shapely · Gemini 1.5 Flash

---

## 1. SYSTEM OVERVIEW

SkyGuard V2 is a real-time AI-powered drone dispatch and surveillance backend for Pune Smart City. It ingests feeds from 8 AI-equipped cameras, detects 5 anomaly types, dispatches drone pairs via a novel clustering-based shortest-path algorithm, enforces no-fly zones, supports SOS from a React Native mobile app, and generates predictive incident heatmaps — all coordinated by Gemini AI for decision-making.

### Architecture Pillars
```
PERCEIVE → ANALYSE → SCORE → ROUTE → DISPATCH → MONITOR → LEARN
   ↑            ↑        ↑       ↑         ↑          ↑        ↑
8 Cameras   5 Models  Baseline Cluster  2 Drones  PQ 500ms  Heatmap
            YOLO+AI   Engine   Router   per Zone  Reallocate SQLite
```

---

## 2. CAMERA INFRASTRUCTURE

### 2.1 Camera Roster (Pune — 8 Cameras)

| ID      | Type         | Source                                    | Coverage Zone   | Location (Lat/Lon)        |
|---------|-------------|-------------------------------------------|-----------------|---------------------------|
| CAM-01  | RTSP Live   | rtsp://admin:admin@192.168.1.64:554/...   | Zone-A: MG Road | 18.5204, 73.8567          |
| CAM-02  | Video Feed  | data/feeds/cam02_shivajinagar.mp4         | Zone-B: Shivajinagar | 18.5308, 73.8474     |
| CAM-03  | Video Feed  | data/feeds/cam03_fc_road.mp4              | Zone-C: FC Road | 18.5286, 73.8395          |
| CAM-04  | Video Feed  | data/feeds/cam04_koregaon.mp4             | Zone-D: Koregaon Park | 18.5362, 73.8939    |
| CAM-05  | Video Feed  | data/feeds/cam05_hinjewadi.mp4            | Zone-E: Hinjewadi IT | 18.5913, 73.7390      |
| CAM-06  | Video Feed  | data/feeds/cam06_kothrud.mp4              | Zone-F: Kothrud | 18.5074, 73.8077          |
| CAM-07  | Video Feed  | data/feeds/cam07_hadapsar.mp4             | Zone-G: Hadapsar | 18.4956, 73.9259         |
| CAM-08  | Video Feed  | data/feeds/cam08_wakad.mp4               | Zone-H: Wakad   | 18.5989, 73.7601          |

### 2.2 Camera Handler Architecture

Each camera runs in its own thread. RTSP uses OpenCV with auto-reconnect. Video files loop infinitely to simulate live feed.

```python
# app/core/camera_manager.py
class CameraManager:
    cameras: Dict[str, CameraFeed]  # cam_id → CameraFeed instance
    
    def get_frame(cam_id: str) -> np.ndarray
    def get_all_statuses() -> List[CameraStatus]
    def restart_camera(cam_id: str) -> bool
```

**RTSP Camera** (CAM-01): OpenCV VideoCapture with 5-retry exponential backoff, 640×360 downscale, 10 FPS target.

**Video Feed Cameras** (CAM-02 to CAM-08): Loop mp4 files via OpenCV, emulate real-time pacing at 10 FPS, apply same YOLO inference pipeline as live camera.

---

## 3. AI DETECTION PIPELINE

### 3.1 Anomaly Detection Models

| Model ID       | Detection Class        | YOLO Classes Used         | Threshold | Severity Weight |
|----------------|------------------------|---------------------------|-----------|----------------|
| crowd_anomaly  | Crowd Gathering        | person (count > baseline)  | 0.5       | 1.0x           |
| fight_detection | Physical Altercation  | person (proximity + motion)| 0.6       | 1.4x           |
| person_down    | Person on Ground       | person (aspect ratio low)  | 0.65      | 1.5x           |
| weapon_detect  | Weapon Visible         | custom YOLO class          | 0.7       | 2.0x           |
| suspicious_behavior | Loitering/Erratic | person (dwell time)       | 0.55      | 1.2x           |

### 3.2 Detection Engine

```python
# app/core/detection.py
class MultiModelDetector:
    model: YOLO  # yolo11n.pt
    
    def detect_all(frame, cam_id) -> DetectionResult:
        """Run all 5 anomaly checks, return unified result"""
        
    def detect_crowd(frame, zone_polygon) -> CrowdResult
    def detect_fight(frame, detections) -> FightResult
    def detect_person_down(frame, detections) -> PersonDownResult
    def detect_weapon(frame, detections) -> WeaponResult
    def detect_suspicious(frame, cam_id, detections) -> SuspiciousResult
```

**Fight Detection**: Uses proximity clustering. If 2+ persons have IoU overlap > 0.3 and velocity vectors oppose → fight flag.

**Person Down**: Bounding box aspect ratio < 0.5 for 3+ consecutive frames → person_down flag.

**Suspicious Behavior**: Track person_id dwell time in zone. If > 120 seconds in restricted area → suspicious flag.

**Weapon Detection**: Separate YOLO class trained on UCF-Crime dataset. Confidence > 0.7 required.

### 3.3 Detection → Alert Pipeline

```
Frame → YOLO Inference → Multi-Model Analysis → Baseline Comparison
    → Severity Score (weighted by model + anomaly score)
    → If severity > 0.4 → Alert Created
    → Alert tagged with: cam_id, zone_id, location, anomaly_type, severity
    → Gemini AI Decision → Drone Dispatch via Priority Queue
```

---

## 4. BASELINE ENGINE

### 4.1 Poisson Anomaly Scoring

For each zone-hour pair, a Poisson distribution models expected crowd density.

```python
# Per zone per hour:
lambda_val = baseline_mean  # Expected crowd count
z_score = (current_count - lambda_val) / sqrt(lambda_val)
anomaly_score = 1 - poisson.cdf(current_count, mu=lambda_val)  # scipy
severity = anomaly_score if current_count > lambda_val else 0.0

# Weighted severity by anomaly type:
final_severity = min(1.0, severity * SEVERITY_WEIGHTS[anomaly_type])
```

### 4.2 Baseline Data

Stored in SQLite `zone_baselines` table with (zone_id, hour, day_of_week, mean, std_dev).

Pre-seeded from `data/baselines/pune_zone_baselines.json` with synthetic historical data for all 8 zones × 24 hours × 7 days.

**Online Learning**: After every 100 detections per zone-hour, update running mean/std in SQLite (Welford's online algorithm).

---

## 5. ROUTING ALGORITHM (Tsinghua-Stanford Inspired)

### 5.1 Algorithm Design

The system uses a **Clustered Layered Shortest Path** (CLSP) algorithm inspired by the Tsinghua/Stanford/Max Planck research. It outperforms Dijkstra by using divide-and-conquer with frontier shrinking instead of full priority queue sorting.

```
Key Insight: Don't sort ALL nodes by distance. 
Instead: Cluster → pick representatives → limited relaxation → expand frontier.
```

### 5.2 Airspace Graph Construction

Pune airspace is divided into a **100×100 meter grid** of waypoints. Each waypoint is a graph node. Edges connect adjacent waypoints with weights = Haversine distance.

```python
# app/core/routing.py

class AirspaceGraph:
    nodes: Dict[NodeID, LatLon]        # ~500 nodes covering Pune
    edges: Dict[NodeID, List[Edge]]    # Adjacency list with haversine weights
    clusters: Dict[ClusterID, List[NodeID]]  # 10×10 km clusters
    cluster_reps: Dict[ClusterID, NodeID]    # One representative per cluster
    no_fly_edges: Set[EdgeID]          # Removed edges from no-fly zones
    
    def build_graph() -> None
    def apply_no_fly_zones(geojson: List[Polygon]) -> None
    def get_nearest_node(lat, lon) -> NodeID
```

### 5.3 CLSP Algorithm Implementation

```python
def clsp_shortest_path(graph: AirspaceGraph, src: LatLon, dst: LatLon) -> Route:
    """
    Clustered Layered Shortest Path
    Steps:
    1. Map src/dst to nearest nodes
    2. Identify cluster layer path (coarse routing)
    3. Apply frontier shrinking within each cluster
    4. Limited relaxation (only relax edges within current frontier + 1 hop)
    5. Reconstruct waypoint path
    6. Smooth path with Bezier curves for drone flight
    """
    
    # Phase 1: Cluster-level routing (coarse)
    src_cluster = get_cluster(src_node)
    dst_cluster = get_cluster(dst_node)
    cluster_path = bfs_cluster_path(src_cluster, dst_cluster)
    
    # Phase 2: Node-level routing within cluster chain (fine)
    frontier = {src_node}
    dist = {src_node: 0}
    prev = {}
    
    for cluster in cluster_path:
        cluster_nodes = graph.clusters[cluster]
        # Limited relaxation: only process nodes in current + adjacent clusters
        new_frontier = set()
        for node in sorted(frontier, key=lambda n: dist.get(n, inf)):
            for neighbor, weight in graph.edges[node]:
                if neighbor in cluster_nodes or neighbor in get_adjacent_cluster_nodes(cluster):
                    new_dist = dist[node] + weight
                    if new_dist < dist.get(neighbor, inf):
                        dist[neighbor] = new_dist
                        prev[neighbor] = node
                        new_frontier.add(neighbor)
        # Frontier shrinking: only keep nodes that improved
        frontier = new_frontier
    
    waypoints = reconstruct_path(prev, src_node, dst_node)
    return Route(waypoints=waypoints, total_distance=dist[dst_node])
```

**No-Fly Zone Enforcement**: Before route computation, remove all edges where midpoint falls inside any no-fly polygon (Shapely `contains()`). If no path exists, find nearest boundary node of no-fly zone and route around its perimeter.

### 5.4 No-Fly Zones (Pune)

```json
[
  {
    "id": "NFZ-01",
    "name": "Pune Airport Restricted Zone",
    "center": {"lat": 18.5822, "lon": 73.9197},
    "polygon": [[18.568, 73.905], [18.595, 73.905], [18.595, 73.935], [18.568, 73.935], [18.568, 73.905]],
    "radius_m": 2000,
    "active": true
  },
  {
    "id": "NFZ-02", 
    "name": "Military Cantonment Area",
    "center": {"lat": 18.5200, "lon": 73.8700},
    "polygon": [[18.510, 73.860], [18.530, 73.860], [18.530, 73.880], [18.510, 73.880], [18.510, 73.860]],
    "radius_m": 1500,
    "active": true
  }
]
```

---

## 6. DRONE FLEET MANAGEMENT

### 6.1 Drone Roster

| ID    | Home Base (Lat/Lon)       | Max Battery | Speed  | Max Range |
|-------|---------------------------|-------------|--------|-----------|
| DR-01 | 18.5204, 73.8567 (Zone-A) | 100%        | 15 m/s | 5 km      |
| DR-02 | 18.5308, 73.8474 (Zone-B) | 100%        | 15 m/s | 5 km      |
| DR-03 | 18.5362, 73.8939 (Zone-D) | 100%        | 15 m/s | 5 km      |
| DR-04 | 18.5913, 73.7390 (Zone-E) | 100%        | 15 m/s | 5 km      |

### 6.2 Drone State Machine

```
IDLE → EN_ROUTE → HOVERING → RETURNING → IDLE
          ↑
     (REROUTING if reassigned mid-flight)
```

**State Transitions**:
- `IDLE → EN_ROUTE`: alert assigned, route computed
- `EN_ROUTE → HOVERING`: distance_to_target < 15m, hover for surveillance
- `EN_ROUTE → REROUTING`: higher-priority alert, ETA > 30s remaining
- `HOVERING → RETURNING`: task_complete OR battery < 20%
- `RETURNING → IDLE`: docked at home base, battery restored (simulated 2 min)

### 6.3 Drone Metrics (Per Drone, Updated Every 500ms)

```json
{
  "id": "DR-01",
  "position": {"lat": 18.5220, "lon": 73.8580, "alt": 50},
  "home_base": {"lat": 18.5204, "lon": 73.8567},
  "battery": 87,
  "status": "EN_ROUTE",
  "target_zone": "B",
  "target_location": {"lat": 18.5308, "lon": 73.8474},
  "current_route": [{"lat": 18.5220, "lon": 73.8580}, "...waypoints..."],
  "eta_seconds": 36,
  "speed_ms": 15.0,
  "distance_remaining_m": 540,
  "rtl_time_seconds": 28,
  "rtl_distance_m": 420,
  "mission_id": "MSN-20260405-001",
  "assigned_alert_id": "AL-20260405-001",
  "score": 0.87,
  "can_be_reassigned": true
}
```

### 6.4 Dispatch Policy: 2 Drones Per Incident

When an alert is created with severity > 0.4, the system dispatches **2 drones**:

- **Primary Drone**: Best-scored available drone (lowest ETA × highest battery)
- **Secondary Drone**: Second-best drone, for redundancy and wider coverage of camera polygon

If only 1 drone is available, dispatch 1 and flag alert as `PARTIAL_RESPONSE`.

```python
def select_drone_pair(alert: Alert, drones: List[Drone]) -> Tuple[Drone, Drone]:
    available = [d for d in drones if d.status in (IDLE, EN_ROUTE) 
                 and d.battery > 30 and d.can_be_reassigned]
    scored = sorted(available, key=lambda d: score_drone(d, alert))
    return scored[0], scored[1] if len(scored) > 1 else None

def score_drone(drone: Drone, alert: Alert) -> float:
    """Lower score = better candidate"""
    eta = haversine(drone.position, alert.location) / drone.speed_ms
    battery_factor = 1.0 - (drone.battery / 100)
    return eta * 0.7 + battery_factor * 0.3
```

---

## 7. PRIORITY QUEUE & REALLOCATION ENGINE

### 7.1 Priority Queue Structure

Max-heap sorted by `(severity × recency_decay)`. Re-evaluated every **500ms**.

```python
class DroneDispatchQueue:
    heap: List[Tuple[float, datetime, Alert, Drone]]  # (neg_score, time, alert, drone)
    
    def push(alert: Alert, drone: Drone) -> None
    def pop() -> Tuple[Alert, Drone]
    def re_evaluate() -> List[ReallocDecision]  # Called every 500ms
    def get_queue_snapshot() -> List[QueueItem]
```

### 7.2 Reallocation Decision Logic

```python
def should_reallocate(drone: Drone, current_alert: Alert, new_alert: Alert) -> bool:
    # Conditions to trigger reallocation:
    severity_delta = new_alert.severity - current_alert.severity
    eta_remaining = drone.eta_seconds
    battery_ok = drone.battery > 30
    not_hovering = drone.status != "HOVERING"
    
    # Primary condition
    if severity_delta > 0.15 and eta_remaining > 30 and battery_ok and not_hovering:
        return True
    
    # Emergency override (weapon detected / person down)
    if new_alert.anomaly_type in ("weapon_detect", "person_down") and eta_remaining > 10:
        return True
    
    return False

def reallocate(drone: Drone, new_alert: Alert) -> ReallocResult:
    # Recompute route using CLSP
    new_route = clsp_shortest_path(graph, drone.position, new_alert.location)
    drone.current_route = new_route.waypoints
    drone.target_zone = new_alert.zone_id
    drone.eta_seconds = new_route.total_distance / drone.speed_ms
    drone.status = "REROUTING"
    drone.assigned_alert_id = new_alert.alert_id
    
    # Log reallocation event
    log_reallocation(drone.id, old_alert_id, new_alert.alert_id, reason="higher_severity")
    return ReallocResult(success=True, new_eta=drone.eta_seconds, new_route=new_route)
```

### 7.3 Queue Re-evaluation Cycle (Every 500ms)

```
1. Update all drone ETAs (position × speed × route remaining)
2. Update all alert severities (time decay: severity *= 0.99 per cycle if no new detection)
3. Re-score queue: score = severity / (1 + eta_normalized)
4. Check each EN_ROUTE drone: can any be reallocated to higher-priority alert?
5. Assign IDLE drones to unassigned alerts
6. Emit drone_update WebSocket event
```

---

## 8. SOS FEATURE

### 8.1 SOS Flow

```
React Native App → POST /sos/create
    → SOS saved to DB (status: PENDING)
    → WebSocket sos_received emitted to dashboard
    → 30-second human confirmation buffer starts
    → Timer countdown emitted via sos_countdown WebSocket event
    
    IF /sos/cancel called within 30s:
        → SOS cancelled, no drone dispatched
        → Reason logged (false_alarm / test / resolved)
    
    IF 30s elapsed without cancellation:
        → SOS auto-confirmed
        → Drone pair dispatched via normal priority queue
        → alert_created WebSocket event emitted
        → sos_dispatched event emitted with drone details
```

### 8.2 SOS Location Types

An SOS can originate from:
- **GPS coordinates** from the mobile app (primary)
- **Known camera zone** (if user selects zone on app)
- **Manual pin drop** on app map

### 8.3 SOS Priority

SOS alerts get severity = 0.90 (maximum non-weapon priority), weapon_detect overrides at 0.95.

---

## 9. GEMINI AI INTEGRATION

### 9.1 Role in the System

Gemini 1.5 Flash (`gemini-1.5-flash`) provides AI-based decision support for:

| Decision Point               | Gemini Input                                       | Gemini Output                                |
|-----------------------------|----------------------------------------------------|----------------------------------------------|
| Alert triage                | Anomaly type, severity, zone history, time of day  | Recommended action + confidence              |
| Reallocation approval       | Current queue state, new alert, drone metrics      | Approve/deny reallocation + reasoning        |
| False positive filtering    | Detection frame description, baseline deviation    | True/False positive probability              |
| SOS classification          | SOS text message, location, history                | Priority level + urgency reasoning           |
| Heatmap risk prediction     | Zone history, time, event density                  | Risk score + predicted next incident zone    |
| Dispatch narrative          | Full incident context                              | Human-readable dispatch report for dashboard |

### 9.2 Gemini Client

```python
# app/services/gemini_service.py
import google.generativeai as genai

genai.configure(api_key="")
model = genai.GenerativeModel("gemini-1.5-flash")

class GeminiDecisionEngine:
    
    async def triage_alert(self, alert: Alert, zone_history: List) -> TriageDecision:
        prompt = f"""
        You are SkyGuard AI for Pune Police Drone Office.
        
        INCIDENT: {alert.anomaly_type} at {alert.zone_name}
        SEVERITY: {alert.severity:.2f}
        TIME: {alert.timestamp} (hour {alert.hour})
        ZONE HISTORY (last 7 days same hour): {zone_history}
        BASELINE MEAN: {alert.baseline_mean}, CURRENT: {alert.current_count}
        
        Respond ONLY as JSON:
        {{
          "action": "DISPATCH" | "MONITOR" | "DISMISS",
          "confidence": 0.0-1.0,
          "reasoning": "brief explanation",
          "priority_override": null | 0.0-1.0
        }}
        """
        response = await model.generate_content_async(prompt)
        return parse_triage_json(response.text)
    
    async def filter_false_positive(self, detection_desc: str, anomaly_score: float) -> FPDecision:
        """Returns probability this is a genuine incident"""
        ...
    
    async def generate_dispatch_report(self, incident: Incident, drones: List[Drone]) -> str:
        """Returns human-readable dashboard report"""
        ...
    
    async def predict_risk_zones(self, heatmap_data: HeatmapData) -> List[RiskPrediction]:
        """Predicts next likely incident zones"""
        ...
```

**Token Optimization**: Use `gemini-1.5-flash` (not Pro). Cache system prompts. Only call Gemini for severity > 0.4 alerts. Batch heatmap predictions every 60 seconds.

---

## 10. HEATMAP & PREDICTIVE ANALYTICS

### 10.1 Incident Location Accumulation

Every dispatched drone mission records:
```python
# app/db/schemas.py — heatmap_events table
{
  "event_id": "HM-001",
  "lat": 18.5204,
  "lon": 73.8567,
  "zone_id": "A",
  "anomaly_type": "crowd_anomaly",
  "severity": 0.83,
  "timestamp": "2026-04-05T14:23:11Z",
  "hour": 14,
  "day_of_week": 6,  # Sunday
  "resolved": true
}
```

### 10.2 Heatmap Computation

```python
# app/core/heatmap.py
class HeatmapEngine:
    
    def compute_realtime_heatmap(self) -> HeatmapData:
        """
        Kernel Density Estimation (KDE) over incident points.
        - Grid: 0.001 degree resolution (~100m) over Pune bounds
        - Bandwidth: 500m gaussian kernel
        - Weight: severity × recency (exponential decay, half-life 24h)
        - Returns: List of {lat, lon, intensity} points
        """
        events = db.get_recent_heatmap_events(hours=168)  # 7 days
        kde_grid = gaussian_kde_weighted(events)
        return HeatmapData(points=kde_grid, computed_at=now())
    
    def get_hotspots(threshold=0.7) -> List[Hotspot]:
        """Returns high-risk zones above intensity threshold"""
        ...
    
    def predict_next_incident(hour: int, day: int) -> List[RiskZone]:
        """
        Time-aware prediction: weight events by time-of-week similarity.
        Feeds into Gemini for natural language risk narrative.
        """
        ...
```

### 10.3 Heatmap Updates

- Recomputed every **30 seconds** in background
- Broadcast via `heatmap_update` WebSocket event
- Cached in memory, persisted to SQLite daily

---

## 11. QGROUNDCONTROL OVERLAY FOR SKYDROID H12

### 11.1 MAVLink Integration

The QGroundControl overlay connects to the drone fleet via **MAVLink over UDP**. Each drone (simulated or real) exposes a MAVLink endpoint.

```python
# app/services/mavlink_bridge.py
from pymavlink import mavutil

class MAVLinkBridge:
    connections: Dict[str, mavutil.mavlink_connection]
    
    async def send_mission(drone_id: str, waypoints: List[LatLon]) -> bool:
        """
        Convert CLSP route waypoints to MAVLink MISSION_ITEM messages.
        Upload mission to drone/simulator.
        """
        
    async def send_reroute(drone_id: str, new_waypoints: List[LatLon]) -> bool:
        """Send DO_REPOSITION + new mission for mid-flight reroute"""
        
    async def get_telemetry(drone_id: str) -> DroneMetrics:
        """Poll GLOBAL_POSITION_INT + BATTERY_STATUS messages"""
        
    async def rtl(drone_id: str) -> bool:
        """Send MAV_CMD_NAV_RETURN_TO_LAUNCH"""
        
    async def emergency_land(drone_id: str) -> bool:
        """Send MAV_CMD_NAV_LAND at current position"""
```

### 11.2 QGC Overlay API Endpoints

The Skydroid H12 overlay is a **WebView** overlaid on QGroundControl. It connects to these backend endpoints:

```
GET  /qgc/mission/{drone_id}       → Current mission waypoints as MAVLink JSON
POST /qgc/dispatch                 → Dispatch drone pair to incident
POST /qgc/reroute/{drone_id}       → Reroute drone to new location
POST /qgc/rtl/{drone_id}           → Return to launch
POST /qgc/emergency_land/{drone_id}→ Emergency land
GET  /qgc/fleet_status             → All drone positions + statuses
WebSocket /qgc/live                → Real-time telemetry stream
```

### 11.3 H12 Overlay Frontend Spec

Single-page WebView app that renders over QGC map:
- Semi-transparent overlay (80% opacity on controls)
- Shows: incident list, drone assignments, dispatch buttons, RTL buttons
- Communicates with backend via REST + WebSocket on local WiFi

---

## 12. POLYGON ZONE MAPPING

Each camera covers a GPS polygon that defines its surveillance area. Drones target the **centroid** of the polygon (incident location). Polygon containment is checked with Shapely.

```python
# data/zones/pune_zones.geojson
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "zone_id": "A", "name": "MG Road Corridor",
        "camera_id": "CAM-01", "baseline_mean": 8.3
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[73.8555, 18.5198], [73.8580, 18.5198],
                          [73.8580, 18.5215], [73.8555, 18.5215],
                          [73.8555, 18.5198]]]
      }
    }
    // ... 7 more zones
  ]
}
```

**Drone Targeting**: When dispatched, drone targets `polygon.centroid`. If multiple detections in polygon, target weighted centroid of detection bounding box centers.

---

## 13. DATABASE SCHEMA (SQLite)

```sql
-- Cameras
CREATE TABLE cameras (
    cam_id TEXT PRIMARY KEY,       -- CAM-01 to CAM-08
    name TEXT,
    type TEXT,                     -- 'rtsp' | 'video_feed'
    source_url TEXT,
    zone_id TEXT,
    lat REAL, lon REAL,
    polygon_geojson TEXT,          -- JSON string of coverage polygon
    is_active INTEGER DEFAULT 1
);

-- Zones
CREATE TABLE zones (
    zone_id TEXT PRIMARY KEY,      -- A to H
    name TEXT,
    cam_id TEXT,
    polygon_geojson TEXT,
    centroid_lat REAL, centroid_lon REAL,
    baseline_mean REAL,
    baseline_std REAL,
    FOREIGN KEY (cam_id) REFERENCES cameras(cam_id)
);

-- Zone Baselines
CREATE TABLE zone_baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id TEXT,
    hour INTEGER,                  -- 0-23
    day_of_week INTEGER,           -- 0-6
    mean REAL,
    std_dev REAL,
    sample_count INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drones
CREATE TABLE drones (
    drone_id TEXT PRIMARY KEY,     -- DR-01 to DR-04
    home_lat REAL, home_lon REAL,
    current_lat REAL, current_lon REAL,
    altitude REAL DEFAULT 50,
    battery INTEGER DEFAULT 100,
    status TEXT DEFAULT 'IDLE',
    speed_ms REAL DEFAULT 15.0,
    max_range_m REAL DEFAULT 5000,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerts
CREATE TABLE alerts (
    alert_id TEXT PRIMARY KEY,
    zone_id TEXT,
    cam_id TEXT,
    anomaly_type TEXT,             -- fight_detection|person_down|weapon_detect|crowd_anomaly|suspicious_behavior
    severity REAL,
    current_count INTEGER,
    baseline_mean REAL,
    z_score REAL,
    location_lat REAL, location_lon REAL,
    primary_drone_id TEXT,
    secondary_drone_id TEXT,
    status TEXT DEFAULT 'ACTIVE',  -- ACTIVE|RESOLVED|CANCELLED|PARTIAL_RESPONSE
    gemini_action TEXT,            -- DISPATCH|MONITOR|DISMISS
    gemini_confidence REAL,
    source TEXT DEFAULT 'camera',  -- 'camera' | 'sos'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dispatched_at TIMESTAMP,
    resolved_at TIMESTAMP
);

-- SOS Events
CREATE TABLE sos_events (
    sos_id TEXT PRIMARY KEY,
    sender_id TEXT,                -- React Native user/device ID
    message TEXT,
    lat REAL, lon REAL,
    location_type TEXT,            -- 'gps' | 'zone' | 'manual'
    zone_id TEXT,
    status TEXT DEFAULT 'PENDING', -- PENDING|CONFIRMED|CANCELLED|DISPATCHED
    confirmed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    cancel_reason TEXT,
    alert_id TEXT,                 -- linked alert if dispatched
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Missions
CREATE TABLE missions (
    mission_id TEXT PRIMARY KEY,
    alert_id TEXT,
    drone_id TEXT,
    role TEXT,                     -- 'primary' | 'secondary'
    route_waypoints TEXT,          -- JSON array of {lat,lon} waypoints
    no_fly_zones_avoided TEXT,     -- JSON array of NFZ IDs avoided
    algorithm TEXT DEFAULT 'CLSP', -- routing algorithm used
    total_distance_m REAL,
    planned_eta_s INTEGER,
    actual_duration_s INTEGER,
    status TEXT DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Heatmap Events
CREATE TABLE heatmap_events (
    event_id TEXT PRIMARY KEY,
    lat REAL, lon REAL,
    zone_id TEXT,
    anomaly_type TEXT,
    severity REAL,
    hour INTEGER,
    day_of_week INTEGER,
    resolved INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reallocation Log
CREATE TABLE reallocation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drone_id TEXT,
    from_alert_id TEXT,
    to_alert_id TEXT,
    reason TEXT,                   -- 'higher_severity' | 'emergency_override' | 'battery_critical'
    old_eta_s INTEGER,
    new_eta_s INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);
CREATE INDEX idx_alerts_zone ON alerts(zone_id);
CREATE INDEX idx_heatmap_time ON heatmap_events(timestamp DESC);
CREATE INDEX idx_heatmap_zone ON heatmap_events(zone_id);
CREATE INDEX idx_missions_drone ON missions(drone_id);
```

---

## 14. ALL REST API ENDPOINTS

### Base URL: `http://0.0.0.0:8000`

---

### 14.1 Health & System

#### `GET /health`
Returns full system health status.
```json
// Response 200
{
  "status": "healthy",
  "timestamp": "2026-04-05T14:23:11Z",
  "uptime_seconds": 3600,
  "version": "2.0.0",
  "components": {
    "cameras": {
      "total": 8, "online": 8, "offline": 0,
      "feeds": [
        {"cam_id": "CAM-01", "type": "rtsp", "status": "connected", "fps": 10.2},
        {"cam_id": "CAM-02", "type": "video_feed", "status": "playing", "fps": 10.0}
      ]
    },
    "model": {"status": "loaded", "device": "cpu", "inference_ms_avg": 87},
    "database": {"status": "connected", "alerts_today": 12},
    "websocket": {"status": "active", "connections": 3},
    "gemini": {"status": "connected", "calls_today": 45},
    "mavlink": {"status": "active", "drones_connected": 4}
  }
}
```

#### `GET /metrics`
CPU, memory, FPS per camera, queue depth.
```json
{
  "cpu_percent": 72.3,
  "memory_mb": 1240,
  "cameras": [{"cam_id": "CAM-01", "fps": 10.2, "inference_ms": 87}],
  "queue_depth": 3,
  "alerts_per_minute": 0.8,
  "uptime_s": 3600
}
```

---

### 14.2 Camera Endpoints

#### `GET /cameras`
All camera statuses and zone associations.
```json
[{
  "cam_id": "CAM-01", "name": "MG Road Live", "type": "rtsp",
  "status": "connected", "fps": 10.2,
  "zone_id": "A", "zone_name": "MG Road Corridor",
  "location": {"lat": 18.5204, "lon": 73.8567},
  "current_count": 12, "current_severity": 0.83
}]
```

#### `GET /cameras/{cam_id}/stream`
MJPEG stream with YOLO bounding boxes and anomaly labels.
```
Content-Type: multipart/x-mixed-replace; boundary=frame
```
Query params: `?overlay=true` (draw bounding boxes) | `?quality=80`

#### `GET /cameras/{cam_id}/snapshot`
Single JPEG frame.
```
Content-Type: image/jpeg
```

#### `GET /cameras/{cam_id}/detections`
Latest detection results for a camera.
```json
{
  "cam_id": "CAM-01", "timestamp": "...",
  "fps": 10.2, "inference_ms": 87,
  "detections": [{
    "bbox": [120, 340, 180, 520],
    "confidence": 0.87, "class": "person",
    "zone": "A", "anomaly_flags": ["crowd_anomaly"]
  }],
  "anomaly_types_detected": ["crowd_anomaly"],
  "total_persons": 12
}
```

---

### 14.3 Zone Endpoints

#### `GET /zones`
All 8 zones with polygons and current stats.
```json
[{
  "zone_id": "A", "name": "MG Road Corridor",
  "camera_id": "CAM-01",
  "polygon": [[18.5198, 73.8555], [18.5198, 73.8580], [18.5215, 73.8580], [18.5215, 73.8555], [18.5198, 73.8555]],
  "centroid": {"lat": 18.5206, "lon": 73.8567},
  "baseline_mean": 8.3, "baseline_std": 2.1,
  "current_count": 12,
  "anomaly_score": 0.83, "severity": 0.83,
  "active_alert_id": "AL-20260405-001"
}]
```

#### `GET /zones/{zone_id}/baseline`
Hourly baseline profile for zone.
```json
{
  "zone_id": "A",
  "baselines": [
    {"hour": 0, "day": "all", "mean": 3.2, "std": 1.8},
    {"hour": 14, "day": "all", "mean": 8.3, "std": 2.1}
  ]
}
```

---

### 14.4 Alert Endpoints

#### `GET /alerts`
Active and recent alerts. Query params: `?status=ACTIVE&limit=20&zone_id=A`
```json
[{
  "alert_id": "AL-20260405-142311-001",
  "zone_id": "A", "zone_name": "MG Road Corridor",
  "cam_id": "CAM-01",
  "anomaly_type": "crowd_anomaly",
  "severity": 0.83,
  "current_count": 12, "baseline_mean": 8.3, "z_score": 1.28,
  "location": {"lat": 18.5206, "lon": 73.8567},
  "primary_drone": "DR-01", "secondary_drone": "DR-02",
  "primary_eta": 36, "secondary_eta": 48,
  "status": "ACTIVE",
  "gemini_action": "DISPATCH", "gemini_confidence": 0.92,
  "gemini_reasoning": "High crowd density at peak hour, historical pattern consistent",
  "source": "camera",
  "created_at": "2026-04-05T14:23:11Z"
}]
```

#### `POST /alerts/manual`
Manually create an alert (demo trigger / operator override).
```json
// Request
{
  "zone_id": "B",
  "anomaly_type": "fight_detection",
  "severity": 0.85,
  "reason": "Operator observation"
}
// Response 201
{
  "alert_id": "AL-20260405-142500-002",
  "zone_id": "B", "severity": 0.85,
  "primary_drone": "DR-01", "secondary_drone": "DR-03",
  "primary_eta": 42, "secondary_eta": 58,
  "status": "ACTIVE",
  "route_primary": [{"lat": 18.5220, "lon": 73.8580}, "..."],
  "route_secondary": [{"lat": 18.5310, "lon": 73.8460}, "..."],
  "no_fly_zones_avoided": ["NFZ-01"],
  "created_at": "2026-04-05T14:25:00Z"
}
```

#### `PATCH /alerts/{alert_id}/resolve`
Mark alert as resolved.
```json
// Request
{ "resolution": "Situation normalized", "resolved_by": "operator" }
// Response 200
{ "alert_id": "...", "status": "RESOLVED", "resolved_at": "..." }
```

---

### 14.5 Drone Endpoints

#### `GET /drones`
All drone states and metrics.
```json
[{
  "id": "DR-01",
  "position": {"lat": 18.5220, "lon": 73.8580, "alt": 50},
  "home_base": {"lat": 18.5204, "lon": 73.8567},
  "battery": 87, "status": "EN_ROUTE",
  "target_zone": "B",
  "target_location": {"lat": 18.5308, "lon": 73.8474},
  "current_route": [{"lat": 18.5220, "lon": 73.8580}, "..."],
  "eta_seconds": 36, "speed_ms": 15.0,
  "distance_remaining_m": 540,
  "rtl_time_seconds": 28, "rtl_distance_m": 420,
  "mission_id": "MSN-20260405-001",
  "assigned_alert_id": "AL-20260405-001",
  "score": 0.87, "can_be_reassigned": true
}]
```

#### `GET /drones/{drone_id}`
Single drone detail.

#### `POST /drones/{drone_id}/dispatch`
Manually dispatch drone to location.
```json
// Request
{
  "target_lat": 18.5308, "target_lon": 73.8474,
  "mission_type": "surveillance",
  "priority": "high"
}
// Response 200
{
  "drone_id": "DR-01", "status": "EN_ROUTE",
  "route": [...], "eta_seconds": 42,
  "no_fly_zones_avoided": [],
  "algorithm": "CLSP"
}
```

#### `POST /drones/{drone_id}/rtl`
Send Return to Launch command.
```json
// Response 200
{ "drone_id": "DR-01", "status": "RETURNING", "rtl_eta_seconds": 28 }
```

#### `POST /drones/{drone_id}/reroute`
Force reroute to new target.
```json
// Request
{ "new_lat": 18.5362, "new_lon": 73.8939, "reason": "higher_priority_alert" }
// Response 200
{ "drone_id": "DR-01", "new_route": [...], "new_eta": 67, "status": "REROUTING" }
```

#### `GET /drones/{drone_id}/history`
Past missions for a drone.
```json
[{
  "mission_id": "MSN-001", "alert_id": "AL-001",
  "started_at": "...", "completed_at": "...",
  "duration_s": 240, "distance_m": 1800,
  "outcome": "surveillance_complete"
}]
```

---

### 14.6 Route Planning

#### `POST /routes/plan`
Compute CLSP route between two points (respects no-fly zones).
```json
// Request
{
  "from": {"lat": 18.5204, "lon": 73.8567},
  "to": {"lat": 18.5362, "lon": 73.8939}
}
// Response 200
{
  "algorithm": "CLSP",
  "waypoints": [{"lat": 18.5204, "lon": 73.8567, "alt": 50}, "..."],
  "total_distance_m": 4200,
  "estimated_time_s": 280,
  "no_fly_zones_avoided": ["NFZ-01"],
  "cluster_path": ["C1", "C3", "C5"],
  "computation_ms": 12
}
```

#### `GET /routes/no_fly_zones`
All active no-fly zones.
```json
[{
  "id": "NFZ-01", "name": "Pune Airport Restricted",
  "polygon": [[...]], "center": {"lat": 18.5822, "lon": 73.9197},
  "radius_m": 2000, "active": true
}]
```

---

### 14.7 SOS Endpoints

#### `POST /sos`
Create SOS alert from mobile app.
```json
// Request
{
  "sender_id": "user_abc123",
  "message": "Fight happening near fountain",
  "lat": 18.5204, "lon": 73.8567,
  "location_type": "gps"  // 'gps' | 'zone' | 'manual'
}
// Response 201
{
  "sos_id": "SOS-20260405-001",
  "status": "PENDING",
  "confirmation_deadline": "2026-04-05T14:25:30Z",
  "buffer_seconds": 30,
  "message": "SOS received. Drone dispatch pending human confirmation. Cancel within 30 seconds if false alarm."
}
```

#### `POST /sos/{sos_id}/cancel`
Cancel SOS within buffer window.
```json
// Request
{ "reason": "false_alarm" }  // 'false_alarm' | 'resolved' | 'test'
// Response 200
{ "sos_id": "SOS-001", "status": "CANCELLED", "reason": "false_alarm" }
```

#### `GET /sos`
List all SOS events. Query: `?status=PENDING&limit=10`
```json
[{
  "sos_id": "SOS-001", "status": "PENDING",
  "message": "Fight near fountain",
  "location": {"lat": 18.5204, "lon": 73.8567},
  "seconds_remaining": 22,
  "created_at": "..."
}]
```

#### `GET /sos/{sos_id}`
Single SOS detail with linked alert if dispatched.

---

### 14.8 Heatmap Endpoints

#### `GET /heatmap`
Current incident density heatmap.
```json
{
  "computed_at": "2026-04-05T14:23:00Z",
  "points": [
    {"lat": 18.5204, "lon": 73.8567, "intensity": 0.87},
    {"lat": 18.5308, "lon": 73.8474, "intensity": 0.45}
  ],
  "hotspots": [
    {"zone_id": "A", "zone_name": "MG Road", "intensity": 0.87, "incident_count": 8}
  ],
  "total_incidents": 47,
  "time_range_hours": 168
}
```

#### `GET /heatmap/predict`
AI-predicted risk zones for next 2 hours.
```json
{
  "prediction_hour": 16, "predicted_for": "2026-04-05T16:00:00Z",
  "risk_zones": [
    {
      "zone_id": "A", "zone_name": "MG Road",
      "risk_score": 0.82,
      "gemini_reasoning": "Historical peak at 16:00 on Sundays. Pattern match 87%.",
      "recommended_action": "PRE_POSITION_DRONE"
    }
  ]
}
```

#### `GET /heatmap/history`
Historical incident counts per zone. Query: `?zone_id=A&days=7`
```json
{
  "zone_id": "A",
  "incidents": [
    {"date": "2026-04-04", "hour": 14, "count": 3, "avg_severity": 0.71},
    {"date": "2026-04-03", "hour": 14, "count": 1, "avg_severity": 0.55}
  ]
}
```

---

### 14.9 Baseline Endpoints

#### `GET /baseline/stats`
Current anomaly scores for all zones.
```json
{
  "timestamp": "...",
  "zones": [{
    "zone_id": "A", "current": 12, "mean": 8.3, "std_dev": 2.1,
    "z_score": 1.28, "anomaly_score": 0.83, "severity": 0.83
  }]
}
```

---

### 14.10 QGroundControl Bridge

#### `GET /qgc/fleet_status`
Fleet summary for H12 overlay.
```json
{
  "drones": [{"id": "DR-01", "status": "EN_ROUTE", "battery": 87, "eta": 36, "lat": 18.5220, "lon": 73.8580}],
  "active_alerts": 2, "queue_depth": 3
}
```

#### `POST /qgc/dispatch`
Dispatch command from H12 overlay.
```json
// Request
{ "alert_id": "AL-001", "drone_ids": ["DR-01", "DR-02"] }
// Response 200
{ "dispatched": true, "missions": [{"drone_id": "DR-01", "eta": 36}, {"drone_id": "DR-02", "eta": 48}] }
```

---

## 15. WEBSOCKET EVENTS

### Connection: `ws://0.0.0.0:8000/socket.io/`

---

### 15.1 Backend → Frontend Events

#### `drone_update` — Every 500ms
```json
{
  "event": "drone_update",
  "timestamp": "2026-04-05T14:23:11.345Z",
  "data": {
    "drones": [{
      "id": "DR-01",
      "position": {"lat": 18.5220, "lon": 73.8580, "alt": 50},
      "battery": 87, "status": "EN_ROUTE",
      "target_zone": "B", "target_location": {"lat": 18.5308, "lon": 73.8474},
      "eta": 36, "speed_ms": 15.0,
      "distance_remaining_m": 540,
      "rtl_time_s": 28, "score": 0.87,
      "can_be_reassigned": true,
      "route_remaining": [{"lat": 18.5235, "lon": 73.8590}, "..."],
      "mission_id": "MSN-001"
    }]
  }
}
```

#### `alert_created` — On new anomaly (severity > 0.4)
```json
{
  "event": "alert_created",
  "timestamp": "2026-04-05T14:23:11.567Z",
  "data": {
    "alert_id": "AL-20260405-142311-001",
    "zone_id": "A", "zone_name": "MG Road Corridor",
    "cam_id": "CAM-01",
    "anomaly_type": "crowd_anomaly",
    "severity": 0.83,
    "current_count": 12, "baseline_mean": 8.3, "z_score": 1.28,
    "primary_drone": "DR-01", "secondary_drone": "DR-02",
    "primary_eta": 36, "secondary_eta": 48,
    "location": {"lat": 18.5206, "lon": 73.8567},
    "source_camera": "CAM-01",
    "gemini_action": "DISPATCH",
    "gemini_confidence": 0.92,
    "polygon": [[18.5198, 73.8555], "..."],
    "routes": {
      "primary": [{"lat": 18.5220, "lon": 73.8580}, "..."],
      "secondary": [{"lat": 18.5310, "lon": 73.8460}, "..."]
    },
    "no_fly_avoided": ["NFZ-01"]
  }
}
```

#### `alert_updated` — On status change
```json
{
  "event": "alert_updated",
  "data": {
    "alert_id": "AL-001", "status": "RESOLVED",
    "resolved_at": "...", "duration_s": 240
  }
}
```

#### `baseline_update` — Every 5 seconds
```json
{
  "event": "baseline_update",
  "timestamp": "...",
  "data": {
    "zones": [{
      "zone_id": "A", "current": 12, "mean": 8.3,
      "std_dev": 2.1, "anomaly_score": 0.83, "severity": 0.83
    }]
  }
}
```

#### `heatmap_update` — Every 30 seconds
```json
{
  "event": "heatmap_update",
  "timestamp": "...",
  "data": {
    "points": [{"lat": 18.5204, "lon": 73.8567, "intensity": 0.87}],
    "hotspots": [{"zone_id": "A", "intensity": 0.87}],
    "predictions": [{"zone_id": "A", "risk_score": 0.82, "hour": 16}]
  }
}
```

#### `sos_received` — On new SOS
```json
{
  "event": "sos_received",
  "data": {
    "sos_id": "SOS-001", "status": "PENDING",
    "message": "Fight near fountain",
    "location": {"lat": 18.5204, "lon": 73.8567},
    "buffer_seconds": 30,
    "created_at": "..."
  }
}
```

#### `sos_countdown` — Every second during buffer
```json
{
  "event": "sos_countdown",
  "data": {
    "sos_id": "SOS-001",
    "seconds_remaining": 22,
    "status": "PENDING"
  }
}
```

#### `sos_dispatched` — After buffer expires without cancel
```json
{
  "event": "sos_dispatched",
  "data": {
    "sos_id": "SOS-001",
    "alert_id": "AL-002",
    "primary_drone": "DR-01",
    "secondary_drone": "DR-02",
    "eta": 45
  }
}
```

#### `drone_reallocated` — On mid-flight reassignment
```json
{
  "event": "drone_reallocated",
  "data": {
    "drone_id": "DR-01",
    "from_alert_id": "AL-001", "to_alert_id": "AL-002",
    "reason": "higher_severity",
    "old_eta": 36, "new_eta": 67,
    "new_route": [...]
  }
}
```

#### `camera_offline` / `camera_online`
```json
{ "event": "camera_offline", "data": { "cam_id": "CAM-01", "reason": "RTSP connection lost" } }
```

#### `detection_stream` — Every frame (opt-in, high frequency)
```json
{
  "event": "detection_stream",
  "data": {
    "cam_id": "CAM-01", "fps": 10.2,
    "detections": [{"bbox": [120, 340, 180, 520], "confidence": 0.87, "class": "person", "zone": "A"}],
    "anomaly_flags": ["crowd_anomaly"],
    "processing_ms": 87
  }
}
```

#### `system_error`
```json
{ "event": "system_error", "data": { "component": "YOLO", "message": "...", "severity": "warning" } }
```

---

### 15.2 Frontend → Backend Events

#### `subscribe_camera` — Subscribe to detection stream for specific camera
```json
{ "cam_id": "CAM-01" }
```

#### `request_dispatch` — Manual dispatch from dashboard
```json
{ "alert_id": "AL-001" }
```

#### `request_reroute`
```json
{ "drone_id": "DR-01", "alert_id": "AL-002" }
```

---

## 16. BACKGROUND TASK SCHEDULE

| Task                      | Interval | Function                                      |
|---------------------------|----------|-----------------------------------------------|
| Detection loop (all cams) | 100ms    | YOLO inference on all 8 camera frames         |
| Priority queue eval       | 500ms    | Re-score, reallocate, assign idle drones      |
| Drone position update     | 500ms    | Interpolate positions along routes            |
| drone_update broadcast    | 500ms    | Emit all drone states via WebSocket           |
| Baseline update           | 500ms    | Recalculate anomaly scores per zone           |
| baseline_update broadcast | 5s       | Emit zone stats via WebSocket                 |
| SOS buffer checker        | 1s       | Check pending SOS countdowns                  |
| Heatmap recompute         | 30s      | KDE over recent incidents                     |
| heatmap_update broadcast  | 30s      | Emit heatmap via WebSocket                    |
| Gemini risk prediction    | 60s      | Predict next 2 hours risk zones               |
| Baseline learning         | Per 100  | Update Poisson params from real detections    |
| Health check              | 10s      | Poll all component statuses                   |
| Battery simulation        | 1s       | Drain battery (0.05%/s flying, restore docked)|

---

## 17. DIRECTORY STRUCTURE

```
skyguard-v2/
├── app/
│   ├── main.py                    # FastAPI + SocketIO entry
│   ├── config.py                  # Pydantic settings from .env
│   ├── core/
│   │   ├── camera_manager.py      # 8-camera orchestrator
│   │   ├── camera_rtsp.py         # CP Plus RTSP handler
│   │   ├── camera_video.py        # Video file feed handler
│   │   ├── detection.py           # MultiModelDetector (5 types)
│   │   ├── baseline.py            # Poisson anomaly engine
│   │   ├── priority_queue.py      # Dispatch queue + reallocation
│   │   ├── routing.py             # CLSP algorithm + AirspaceGraph
│   │   ├── geofence.py            # No-fly zone enforcement
│   │   ├── heatmap.py             # KDE heatmap + predictions
│   │   └── drone_simulator.py     # Drone position interpolation
│   ├── services/
│   │   ├── websocket.py           # SocketIO manager + room handling
│   │   ├── gemini_service.py      # Gemini 1.5 Flash integration
│   │   ├── mavlink_bridge.py      # QGroundControl MAVLink bridge
│   │   ├── alert_manager.py       # Alert lifecycle + SOS timer
│   │   └── background_tasks.py    # All async loops
│   ├── api/
│   │   ├── cameras.py             # /cameras routes
│   │   ├── alerts.py              # /alerts routes
│   │   ├── drones.py              # /drones routes
│   │   ├── routes_api.py          # /routes planning routes
│   │   ├── sos.py                 # /sos routes
│   │   ├── heatmap.py             # /heatmap routes
│   │   ├── baseline.py            # /baseline routes
│   │   ├── qgc.py                 # /qgc overlay routes
│   │   └── health.py              # /health, /metrics
│   ├── models/
│   │   ├── drone.py               # DroneState, DroneMetrics Pydantic
│   │   ├── alert.py               # Alert, AlertCreate Pydantic
│   │   ├── sos.py                 # SOSEvent Pydantic
│   │   ├── zone.py                # Zone, ZoneBaseline Pydantic
│   │   ├── heatmap.py             # HeatmapData, HeatmapPoint
│   │   └── routing.py             # Route, Waypoint, NoFlyZone
│   ├── db/
│   │   ├── database.py            # SQLite connection + pool
│   │   ├── schemas.sql            # All CREATE TABLE statements
│   │   ├── crud.py                # CRUD operations
│   │   └── seed.py                # Initial data seeding
│   └── utils/
│       ├── haversine.py           # Distance calculations
│       ├── geo_utils.py           # Shapely polygon helpers
│       ├── logger.py              # Structured JSON logger
│       └── validators.py          # Input validation
├── data/
│   ├── models/yolo11n.pt          # YOLO weights
│   ├── zones/pune_zones.geojson   # 8 zone polygons
│   ├── geofence/pune_nfz.geojson  # 2 no-fly zones
│   ├── airspace/pune_graph.json   # Pre-built airspace waypoint graph
│   ├── baselines/pune_baselines.json
│   └── feeds/                     # cam02-cam08 .mp4 files
├── tests/
│   ├── test_detection.py
│   ├── test_routing.py            # CLSP algorithm tests
│   ├── test_priority_queue.py
│   ├── test_geofence.py
│   ├── test_heatmap.py
│   ├── test_sos.py
│   └── test_websocket.py
├── scripts/
│   ├── seed_database.py
│   ├── build_airspace_graph.py    # Pre-compute Pune waypoint graph
│   ├── download_models.py
│   └── generate_feeds.py          # Download/prepare dataset videos
├── .env
├── requirements.txt
└── Dockerfile
```

---

## 18. KEY DEPENDENCIES (`requirements.txt`)

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-socketio==5.11.1
python-multipart==0.0.9
pydantic==2.7.0
pydantic-settings==2.2.1
opencv-python-headless==4.9.0.80
ultralytics==8.2.0
numpy==1.26.4
scipy==1.13.0
shapely==2.0.4
geopy==2.4.1
google-generativeai==0.5.3
pymavlink==2.4.41
aiosqlite==0.20.0
httpx==0.27.0
python-dotenv==1.0.1
```

---

## 19. ENVIRONMENT VARIABLES (`.env`)

```bash
# Camera
RTSP_URL=rtsp://admin:admin@192.168.1.64:554/cam/realmonitor?channel=1&subtype=0
CAMERA_FPS=10
VIDEO_FEED_DIR=data/feeds

# Models
YOLO_MODEL_PATH=data/models/yolo11n.pt
YOLO_CONF_THRESHOLD=0.5
YOLO_DEVICE=cpu

# Gemini
GEMINI_API_KEY=AIzaSyC8VVKrWPA4ltET4RE0SV5MyrXSq8w6TkQ
GEMINI_MODEL=gemini-1.5-flash

# Drones
DRONE_SPEED_MS=15.0
DRONE_MIN_BATTERY=30
REALLOC_SEVERITY_DELTA=0.15
REALLOC_MIN_ETA_S=30
DRONES_PER_INCIDENT=2

# Routing
NFZ_GEOJSON=data/geofence/pune_nfz.geojson
ZONE_GEOJSON=data/zones/pune_zones.geojson
AIRSPACE_GRAPH=data/airspace/pune_graph.json

# SOS
SOS_BUFFER_SECONDS=30

# Heatmap
HEATMAP_BANDWIDTH_M=500
HEATMAP_DECAY_HOURS=168

# API
HOST=0.0.0.0
PORT=8000

# DB
SQLITE_PATH=data/skyguard.db

# MAVLink
MAVLINK_ENABLED=true
MAVLINK_DRONE_PORTS=DR-01:14550,DR-02:14551,DR-03:14552,DR-04:14553
```

---

## 20. EDGE CASES & ERROR HANDLING

| Scenario | Handling |
|----------|----------|
| RTSP camera disconnects | Auto-reconnect (5 retries, exponential backoff). Emit `camera_offline`. Show last frame for 3s. |
| Video feed ends | Loop from start. Log loop event. |
| All drones unavailable | Alert created as `PARTIAL_RESPONSE`. Emit `insufficient_drones` event. Queue for next available. |
| No path around no-fly zone | Find perimeter boundary route. If still no path, log error, alert as `ROUTE_BLOCKED`. |
| Gemini API fails / timeout | Fallback to rule-based triage (severity > 0.7 → DISPATCH, else MONITOR). Log failure. |
| SOS buffer expires (no cancel) | Auto-dispatch. Can't be cancelled after buffer. Only RTL available. |
| Drone battery critical (<20%) | Force RETURNING. Remove from queue. Reassign active mission to next drone. |
| Two simultaneous alerts | Both enter queue. Scored separately. Each gets own drone pair (or shared if fleet constrained). |
| Baseline data missing for zone | Default to Poisson(λ=5). Log warning. Learn from 50 samples before updating DB. |
| MAVLink connection lost | Continue simulation. Attempt reconnect every 10s. Log disconnection. |
| WebSocket client disconnects | State preserved. Full snapshot sent on reconnect via `state_sync` event. |

---

*Document Version: 2.0 | Last Updated: April 5, 2026 | SkyGuard Backend — Pune Police Drone Office*
