import { API_CONFIG } from '../config/api';

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_CONFIG.BASE_URL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Health & Metrics
  async getHealth() {
    return this.request(API_CONFIG.ENDPOINTS.HEALTH);
  }

  async getMetrics() {
    return this.request(API_CONFIG.ENDPOINTS.METRICS);
  }

  // Cameras
  async getCameras() {
    return this.request(API_CONFIG.ENDPOINTS.CAMERAS);
  }

  async getCameraDetections(camId: string) {
    return this.request(API_CONFIG.ENDPOINTS.CAMERA_DETECTIONS(camId));
  }

  getCameraStreamUrl(camId: string): string {
    return `${this.baseUrl}${API_CONFIG.ENDPOINTS.CAMERA_STREAM(camId)}`;
  }

  getCameraSnapshotUrl(camId: string): string {
    return `${this.baseUrl}${API_CONFIG.ENDPOINTS.CAMERA_SNAPSHOT(camId)}`;
  }

  // Zones
  async getZones() {
    return this.request(API_CONFIG.ENDPOINTS.ZONES);
  }

  async getZoneBaseline(zoneId: string) {
    return this.request(API_CONFIG.ENDPOINTS.ZONE_BASELINE(zoneId));
  }

  // Alerts
  async getAlerts(params?: { status?: string; zone_id?: string; limit?: number; offset?: number }) {
    const query = new URLSearchParams(params as any).toString();
    return this.request(`${API_CONFIG.ENDPOINTS.ALERTS}${query ? `?${query}` : ''}`);
  }

  async createManualAlert(data: { zone_id: string; anomaly_type: string; severity: number }) {
    return this.request(API_CONFIG.ENDPOINTS.ALERT_MANUAL, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getAlert(alertId: string) {
    return this.request(API_CONFIG.ENDPOINTS.ALERT_DETAIL(alertId));
  }

  async resolveAlert(alertId: string) {
    return this.request(API_CONFIG.ENDPOINTS.ALERT_RESOLVE(alertId), {
      method: 'PATCH',
    });
  }

  // Drones
  async getDrones() {
    return this.request(API_CONFIG.ENDPOINTS.DRONES);
  }

  async getDrone(droneId: string) {
    return this.request(API_CONFIG.ENDPOINTS.DRONE_DETAIL(droneId));
  }

  async dispatchDrone(droneId: string, data: { lat: number; lon: number; zone_id?: string }) {
    return this.request(API_CONFIG.ENDPOINTS.DRONE_DISPATCH(droneId), {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async returnDroneToLaunch(droneId: string) {
    return this.request(API_CONFIG.ENDPOINTS.DRONE_RTL(droneId), {
      method: 'POST',
    });
  }

  async rerouteDrone(droneId: string, data: { lat: number; lon: number; alert_id?: string }) {
    return this.request(API_CONFIG.ENDPOINTS.DRONE_REROUTE(droneId), {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getDroneHistory(droneId: string) {
    return this.request(API_CONFIG.ENDPOINTS.DRONE_HISTORY(droneId));
  }

  // Routes
  async planRoute(data: { src_lat: number; src_lon: number; dst_lat: number; dst_lon: number }) {
    return this.request(API_CONFIG.ENDPOINTS.ROUTES_PLAN, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getNoFlyZones() {
    return this.request(API_CONFIG.ENDPOINTS.NO_FLY_ZONES);
  }

  // SOS
  async getSosEvents(params?: { status?: string; limit?: number }) {
    const query = new URLSearchParams(params as any).toString();
    return this.request(`${API_CONFIG.ENDPOINTS.SOS}${query ? `?${query}` : ''}`);
  }

  async createSos(data: {
    sender_id: string;
    message: string;
    lat: number;
    lon: number;
    location_type: string;
    zone_id?: string;
  }) {
    return this.request(API_CONFIG.ENDPOINTS.SOS, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getSos(sosId: string) {
    return this.request(API_CONFIG.ENDPOINTS.SOS_DETAIL(sosId));
  }

  async cancelSos(sosId: string, reason: string) {
    return this.request(API_CONFIG.ENDPOINTS.SOS_CANCEL(sosId), {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  // Heatmap
  async getHeatmap() {
    return this.request(API_CONFIG.ENDPOINTS.HEATMAP);
  }

  async getHeatmapPredictions(hour?: number) {
    const query = hour !== undefined ? `?hour=${hour}` : '';
    return this.request(`${API_CONFIG.ENDPOINTS.HEATMAP_PREDICT}${query}`);
  }

  async getHeatmapHistory(params?: { zone_id?: string; days?: number }) {
    const query = new URLSearchParams(params as any).toString();
    return this.request(`${API_CONFIG.ENDPOINTS.HEATMAP_HISTORY}${query ? `?${query}` : ''}`);
  }

  // Baseline
  async getBaselineStats() {
    return this.request(API_CONFIG.ENDPOINTS.BASELINE_STATS);
  }
}

export const apiService = new ApiService();
