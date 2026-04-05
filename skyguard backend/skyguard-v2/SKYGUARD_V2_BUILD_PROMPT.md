# SKYGUARD V2 — AI CODING AGENT BUILD PROMPT
**Token-Optimized | Production-Ready | Complete Implementation Spec**

---

## MASTER PROMPT (Copy this entire block to your AI coding agent)

---

```
You are building SKYGUARD V2 — a production Python FastAPI backend for Pune Police Drone Office.
Build the COMPLETE working system. No placeholders. No TODOs. Every function must run.

=== STACK ===
Python 3.11, FastAPI 0.111, python-socketio 5.11, ultralytics (YOLO11n), OpenCV,
SQLite (aiosqlite), Shapely 2.0, scipy, numpy, google-generativeai 0.5.3, pymavlink, geopy

=== SYSTEM IN ONE PARAGRAPH ===
8 AI cameras (1 RTSP live + 7 looping mp4 video feeds) feed YOLO11n detection pipeline
detecting 5 anomaly types. Detected anomalies trigger Poisson baseline scoring. Severity > 0.4
creates an Alert. Gemini 1.5 Flash triages alert (DISPATCH/MONITOR/DISMISS). On DISPATCH, 2 drones
are selected via priority scoring and routed via CLSP algorithm (clustering-based, faster than
Dijkstra) avoiding 2 no-fly zones. Drones are simulated flying to incident location. Priority
queue re-evaluates every 500ms for mid-flight reallocation. SOS from React Native app creates
PENDING alert with 30s human cancellation buffer, then auto-dispatches. All events broadcast
via WebSocket. Incident locations feed KDE heatmap with Gemini risk predictions.

=== IMPLEMENT IN THIS EXACT ORDER ===

STEP 1: PROJECT SCAFFOLD
Create directory structure:
skyguard-v2/app/{core,services,api,models,db,utils}/, data/{models,zones,geofence,feeds,airspace,baselines}/
Create: .env, requirements.txt, app/__init__.py for all packages.

STEP 2: DATABASE LAYER (app/db/)
File: database.py — aiosqlite connection pool, get_db() context manager
File: schemas.sql — CREATE TABLE for: cameras, zones, zone_baselines, drones, alerts, sos_events,
  missions, heatmap_events, reallocation_log (exact schemas provided below)
File: crud.py — async CRUD for all tables: create/get/update/list with proper filtering
File: seed.py — seed 8 cameras, 8 zones, 4 drones, baseline data for all zones×24hours on startup

DB SCHEMAS (implement exactly):
cameras(cam_id PK, name, type[rtsp/video_feed], source_url, zone_id, lat, lon, polygon_geojson, is_active)
zones(zone_id PK, name, cam_id FK, polygon_geojson, centroid_lat, centroid_lon, baseline_mean, baseline_std)
zone_baselines(id PK AI, zone_id, hour 0-23, day_of_week 0-6, mean, std_dev, sample_count, updated_at)
drones(drone_id PK, home_lat, home_lon, current_lat, current_lon, altitude, battery, status, speed_ms, updated_at)
alerts(alert_id PK, zone_id, cam_id, anomaly_type, severity, current_count, baseline_mean, z_score,
  location_lat, location_lon, primary_drone_id, secondary_drone_id, status, gemini_action,
  gemini_confidence, source[camera/sos], created_at, dispatched_at, resolved_at)
sos_events(sos_id PK, sender_id, message, lat, lon, location_type, zone_id, status, confirmed_at,
  cancelled_at, cancel_reason, alert_id FK, created_at)
missions(mission_id PK, alert_id FK, drone_id FK, role[primary/secondary], route_waypoints JSON,
  no_fly_zones_avoided JSON, algorithm, total_distance_m, planned_eta_s, actual_duration_s, status, created_at, completed_at)
heatmap_events(event_id PK, lat, lon, zone_id, anomaly_type, severity, hour, day_of_week, resolved, timestamp)
reallocation_log(id PK AI, drone_id, from_alert_id, to_alert_id, reason, old_eta_s, new_eta_s, timestamp)

STEP 3: DATA MODELS (app/models/) — Pydantic v2
DroneStatus enum: IDLE, EN_ROUTE, REROUTING, HOVERING, RETURNING
AnomalyType enum: crowd_anomaly, fight_detection, person_down, weapon_detect, suspicious_behavior
AlertStatus enum: ACTIVE, RESOLVED, CANCELLED, PARTIAL_RESPONSE, ROUTE_BLOCKED
SOSStatus enum: PENDING, CONFIRMED, CANCELLED, DISPATCHED

DroneState: id, position(lat,lon,alt), home_base, battery, status, target_zone, target_location,
  current_route(List[Waypoint]), eta_seconds, speed_ms, distance_remaining_m, rtl_time_seconds,
  rtl_distance_m, mission_id, assigned_alert_id, score, can_be_reassigned

Alert: alert_id, zone_id, zone_name, cam_id, anomaly_type, severity, current_count, baseline_mean,
  z_score, location, primary_drone, secondary_drone, primary_eta, secondary_eta, status,
  gemini_action, gemini_confidence, gemini_reasoning, source, polygon, routes, created_at

SOSEvent: sos_id, sender_id, message, location, location_type, zone_id, status,
  buffer_seconds, seconds_remaining, alert_id, created_at

Route: waypoints(List[Waypoint]), total_distance_m, estimated_time_s, no_fly_zones_avoided,
  cluster_path, computation_ms

HeatmapPoint: lat, lon, intensity
HeatmapData: points(List[HeatmapPoint]), hotspots, predictions, computed_at, total_incidents

STEP 4: UTILITY MODULES (app/utils/)
haversine.py: haversine_distance(lat1,lon1,lat2,lon2)->float in meters
geo_utils.py: point_in_polygon(lat,lon,polygon)->bool using Shapely; polygon_centroid(polygon)->LatLon;
  polygons_overlap(p1,p2)->bool; edge_intersects_polygon(p1,p2,polygon)->bool
logger.py: setup_logger(name)->Logger with JSON formatter, file handler logs/backend.log

STEP 5: GEOFENCE MODULE (app/core/geofence.py)
Load pune_nfz.geojson on startup containing 2 no-fly zones:
  NFZ-01: Pune Airport area (18.5822, 73.9197) polygon
  NFZ-02: Military Cantonment (18.5200, 73.8700) polygon
Methods:
  is_point_in_nfz(lat,lon)->Optional[str]: returns NFZ id if inside, else None
  get_active_nfz()->List[NoFlyZone]
  get_nfz_boundary_waypoints(nfz_id)->List[LatLon]: for rerouting around boundary

STEP 6: ROUTING MODULE (app/core/routing.py)
Implement CLSP (Clustered Layered Shortest Path):

class AirspaceGraph:
  Build 100m grid waypoint graph over Pune bounds (18.45-18.65 lat, 73.75-73.95 lon)
  ~200 nodes, adjacency list with haversine weights
  Cluster nodes into 5km×5km squares (~16 clusters)
  apply_no_fly_zones(): remove/block edges whose midpoints fall inside NFZ polygons using Shapely
  get_nearest_node(lat,lon)->NodeID: find closest unblocked graph node
  Pre-build on startup, save to data/airspace/pune_graph.json, load if exists

def clsp_shortest_path(graph, src_latlon, dst_latlon) -> Route:
  """
  Phase 1 — Cluster routing (coarse BFS between cluster representatives):
    Map src/dst to clusters. BFS between clusters avoiding NFZ-blocked clusters.
  Phase 2 — Node routing (fine, limited relaxation within cluster chain):
    frontier = {src_node}
    dist = {src_node: 0}, prev = {}
    For each cluster in chain:
      new_frontier = {}
      For node in frontier (process by dist, not full sort):
        For (neighbor, weight) in graph.edges[node]:
          If neighbor in current_cluster OR adjacent_cluster:
            relax(neighbor, dist[node]+weight)
            new_frontier.add(neighbor)
      frontier = new_frontier  # frontier shrinking
  Phase 3 — Reconstruct path. If dst_node unreachable, route via NFZ perimeter.
  Return Route(waypoints, total_distance_m, no_fly_zones_avoided, cluster_path, computation_ms)
  """
  [IMPLEMENT THE FULL ALGORITHM - no stubs]

STEP 7: CAMERA MODULES (app/core/)
camera_rtsp.py — class RTSPCamera:
  __init__(rtsp_url, cam_id, zone_id)
  connect(): cv2.VideoCapture, retry 5x exponential backoff
  get_frame()->Optional[np.ndarray]: thread-safe, resize 640×360
  is_connected()->bool
  get_fps()->float
  run_loop(): background thread updating self._latest_frame

camera_video.py — class VideoFeedCamera:
  __init__(video_path, cam_id, zone_id)
  Same interface as RTSPCamera. Loop video on end. Pace at 10 FPS.

camera_manager.py — class CameraManager:
  cameras: Dict[str, Union[RTSPCamera, VideoFeedCamera]]
  Initialize 8 cameras from DB seed data on startup
  CAM-01: RTSPCamera from RTSP_URL env var
  CAM-02 to CAM-08: VideoFeedCamera from data/feeds/cam0X_*.mp4
  get_frame(cam_id)->Optional[np.ndarray]
  get_all_statuses()->List[CameraStatus]

STEP 8: DETECTION ENGINE (app/core/detection.py)
class MultiModelDetector:
  model: YOLO loaded from YOLO_MODEL_PATH
  SEVERITY_WEIGHTS = {crowd_anomaly:1.0, fight_detection:1.4, person_down:1.5, weapon_detect:2.0, suspicious_behavior:1.2}
  dwell_tracker: Dict[cam_id, Dict[person_track_id, int]] for suspicious behavior

  detect_all(frame, cam_id, zone_polygon) -> DetectionResult:
    Run YOLO11n inference.
    persons = [d for d in detections if d.class=='person' and d.conf>0.5]
    Run all 5 checks:
      crowd: count persons in zone polygon > 0
      fight: check pairs with IoU>0.3 AND opposing velocity (use centroid movement between frames)
      person_down: any person bbox aspect_ratio < 0.5 for 3+ frames
      weapon: YOLO detections with class in [knife,gun,bat] and conf>0.7
      suspicious: person in zone > 120 seconds using dwell_tracker
    Return DetectionResult(cam_id, zone_id, persons_count, anomaly_flags, detections, processing_ms)

  draw_annotated_frame(frame, detections, anomaly_flags) -> np.ndarray:
    Draw green bboxes + class labels + anomaly warning text overlay

  encode_mjpeg(frame, quality=80) -> bytes: cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])

STEP 9: BASELINE ENGINE (app/core/baseline.py)
class BaselineEngine:
  Load zone_baselines from DB on startup

  calculate(zone_id, current_count, anomaly_type) -> BaselineResult:
    hour = datetime.now().hour
    lambda_val = get_baseline_mean(zone_id, hour)  # from DB, default 5.0 if missing
    z_score = (current_count - lambda_val) / max(sqrt(lambda_val), 0.01)
    anomaly_score = float(1 - poisson.cdf(current_count, mu=max(lambda_val, 0.01)))
    severity = anomaly_score if current_count > lambda_val else 0.0
    final_severity = min(1.0, severity * SEVERITY_WEIGHTS[anomaly_type])
    return BaselineResult(zone_id, current_count, lambda_val, z_score, anomaly_score, final_severity)

  update_baseline(zone_id, hour, new_count): Welford online update to DB every 100 samples

STEP 10: DRONE SIMULATOR (app/core/drone_simulator.py)
Manages 4 drones in memory (DR-01 to DR-04) with home bases seeded from DB.

update_positions(): Called every 500ms via background task.
  For each EN_ROUTE/REROUTING drone:
    Move along current_route waypoints at speed_ms (15 m/s).
    Advance position: calculate meters to move in 500ms = 15*0.5 = 7.5m.
    If distance_remaining < 15m: transition to HOVERING. Start 30s hover timer.
  For HOVERING: count down hover timer. After 30s: transition to RETURNING.
  For RETURNING: move toward home_base. On arrival: transition to IDLE, restore battery.
  Battery drain: 0.05% per second flying. Restore 1% per second when IDLE.
  If battery < 20%: force RETURNING regardless of status. Emit battery_critical event.

score_drone(drone, alert_location) -> float: eta*0.7 + (1-battery/100)*0.3

select_drone_pair(alert) -> Tuple[Optional[Drone], Optional[Drone]]:
  Available = IDLE or (EN_ROUTE with can_be_reassigned=True and battery>30)
  Score all available. Return top 2. Flag PARTIAL_RESPONSE if only 1.

STEP 11: PRIORITY QUEUE (app/core/priority_queue.py)
class DroneDispatchQueue:
  queue: List of QueueItem(neg_score, created_at, alert, primary_drone, secondary_drone)

  push(alert, primary, secondary): heapq.heappush
  
  re_evaluate_every_500ms():
    For each EN_ROUTE/REROUTING drone:
      Update drone.eta_seconds based on current position
      Check all unassigned/lower-priority alerts:
        should_reallocate(drone, current_alert, candidate_alert):
          IF (candidate.severity - current.severity) > 0.15
             AND drone.eta_seconds > 30
             AND drone.battery > 30
             AND drone.status != HOVERING:
            return True
          IF candidate.anomaly_type in [weapon_detect, person_down] AND drone.eta > 10:
            return True
        If yes: reallocate(drone, new_alert). Log to reallocation_log table.
    
    Assign IDLE drones to highest-priority unassigned alerts.
    Decay alert severity: severity *= 0.995 per cycle (time decay).

STEP 12: GEMINI SERVICE (app/services/gemini_service.py)
import google.generativeai as genai
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

class GeminiDecisionEngine:
  async triage_alert(alert, zone_history) -> TriageDecision:
    Prompt: give zone history, anomaly type, severity, time. Ask for JSON:
      {action: DISPATCH|MONITOR|DISMISS, confidence: 0-1, reasoning: str, priority_override: null|float}
    Parse response as JSON. Fallback if parse fails: DISPATCH if severity>0.7 else MONITOR.
    
  async filter_false_positive(cam_id, anomaly_type, score) -> float:
    Returns 0.0-1.0 probability it's a real incident.
    
  async predict_risk_zones(heatmap_data, current_hour) -> List[RiskPrediction]:
    Send zone incident counts by hour. Return predicted risk zones for next 2 hours.
    
  async generate_dispatch_report(alert, drones) -> str:
    Returns 2-sentence human-readable incident summary for dashboard.

Rate limiting: max 10 calls/minute. Cache responses for same zone+hour for 60s.

STEP 13: ALERT MANAGER (app/services/alert_manager.py)
class AlertManager:
  pending_sos: Dict[sos_id, asyncio.Task]  # countdown timers

  async create_from_detection(cam_id, zone_id, detection_result, baseline_result) -> Optional[Alert]:
    If baseline_result.final_severity < 0.4: return None  # below threshold
    Gemini triage (async). If action == DISMISS: return None.
    Generate alert_id = f"AL-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{zone_id}"
    Select drone pair.
    Compute routes for both drones via CLSP.
    Save alert to DB. Save missions to DB.
    Dispatch drones (update drone states).
    Add to priority queue.
    Save to heatmap_events table.
    Emit alert_created WebSocket event.
    Return alert.

  async create_from_sos(sos_data) -> SOSEvent:
    Save SOS to DB with status=PENDING.
    Emit sos_received WebSocket event.
    Start 30s countdown task.
    Return sos_event.

  async sos_countdown(sos_id):
    For each second from 30 to 0:
      Emit sos_countdown WebSocket event with seconds_remaining.
      await asyncio.sleep(1)
      Check if SOS status changed to CANCELLED (from /sos/{id}/cancel call).
      If cancelled: return.
    # Buffer expired, auto-dispatch
    Create alert from SOS location with severity=0.90.
    Update SOS status to DISPATCHED.
    Emit sos_dispatched WebSocket event.

  async cancel_sos(sos_id, reason) -> bool:
    If SOS not in pending_sos or already dispatched: return False.
    Cancel asyncio task. Update DB. Emit sos_cancelled event. Return True.

  async resolve_alert(alert_id, resolution) -> Alert:
    Update DB. Update drone status to RETURNING. Emit alert_updated event.

STEP 14: WEBSOCKET SERVICE (app/services/websocket.py)
Use python-socketio AsyncServer with cors_allowed_origins='*'.
Mount on FastAPI via socketio.ASGIApp.
Rooms: 'all_clients', 'qgc_overlay', per-camera rooms 'cam_{cam_id}'.

emit_drone_update(drones: List[DroneState]): emit 'drone_update' to 'all_clients'
emit_alert_created(alert: Alert): emit 'alert_created' to 'all_clients'
emit_alert_updated(alert): emit 'alert_updated' to 'all_clients'
emit_baseline_update(zones): emit 'baseline_update' to 'all_clients'
emit_heatmap_update(heatmap): emit 'heatmap_update' to 'all_clients'
emit_sos_received(sos): emit 'sos_received' to 'all_clients'
emit_sos_countdown(sos_id, seconds): emit 'sos_countdown' to 'all_clients'
emit_sos_dispatched(sos, alert): emit 'sos_dispatched' to 'all_clients'
emit_drone_reallocated(event): emit 'drone_reallocated' to 'all_clients'
emit_camera_offline(cam_id): emit 'camera_offline' to 'all_clients'
emit_detection_stream(cam_id, result): emit 'detection_stream' to room 'cam_{cam_id}' only

@sio.event async on_connect(sid, environ): join 'all_clients' room
@sio.on('subscribe_camera') async on_subscribe_camera(sid, data): join 'cam_{cam_id}' room

On reconnect: send full state snapshot (all drones, active alerts, latest baselines).

STEP 15: BACKGROUND TASKS (app/services/background_tasks.py)
async detection_loop():  # Every 100ms per camera
  For each of 8 cameras:
    frame = camera_manager.get_frame(cam_id)
    If frame None: continue
    zone = get_zone_for_camera(cam_id)
    result = detector.detect_all(frame, cam_id, zone.polygon)
    baseline_result = baseline_engine.calculate(zone.zone_id, result.persons_count, primary_anomaly_type)
    If baseline_result.final_severity > 0.4:
      alert = await alert_manager.create_from_detection(...)  # handles dedup: skip if same zone has active alert < 30s old
  # Store latest annotated frame per camera for MJPEG stream

async priority_queue_loop():  # Every 500ms
  priority_queue.re_evaluate_every_500ms()
  drone_simulator.update_positions()
  drones = drone_simulator.get_all_drones()
  await ws.emit_drone_update(drones)

async baseline_broadcast_loop():  # Every 5 seconds
  zones_data = baseline_engine.get_all_zone_stats()
  await ws.emit_baseline_update(zones_data)

async heatmap_loop():  # Every 30 seconds
  heatmap = heatmap_engine.compute_realtime_heatmap()
  predictions = await gemini.predict_risk_zones(heatmap, datetime.now().hour)
  await ws.emit_heatmap_update({...heatmap, predictions})

STEP 16: HEATMAP ENGINE (app/core/heatmap.py)
class HeatmapEngine:
  compute_realtime_heatmap() -> HeatmapData:
    events = db.get_heatmap_events(hours=168)  # last 7 days
    If no events: return empty heatmap.
    Grid: 0.002° resolution over Pune bounds.
    KDE: Gaussian kernel bandwidth=0.005° (~500m).
    Weight each event: w = severity × exp(-age_hours / 24)  # exponential decay
    intensity[grid_point] = sum(w × gaussian(dist)) / normalizer
    hotspots = grid points with intensity > 0.7 mapped back to zones.
    Return HeatmapData(points=non-zero-grid-points, hotspots, computed_at)
    Cache result in memory. Only recompute every 30s.

STEP 17: ALL REST API ROUTES

app/api/health.py:
  GET /health -> full system health JSON (see spec)
  GET /metrics -> cpu%, memory, per-camera fps, queue depth

app/api/cameras.py:
  GET /cameras -> all 8 camera statuses
  GET /cameras/{cam_id}/stream -> StreamingResponse MJPEG from latest annotated frame buffer
  GET /cameras/{cam_id}/snapshot -> Response(latest_jpeg, media_type='image/jpeg')
  GET /cameras/{cam_id}/detections -> latest DetectionResult for camera

app/api/zones.py:
  GET /zones -> all zones with current stats
  GET /zones/{zone_id}/baseline -> hourly baseline profile

app/api/alerts.py:
  GET /alerts -> list alerts (query: status, zone_id, limit, offset)
  POST /alerts/manual -> create manual alert, trigger dispatch
  GET /alerts/{alert_id} -> single alert detail
  PATCH /alerts/{alert_id}/resolve -> resolve alert

app/api/drones.py:
  GET /drones -> all drone states with full metrics
  GET /drones/{drone_id} -> single drone
  POST /drones/{drone_id}/dispatch -> manual dispatch to lat/lon
  POST /drones/{drone_id}/rtl -> return to launch
  POST /drones/{drone_id}/reroute -> reroute to new target
  GET /drones/{drone_id}/history -> past missions

app/api/routes_api.py:
  POST /routes/plan -> compute CLSP route, return waypoints + stats
  GET /routes/no_fly_zones -> active NFZ list

app/api/sos.py:
  POST /sos -> create SOS, start 30s buffer, return sos_id + deadline
  POST /sos/{sos_id}/cancel -> cancel SOS if within buffer
  GET /sos -> list SOS events (query: status, limit)
  GET /sos/{sos_id} -> single SOS detail

app/api/heatmap.py:
  GET /heatmap -> current KDE heatmap + hotspots
  GET /heatmap/predict -> Gemini risk predictions for next 2h
  GET /heatmap/history -> historical incident counts (query: zone_id, days)

app/api/baseline.py:
  GET /baseline/stats -> current anomaly scores all zones

app/api/qgc.py:
  GET /qgc/fleet_status -> compact fleet summary for H12 overlay
  POST /qgc/dispatch -> dispatch from H12
  POST /qgc/reroute/{drone_id} -> reroute from H12
  POST /qgc/rtl/{drone_id} -> RTL from H12
  POST /qgc/emergency_land/{drone_id} -> emergency land

STEP 18: MAIN APP (app/main.py)
FastAPI app with CORS allow_origins=["*"].
Include all routers with correct prefixes.
Mount socketio ASGIApp at "/".
@app.on_event("startup"):
  Init DB + run migrations.
  Seed initial data (8 cameras, 8 zones, 4 drones, baselines).
  Build airspace graph (load from file if exists, else compute and save).
  Load no-fly zones.
  Load YOLO model.
  Start all background tasks via asyncio.create_task().
  Log "SkyGuard V2 ready — 8 cameras, 4 drones, 2 NFZs loaded"
Run: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

=== DATA SEED VALUES ===
8 Cameras + Zones:
CAM-01/Zone-A: MG Road (18.5204, 73.8567) polygon 200m square centered there
CAM-02/Zone-B: Shivajinagar (18.5308, 73.8474)
CAM-03/Zone-C: FC Road (18.5286, 73.8395)
CAM-04/Zone-D: Koregaon Park (18.5362, 73.8939)
CAM-05/Zone-E: Hinjewadi (18.5913, 73.7390)
CAM-06/Zone-F: Kothrud (18.5074, 73.8077)
CAM-07/Zone-G: Hadapsar (18.4956, 73.9259)
CAM-08/Zone-H: Wakad (18.5989, 73.7601)

4 Drones (home bases = zone centroids):
DR-01: Zone-A (18.5204, 73.8567)
DR-02: Zone-B (18.5308, 73.8474)
DR-03: Zone-D (18.5362, 73.8939)
DR-04: Zone-E (18.5913, 73.7390)

2 No-Fly Zones (build polygon from center + radius):
NFZ-01: Pune Airport (18.5822, 73.9197) radius 2000m
NFZ-02: Military Cantonment (18.5200, 73.8700) radius 1500m

Zone baselines: for each zone×hour, use realistic Poisson means:
  Night (0-5h): mean=2-3, std=1.5
  Morning peak (7-10h): mean=12-18, std=3-5
  Afternoon (11-16h): mean=7-10, std=2-3
  Evening peak (17-21h): mean=15-25, std=4-6
  Night (22-23h): mean=3-5, std=2

Video feed files (data/feeds/): If mp4 files don't exist, generate synthetic colored test video
  using OpenCV VideoWriter with zone name text overlay so demo still works.
  def generate_test_video(path, zone_name, duration_s=60): write 640×360 colored frames.

=== CRITICAL IMPLEMENTATION RULES ===
1. All DB operations: async with aiosqlite. Never block event loop.
2. Camera frames: use threading.Lock() for thread-safe buffer access.
3. Detection loop: one asyncio task per camera running concurrently.
4. Alert deduplication: don't create new alert for same zone if active alert < 30s old.
5. CLSP routing: if graph not pre-built, compute at startup and cache to JSON file.
6. Gemini calls: always wrap in try/except. Fallback to rule-based if API fails.
7. SOS countdown: use asyncio.Task stored in dict. Cancel task on /sos/cancel.
8. Drone position update: 500ms interval. Move 7.5m per tick at 15 m/s.
9. Battery drain: 0.05% per second flying. 1% per second when IDLE/charging.
10. WebSocket: emit drone_update + re-evaluate queue every 500ms in same loop.
11. MJPEG stream: use async generator with yield frame bytes. No buffering.
12. All timestamps: UTC ISO 8601 format.
13. Alert IDs: f"AL-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{zone_id}-{counter:03d}"
14. Mission IDs: f"MSN-{drone_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
15. Severity decimal: always round to 2 places before storing/emitting.

=== WEBSOCKET EVENTS SUMMARY ===
Emitted by backend every 500ms: drone_update
Emitted by backend every 5s: baseline_update
Emitted by backend every 30s: heatmap_update
Emitted by backend on event: alert_created, alert_updated, sos_received, sos_countdown,
  sos_dispatched, drone_reallocated, camera_offline, camera_online, detection_stream, system_error
Received from client: subscribe_camera, request_dispatch, request_reroute

=== FILES TO CREATE IN ORDER ===
requirements.txt → .env → app/utils/logger.py → app/utils/haversine.py → app/utils/geo_utils.py
→ app/db/database.py → app/db/schemas.sql → app/db/crud.py → app/db/seed.py
→ app/models/*.py → app/core/geofence.py → app/core/routing.py → app/core/camera_rtsp.py
→ app/core/camera_video.py → app/core/camera_manager.py → app/core/detection.py
→ app/core/baseline.py → app/core/drone_simulator.py → app/core/priority_queue.py
→ app/core/heatmap.py → app/services/websocket.py → app/services/gemini_service.py
→ app/services/alert_manager.py → app/services/background_tasks.py
→ app/api/health.py → app/api/cameras.py → app/api/zones.py → app/api/alerts.py
→ app/api/drones.py → app/api/routes_api.py → app/api/sos.py → app/api/heatmap.py
→ app/api/baseline.py → app/api/qgc.py → app/config.py → app/main.py
→ scripts/seed_database.py → scripts/build_airspace_graph.py → Dockerfile

=== DOCKERFILE ===
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Pre-download YOLO model at build time
RUN python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"
COPY . .
RUN mkdir -p logs data/feeds
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

Build and deliver complete, working Python code for every file. No stubs. No TODOs.
Test each module is importable before moving to next step.
```

