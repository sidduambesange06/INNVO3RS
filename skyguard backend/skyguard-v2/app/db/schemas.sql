-- SkyGuard V2 — Database Schema
-- All tables for the complete system

CREATE TABLE IF NOT EXISTS cameras (
    cam_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('rtsp', 'video_feed')),
    source_url TEXT NOT NULL,
    zone_id TEXT,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    polygon_geojson TEXT,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS zones (
    zone_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cam_id TEXT REFERENCES cameras(cam_id),
    polygon_geojson TEXT,
    centroid_lat REAL NOT NULL,
    centroid_lon REAL NOT NULL,
    baseline_mean REAL DEFAULT 5.0,
    baseline_std REAL DEFAULT 2.0
);

CREATE TABLE IF NOT EXISTS zone_baselines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id TEXT NOT NULL REFERENCES zones(zone_id),
    hour INTEGER NOT NULL CHECK(hour >= 0 AND hour <= 23),
    day_of_week INTEGER NOT NULL CHECK(day_of_week >= 0 AND day_of_week <= 6),
    mean REAL NOT NULL DEFAULT 5.0,
    std_dev REAL NOT NULL DEFAULT 2.0,
    sample_count INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(zone_id, hour, day_of_week)
);

CREATE TABLE IF NOT EXISTS drones (
    drone_id TEXT PRIMARY KEY,
    home_lat REAL NOT NULL,
    home_lon REAL NOT NULL,
    current_lat REAL NOT NULL,
    current_lon REAL NOT NULL,
    altitude REAL DEFAULT 50.0,
    battery INTEGER DEFAULT 100,
    status TEXT DEFAULT 'IDLE' CHECK(status IN ('IDLE','EN_ROUTE','REROUTING','HOVERING','RETURNING')),
    speed_ms REAL DEFAULT 15.0,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    zone_id TEXT REFERENCES zones(zone_id),
    cam_id TEXT REFERENCES cameras(cam_id),
    anomaly_type TEXT NOT NULL,
    severity REAL NOT NULL,
    current_count INTEGER DEFAULT 0,
    baseline_mean REAL DEFAULT 0.0,
    z_score REAL DEFAULT 0.0,
    location_lat REAL,
    location_lon REAL,
    primary_drone_id TEXT REFERENCES drones(drone_id),
    secondary_drone_id TEXT REFERENCES drones(drone_id),
    status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','RESOLVED','CANCELLED','PARTIAL_RESPONSE','ROUTE_BLOCKED')),
    gemini_action TEXT,
    gemini_confidence REAL,
    source TEXT DEFAULT 'camera' CHECK(source IN ('camera', 'sos', 'manual')),
    created_at TEXT DEFAULT (datetime('now')),
    dispatched_at TEXT,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS sos_events (
    sos_id TEXT PRIMARY KEY,
    sender_id TEXT NOT NULL,
    message TEXT,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    location_type TEXT DEFAULT 'gps' CHECK(location_type IN ('gps','zone','manual')),
    zone_id TEXT,
    status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING','CONFIRMED','CANCELLED','DISPATCHED')),
    confirmed_at TEXT,
    cancelled_at TEXT,
    cancel_reason TEXT,
    alert_id TEXT REFERENCES alerts(alert_id),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS missions (
    mission_id TEXT PRIMARY KEY,
    alert_id TEXT REFERENCES alerts(alert_id),
    drone_id TEXT REFERENCES drones(drone_id),
    role TEXT DEFAULT 'primary' CHECK(role IN ('primary','secondary')),
    route_waypoints TEXT,  -- JSON array of [lat,lon]
    no_fly_zones_avoided TEXT,  -- JSON array of NFZ ids
    algorithm TEXT DEFAULT 'CLSP',
    total_distance_m REAL DEFAULT 0.0,
    planned_eta_s REAL DEFAULT 0.0,
    actual_duration_s REAL,
    status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','COMPLETED','ABORTED','REROUTED')),
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS heatmap_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    zone_id TEXT,
    anomaly_type TEXT NOT NULL,
    severity REAL NOT NULL,
    hour INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    resolved INTEGER DEFAULT 0,
    timestamp TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reallocation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drone_id TEXT NOT NULL,
    from_alert_id TEXT,
    to_alert_id TEXT,
    reason TEXT,
    old_eta_s REAL,
    new_eta_s REAL,
    timestamp TEXT DEFAULT (datetime('now'))
);

-- Real-time detection storage tables
CREATE TABLE IF NOT EXISTS detections (
    detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cam_id TEXT NOT NULL REFERENCES cameras(cam_id),
    zone_id TEXT REFERENCES zones(zone_id),
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    class_name TEXT NOT NULL,
    confidence REAL NOT NULL,
    bbox_x1 REAL NOT NULL,
    bbox_y1 REAL NOT NULL,
    bbox_x2 REAL NOT NULL,
    bbox_y2 REAL NOT NULL,
    track_id INTEGER
);

CREATE TABLE IF NOT EXISTS anomaly_detections (
    anomaly_detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cam_id TEXT NOT NULL REFERENCES cameras(cam_id),
    zone_id TEXT REFERENCES zones(zone_id),
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    anomaly_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    description TEXT,
    persons_count INTEGER DEFAULT 0
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_alerts_zone ON alerts(zone_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_baselines_zone_hour ON zone_baselines(zone_id, hour);
CREATE INDEX IF NOT EXISTS idx_heatmap_time ON heatmap_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_heatmap_zone ON heatmap_events(zone_id);
CREATE INDEX IF NOT EXISTS idx_sos_status ON sos_events(status);
CREATE INDEX IF NOT EXISTS idx_missions_alert ON missions(alert_id);
CREATE INDEX IF NOT EXISTS idx_detections_cam_time ON detections(cam_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_detections_zone_time ON detections(zone_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_anomaly_detections_cam_time ON anomaly_detections(cam_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_anomaly_detections_type ON anomaly_detections(anomaly_type);
