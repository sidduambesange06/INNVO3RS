// API Configuration
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  ENDPOINTS: {
    // Health & Metrics
    HEALTH: '/health',
    METRICS: '/metrics',
    
    // Cameras
    CAMERAS: '/cameras',
    CAMERA_STREAM: (camId: string) => `/cameras/${camId}/stream`,
    CAMERA_SNAPSHOT: (camId: string) => `/cameras/${camId}/snapshot`,
    CAMERA_DETECTIONS: (camId: string) => `/cameras/${camId}/detections`,
    
    // Zones
    ZONES: '/zones',
    ZONE_BASELINE: (zoneId: string) => `/zones/${zoneId}/baseline`,
    
    // Alerts
    ALERTS: '/alerts',
    ALERT_MANUAL: '/alerts/manual',
    ALERT_DETAIL: (alertId: string) => `/alerts/${alertId}`,
    ALERT_RESOLVE: (alertId: string) => `/alerts/${alertId}/resolve`,
    
    // Drones
    DRONES: '/drones',
    DRONE_DETAIL: (droneId: string) => `/drones/${droneId}`,
    DRONE_DISPATCH: (droneId: string) => `/drones/${droneId}/dispatch`,
    DRONE_RTL: (droneId: string) => `/drones/${droneId}/rtl`,
    DRONE_REROUTE: (droneId: string) => `/drones/${droneId}/reroute`,
    DRONE_HISTORY: (droneId: string) => `/drones/${droneId}/history`,
    
    // Routes
    ROUTES_PLAN: '/routes/plan',
    NO_FLY_ZONES: '/routes/no_fly_zones',
    
    // SOS
    SOS: '/sos',
    SOS_DETAIL: (sosId: string) => `/sos/${sosId}`,
    SOS_CANCEL: (sosId: string) => `/sos/${sosId}/cancel`,
    
    // Heatmap
    HEATMAP: '/heatmap',
    HEATMAP_PREDICT: '/heatmap/predict',
    HEATMAP_HISTORY: '/heatmap/history',
    
    // Baseline
    BASELINE_STATS: '/baseline/stats',
    
    // QGC
    QGC_FLEET: '/qgc/fleet_status',
    QGC_DISPATCH: '/qgc/dispatch',
    QGC_REROUTE: (droneId: string) => `/qgc/reroute/${droneId}`,
    QGC_RTL: (droneId: string) => `/qgc/rtl/${droneId}`,
    QGC_EMERGENCY: (droneId: string) => `/qgc/emergency_land/${droneId}`,
  }
} as const;