---

## SUPPLEMENTARY PROMPTS (Use for individual features if context is limited)

---

### PROMPT A — CLSP Routing Algorithm Only

```
Implement the Clustered Layered Shortest Path (CLSP) algorithm in Python for drone routing over Pune airspace.

Requirements:
- Build a waypoint graph: 100m grid over Pune (18.45-18.65 lat, 73.75-73.95 lon), ~200 nodes
- Adjacency list with Haversine edge weights
- Cluster nodes into 5km² squares (~16 clusters), one representative per cluster
- No-fly zone enforcement: remove edges whose midpoints fall in NFZ polygons (use Shapely)
- CLSP: Phase 1 = coarse BFS between cluster representatives. Phase 2 = fine routing within cluster chain using frontier shrinking + limited relaxation (only relax edges within current + adjacent clusters, do NOT sort all nodes — process frontier only)
- Return: List[LatLon] waypoints, total_distance_m, computation_ms, nfz_avoided list
- If destination unreachable (fully surrounded by NFZ): route via NFZ perimeter boundary nodes
- Serialize graph to JSON and cache. Load from cache on subsequent calls.
- Include unit tests: route from Zone-A to Zone-D, route avoiding NFZ-01, route with no path (return perimeter route)
Implement complete working code.
```

---

### PROMPT B — Priority Queue & Reallocation Engine Only

