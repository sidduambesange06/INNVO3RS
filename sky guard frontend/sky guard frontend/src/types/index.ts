export type DroneStatus =
  | 'IDLE' | 'EN_ROUTE' | 'HOVERING' | 'RETURNING' | 'CHARGING';

export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type CameraStatus = 'connected' | 'disconnected' | 'error';
export type SosStatus = 'PENDING' | 'CONFIRMED' | 'CANCELLED' | 'DISPATCHED';
export type AlertStatus = 'ACTIVE' | 'RESOLVED' | 'CANCELLED';

export interface Drone {
  drone_id: string;
  position: { lat: number; lon: number; alt: number };
  home_base: { lat: number; lon: number };
  battery: number;
  status: DroneStatus;
  target_zone: string | null;
  target_location: { lat: number; lon: number } | null;
  eta_seconds: number | null;
  speed_ms: number;
  distance_remaining_m: number | null;
  mission_id: string | null;
  assigned_alert_id: string | null;
  can_be_reassigned: boolean;
}

export interface Alert {
  alert_id: string;
  zone_id: string;
  zone_name: string;
  cam_id: string;
  anomaly_type: string;
  severity: number;
  current_count: number;
  baseline_mean: number;
  z_score: number;
  location: { lat: number; lon: number };
  primary_drone: string | null;
  secondary_drone: string | null;
  primary_eta: number | null;
  secondary_eta: number | null;
  status: AlertStatus;
  source: string;
  timestamp: string;
}

export interface Camera {
  cam_id: string;
  zone_id: string;
  type: string;
  status: CameraStatus;
  fps: number;
  resolution: string;
}

export interface Detection {
  cam_id: string;
  zone_id: string;
  persons_count: number;
  detections: Array<{
    bbox: number[];
    confidence: number;
    class: string;
    track_id: number;
  }>;
  anomaly_flags: Array<{
    type: string;
    confidence: number;
    description: string;
  }>;
  processing_ms: number;
}

export interface SosRequest {
  sos_id: string;
  sender_id: string;
  message: string;
  location: { lat: number; lon: number };
  location_type: string;
  zone_id: string | null;
  status: SosStatus;
  alert_id: string | null;
  created_at: string;
  confirmation_deadline?: string;
  buffer_seconds?: number;
}

export interface Zone {
  zone_id: string;
  name: string;
  cam_id: string;
  polygon: Array<[number, number]>;
  centroid_lat: number;
  centroid_lon: number;
  baseline_mean: number;
  baseline_std: number;
  current_stats: {
    zone_id: string;
    current: number;
    mean: number;
    std_dev: number;
    anomaly_score: number;
    severity: number;
  };
}

export interface HeatmapPoint {
  lat: number;
  lon: number;
  intensity: number;
}

export interface Hotspot {
  zone_id: string;
  zone_name: string;
  lat: number;
  lon: number;
  intensity: number;
  incident_count: number;
}

export interface AlertEvent {
  id: string;
  type: string;
  description: string;
  severity: Severity;
  source: string;
  timestamp: Date;
}

export interface ToastNotification {
  id: string;
  type: 'INCIDENT_DETECTED' | 'DRONE_DISPATCHED' | 'DRONE_REROUTED'
      | 'SOS_RECEIVED' | 'DRONE_ARRIVED' | 'NO_FLY_ZONE' | 'SYSTEM_ALERT';
  title: string;
  description: string;
}

export interface ActionModalPayload {
  modalType: 'DISPATCH' | 'REROUTE';
  droneId: string;
  droneName: string;
  // DISPATCH fields
  incidentId?: string;
  incidentType?: string;
  incidentSeverity?: Severity;
  incidentLocation?: string;
  // REROUTE fields
  fromIncidentId?: string;
  fromIncidentType?: string;
  fromSeverity?: Severity;
  toIncidentId?: string;
  toIncidentType?: string;
  toSeverity?: Severity;
  toLocation?: string;
  aiRecommendation?: string;
  estimatedEta?: number;
}