```
Implement DroneDispatchQueue for SkyGuard V2 drone dispatch system in Python.

Data models (define these):
DroneStatus: IDLE | EN_ROUTE | REROUTING | HOVERING | RETURNING
DroneState: id, position(lat,lon), battery(int), status, target_zone, eta_seconds, assigned_alert_id, can_be_reassigned
Alert: alert_id, zone_id, anomaly_type, severity(float 0-1), location(lat,lon), primary_drone_id, secondary_drone_id

Implement DroneDispatchQueue with:
1. push(alert, primary_drone, secondary_drone): add to heap, score = severity / (1 + eta_normalized)
2. re_evaluate(): called every 500ms
   - Update all drone ETAs based on position interpolation (15 m/s)
   - Decay alert severity by *=0.995 per call
   - For each EN_ROUTE/REROUTING drone check if should_reallocate():
     * (new_severity - current_severity) > 0.15 AND eta > 30s AND battery > 30 AND not HOVERING
     * OR anomaly_type in [weapon_detect, person_down] AND eta > 10s
   - If reallocate: update drone target, compute new ETA, log to reallocation_log, emit event
   - Assign IDLE drones to highest-priority unassigned alerts
3. select_drone_pair(alert, drones): score = eta*0.7 + (1-battery/100)*0.3, return top 2
4. get_queue_snapshot(): return sorted list for API response

Include edge cases:
- All drones HOVERING: queue alert as PENDING
- Battery < 20% mid-mission: force RETURNING, reassign mission
- Two simultaneous equal-severity alerts: assign separate drones
Write complete working Python with type hints.
```

---

### PROMPT C — SOS System Only

```
Implement the SOS subsystem for SkyGuard V2 FastAPI backend.

Flow:
POST /sos → Save to DB (status=PENDING) → Emit sos_received WebSocket → Start 30s asyncio countdown task
  During countdown: emit sos_countdown every second with seconds_remaining
  POST /sos/{id}/cancel within 30s: cancel task, update status=CANCELLED, emit sos_cancelled
  If 30s expires without cancel: create Alert (severity=0.90), dispatch 2 drones via priority queue,
    update status=DISPATCHED, emit sos_dispatched with drone assignments

Data models:
SOSCreate: sender_id, message, lat, lon, location_type[gps|zone|manual], zone_id(optional)
SOSResponse: sos_id, status, confirmation_deadline, buffer_seconds, message

Implement:
- SQLite table: sos_events (sos_id, sender_id, message, lat, lon, location_type, zone_id,
  status, confirmed_at, cancelled_at, cancel_reason, alert_id, created_at)
- AlertManager.create_from_sos(sos_data) -> SOSEvent
- AlertManager.sos_countdown(sos_id) async task
- AlertManager.cancel_sos(sos_id, reason) -> bool
- FastAPI router: POST /sos, POST /sos/{id}/cancel, GET /sos, GET /sos/{id}
- All WebSocket events emitted correctly
- Edge case: cancel after buffer expires returns 409 Conflict
- Edge case: duplicate SOS from same sender within 60s returns existing SOS
Write complete working code.
```

---

### PROMPT D — Heatmap Engine Only

```
Implement KDE-based predictive heatmap for SkyGuard V2 in Python.

HeatmapEngine class:
Input: heatmap_events table rows: (event_id, lat, lon, zone_id, anomaly_type, severity, hour, day_of_week, timestamp)

compute_realtime_heatmap() -> HeatmapData:
  - Load last 168 hours of events from SQLite
  - Build grid: 0.002° resolution over Pune (18.45-18.65, 73.75-73.95) → ~10000 grid points
  - Weight per event: w = severity × exp(-age_hours / 24)  [exponential decay, half-life 24h]
  - Gaussian kernel: σ = 0.005° (~500m). For each grid point: intensity = Σ(w × gaussian(dist))
  - Normalize intensity to 0-1 range
  - Return only non-zero points (intensity > 0.01) to save bandwidth
  - Cache result; only recompute if >30s since last computation

get_hotspots(threshold=0.7) -> List[Hotspot]:
  - Find grid points above threshold, cluster them, map to nearest zone

predict_next_incident(hour, day) -> List[RiskZone]:
  - Filter events from same hour±2 and same day_of_week from historical data
  - Score each zone by weighted incident density
  - Return top 3 zones with risk_score 0-1

Gemini integration in predict_next_incident:
  - Pass zone scores to Gemini: "Based on historical patterns [data], predict risk for hour [h]"
  - Parse JSON response: [{zone_id, risk_score, reasoning, recommended_action}]
  - Fallback to rule-based if Gemini fails

FastAPI endpoints:
  GET /heatmap → HeatmapData
  GET /heatmap/predict?hour=16 → risk predictions
  GET /heatmap/history?zone_id=A&days=7 → historical counts

Write complete working code with numpy/scipy for KDE.
```

---

### PROMPT E — H12 QGroundControl Overlay

```
Build the Skydroid H12 QGroundControl overlay for SkyGuard V2.

This is a single HTML file (qgc_overlay.html) served from the FastAPI backend at GET /qgc/overlay.
It runs as a WebView overlaid on QGroundControl on the Skydroid H12 (5.5" 1920×1080, Chrome Android).

Layout (semi-transparent dark overlay, vertical scroll):
- Header: "SkyGuard Command" + connection status dot
- Incident Panel: list of active alerts with [Dispatch] button each
- Fleet Panel: 4 drones, each showing: status badge, battery bar, ETA countdown, [RTL] button
- Quick Actions: [Manual Alert] [All RTL] [Emergency Land All]
- Connection: connects to ws://[BACKEND_IP]:8000 via Socket.IO CDN

Functionality:
- On connect: fetch /drones and /alerts, render state
- On drone_update WS event: update drone cards live (battery, eta, status, position)
- On alert_created WS event: add to incident panel with severity color (red>0.7, yellow>0.4)
- [Dispatch] button: POST /qgc/dispatch {alert_id, drone_ids: auto-select best 2}
- [RTL] button: POST /qgc/rtl/{drone_id}
- [Manual Alert] button: shows simple form (zone dropdown, anomaly type dropdown) → POST /alerts/manual
- Backend IP: read from URL param ?backend=192.168.1.100:8000, default to localhost:8000

Design: Dark theme (#0a0a0a bg, #1a1a2e panels), blue accents (#4361ee), red alerts (#ef233c),
  semi-transparent panels (rgba 0.85 opacity), large touch targets (min 48px), no external CSS deps.

Serve this file from FastAPI:
  GET /qgc/overlay → FileResponse('static/qgc_overlay.html')

Write complete single-file HTML with embedded CSS+JS using Socket.IO CDN.
```

---

## IMPLEMENTATION CHECKLIST

Copy this checklist and track progress as you build:

```
CORE INFRASTRUCTURE
[ ] requirements.txt + .env
[ ] DB layer (database.py, schemas.sql, crud.py, seed.py)
[ ] Pydantic models (all 7 model files)
[ ] Utility modules (haversine, geo_utils, logger)

DETECTION PIPELINE
[ ] Geofence module (2 NFZs loaded)
[ ] CLSP routing algorithm (with tests)
[ ] RTSP camera handler (auto-reconnect)
[ ] Video feed camera handler (looping)
[ ] Camera manager (8 cameras orchestrated)
[ ] Multi-model detector (5 anomaly types)
[ ] Baseline engine (Poisson scoring)

DRONE MANAGEMENT
[ ] Drone simulator (position interpolation)
[ ] Priority queue (heap + reallocation)
[ ] Alert manager (creation + SOS + lifecycle)

AI & ANALYTICS
[ ] Gemini service (triage + prediction + fallback)
[ ] Heatmap engine (KDE + predictions)

REAL-TIME LAYER
[ ] WebSocket service (all 14 events)
[ ] Background tasks (all 5 loops)

REST API (18 endpoints)
[ ] /health, /metrics
[ ] /cameras (4 endpoints)
[ ] /zones (2 endpoints)
[ ] /alerts (4 endpoints)
[ ] /drones (5 endpoints)
[ ] /routes (2 endpoints)
[ ] /sos (4 endpoints)
[ ] /heatmap (3 endpoints)
[ ] /baseline (1 endpoint)
[ ] /qgc (5 endpoints)

INTEGRATION
[ ] app/main.py (startup, routing, task launch)
[ ] Dockerfile
[ ] QGC overlay HTML

VERIFICATION
[ ] Server starts without errors
[ ] /health returns 200
[ ] /cameras returns 8 cameras
[ ] /drones returns 4 drones
[ ] WebSocket connects and emits drone_update every 500ms
[ ] POST /alerts/manual creates alert, dispatches 2 drones
[ ] POST /sos creates pending SOS, counts down 30s
[ ] GET /heatmap returns intensity points
[ ] RTSP stream loads at /cameras/CAM-01/stream
```

---

*SkyGuard V2 Build Prompt | Version 2.0 | Pune Police Drone Office | April 2026*
