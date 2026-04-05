import { create } from 'zustand';
import { apiService } from '../services/api';
import { wsService } from '../services/websocket';
import type { 
  Drone, Alert, Camera, SosRequest, Zone, 
  ToastNotification, ActionModalPayload, HeatmapPoint, Hotspot 
} from '../types';

interface SystemStore {
  drones: Drone[];
  alerts: Alert[];
  cameras: Camera[];
  sosRequests: SosRequest[];
  zones: Zone[];
  heatmapPoints: HeatmapPoint[];
  hotspots: Hotspot[];
  toasts: ToastNotification[];
  systemStatus: 'NOMINAL' | 'ALERT' | 'SIMULATION';
  isConnected: boolean;
  isLoading: boolean;

  actionModal: {
    visible: boolean;
    payload: ActionModalPayload | null;
  };

  // Actions
  initialize: () => Promise<void>;
  fetchDrones: () => Promise<void>;
  fetchAlerts: () => Promise<void>;
  fetchCameras: () => Promise<void>;
  fetchSosRequests: () => Promise<void>;
  fetchZones: () => Promise<void>;
  fetchHeatmap: () => Promise<void>;
  
  addToast: (t: Omit<ToastNotification, 'id'>) => void;
  removeToast: (id: string) => void;
  showActionModal: (payload: ActionModalPayload) => void;
  confirmAction: () => Promise<void>;
  declineAction: () => void;
  
  dispatchDrone: (droneId: string, lat: number, lon: number, zoneId?: string) => Promise<void>;
  rerouteDrone: (droneId: string, lat: number, lon: number, alertId?: string) => Promise<void>;
  returnDroneToLaunch: (droneId: string) => Promise<void>;
  resolveAlert: (alertId: string) => Promise<void>;
  createSos: (data: any) => Promise<void>;
  cancelSos: (sosId: string, reason: string) => Promise<void>;
}

const generateId = () => Math.random().toString(36).substr(2, 9);

export const useSystemStore = create<SystemStore>((set, get) => ({
  drones: [],
  alerts: [],
  cameras: [],
  sosRequests: [],
  zones: [],
  heatmapPoints: [],
  hotspots: [],
  toasts: [],
  systemStatus: 'NOMINAL',
  isConnected: false,
  isLoading: true,

  actionModal: {
    visible: false,
    payload: null,
  },

  initialize: async () => {
    try {
      set({ isLoading: true });
      
      console.log('Initializing SkyGuard system...');
      
      // Connect WebSocket
      wsService.connect();
      
      // Setup WebSocket event handlers
      wsService.on('drone_update', (data) => {
        if (data?.data?.drones) {
          set({ drones: data.data.drones, isConnected: true });
        }
      });

      wsService.on('alert_created', (data) => {
        if (data?.data) {
          const { addToast } = get();
          set((state) => ({
            alerts: [data.data, ...state.alerts],
          }));
          addToast({
            type: 'INCIDENT_DETECTED',
            title: 'New Alert',
            description: `${data.data.anomaly_type} detected in ${data.data.zone_name}`,
          });
        }
      });

      wsService.on('alert_updated', (data) => {
        if (data?.data) {
          set((state) => ({
            alerts: state.alerts.map(a => 
              a.alert_id === data.data.alert_id ? data.data : a
            ),
          }));
        }
      });

      wsService.on('baseline_update', (data) => {
        if (data?.data?.zones) {
          set((state) => ({
            zones: state.zones.map(zone => {
              const update = data.data.zones.find((z: any) => z.zone_id === zone.zone_id);
              return update ? { ...zone, current_stats: update } : zone;
            }),
          }));
        }
      });

      wsService.on('heatmap_update', (data) => {
        if (data?.data) {
          set({
            heatmapPoints: data.data.points || [],
            hotspots: data.data.hotspots || [],
          });
        }
      });

      wsService.on('sos_received', (data) => {
        if (data?.data) {
          const { addToast } = get();
          set((state) => ({
            sosRequests: [data.data, ...state.sosRequests],
          }));
          addToast({
            type: 'SOS_RECEIVED',
            title: 'SOS Received',
            description: data.data.message || 'Emergency request received',
          });
        }
      });

      wsService.on('sos_dispatched', (data) => {
        if (data?.data) {
          const { addToast } = get();
          set((state) => ({
            sosRequests: state.sosRequests.map(s =>
              s.sos_id === data.data.sos.sos_id ? data.data.sos : s
            ),
            alerts: data.data.alert ? [data.data.alert, ...state.alerts] : state.alerts,
          }));
          addToast({
            type: 'DRONE_DISPATCHED',
            title: 'SOS Dispatched',
            description: 'Drone dispatched to SOS location',
          });
        }
      });

      wsService.on('sos_cancelled', (data) => {
        if (data?.data) {
          set((state) => ({
            sosRequests: state.sosRequests.map(s =>
              s.sos_id === data.data.sos_id ? data.data : s
            ),
          }));
        }
      });

      wsService.on('drone_reallocated', (data) => {
        if (data?.data) {
          const { addToast } = get();
          addToast({
            type: 'DRONE_REROUTED',
            title: 'Drone Reallocated',
            description: `${data.data.drone_id} reassigned: ${data.data.reason}`,
          });
        }
      });

      wsService.on('camera_offline', (data) => {
        if (data?.data?.cam_id) {
          set((state) => ({
            cameras: state.cameras.map(c =>
              c.cam_id === data.data.cam_id ? { ...c, status: 'disconnected' as const } : c
            ),
          }));
        }
      });

      wsService.on('camera_online', (data) => {
        if (data?.data?.cam_id) {
          set((state) => ({
            cameras: state.cameras.map(c =>
              c.cam_id === data.data.cam_id ? { ...c, status: 'connected' as const } : c
            ),
          }));
        }
      });

      wsService.on('system_error', (data) => {
        if (data?.data?.message) {
          const { addToast } = get();
          addToast({
            type: 'SYSTEM_ALERT',
            title: 'System Error',
            description: data.data.message,
          });
        }
      });

      // Fetch initial data
      await Promise.all([
        get().fetchDrones(),
        get().fetchAlerts(),
        get().fetchCameras(),
        get().fetchSosRequests(),
        get().fetchZones(),
        get().fetchHeatmap(),
      ]);

      set({ isLoading: false, isConnected: wsService.isConnected() });
      console.log('SkyGuard system initialized successfully');
    } catch (error) {
      console.error('Initialization error:', error);
      set({ isLoading: false, isConnected: false });
      // Don't throw - allow app to render with empty data
    }
  },

  fetchDrones: async () => {
    try {
      const response = await apiService.getDrones();
      if (response?.drones) {
        set({ drones: response.drones });
      }
    } catch (error) {
      console.error('Failed to fetch drones:', error);
    }
  },

  fetchAlerts: async () => {
    try {
      const response = await apiService.getAlerts({ limit: 50 });
      if (response?.alerts) {
        set({ alerts: response.alerts });
      }
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    }
  },

  fetchCameras: async () => {
    try {
      const response = await apiService.getCameras();
      if (response?.cameras) {
        set({ cameras: response.cameras });
      }
    } catch (error) {
      console.error('Failed to fetch cameras:', error);
    }
  },

  fetchSosRequests: async () => {
    try {
      const response = await apiService.getSosEvents({ limit: 50 });
      if (response?.sos_events) {
        set({ sosRequests: response.sos_events });
      }
    } catch (error) {
      console.error('Failed to fetch SOS requests:', error);
    }
  },

  fetchZones: async () => {
    try {
      const response = await apiService.getZones();
      if (response?.zones) {
        set({ zones: response.zones });
      }
    } catch (error) {
      console.error('Failed to fetch zones:', error);
    }
  },

  fetchHeatmap: async () => {
    try {
      const response = await apiService.getHeatmap();
      if (response) {
        set({
          heatmapPoints: response.points || [],
          hotspots: response.hotspots || [],
        });
      }
    } catch (error) {
      console.error('Failed to fetch heatmap:', error);
    }
  },

  addToast: (t) => set((state) => {
    const newToast = { ...t, id: generateId() };
    const queue = [...state.toasts, newToast].slice(-3);
    return { toasts: queue };
  }),

  removeToast: (id) => set((state) => ({
    toasts: state.toasts.filter(t => t.id !== id)
  })),

  showActionModal: (payload) => set({
    actionModal: { visible: true, payload }
  }),

  confirmAction: async () => {
    const { actionModal, dispatchDrone, rerouteDrone, addToast } = get();
    if (!actionModal.payload) return;
    
    const payload = actionModal.payload;
    
    try {
      if (payload.modalType === 'DISPATCH' && payload.incidentId) {
        // Extract coordinates from incident
        const alert = get().alerts.find(a => a.alert_id === payload.incidentId);
        if (alert) {
          await dispatchDrone(
            payload.droneId,
            alert.location.lat,
            alert.location.lon,
            alert.zone_id
          );
          addToast({
            type: 'DRONE_DISPATCHED',
            title: 'Drone Dispatched',
            description: `${payload.droneId} dispatched to ${payload.incidentId}`,
          });
        }
      } else if (payload.modalType === 'REROUTE' && payload.toIncidentId) {
        const alert = get().alerts.find(a => a.alert_id === payload.toIncidentId);
        if (alert) {
          await rerouteDrone(
            payload.droneId,
            alert.location.lat,
            alert.location.lon,
            alert.alert_id
          );
          addToast({
            type: 'DRONE_REROUTED',
            title: 'Drone Rerouted',
            description: `${payload.droneId} rerouted to ${payload.toIncidentId}`,
          });
        }
      }
      
      set({ actionModal: { visible: false, payload: null } });
    } catch (error) {
      console.error('Action confirmation failed:', error);
      addToast({
        type: 'SYSTEM_ALERT',
        title: 'Action Failed',
        description: 'Failed to execute action',
      });
    }
  },

  declineAction: () => set({
    actionModal: { visible: false, payload: null }
  }),

  dispatchDrone: async (droneId, lat, lon, zoneId) => {
    try {
      await apiService.dispatchDrone(droneId, { lat, lon, zone_id: zoneId });
      await get().fetchDrones();
    } catch (error) {
      console.error('Failed to dispatch drone:', error);
      throw error;
    }
  },

  rerouteDrone: async (droneId, lat, lon, alertId) => {
    try {
      await apiService.rerouteDrone(droneId, { lat, lon, alert_id: alertId });
      await get().fetchDrones();
    } catch (error) {
      console.error('Failed to reroute drone:', error);
      throw error;
    }
  },

  returnDroneToLaunch: async (droneId) => {
    try {
      await apiService.returnDroneToLaunch(droneId);
      await get().fetchDrones();
    } catch (error) {
      console.error('Failed to return drone:', error);
      throw error;
    }
  },

  resolveAlert: async (alertId) => {
    try {
      await apiService.resolveAlert(alertId);
      await get().fetchAlerts();
    } catch (error) {
      console.error('Failed to resolve alert:', error);
      throw error;
    }
  },

  createSos: async (data) => {
    try {
      await apiService.createSos(data);
      await get().fetchSosRequests();
    } catch (error) {
      console.error('Failed to create SOS:', error);
      throw error;
    }
  },

  cancelSos: async (sosId, reason) => {
    try {
      await apiService.cancelSos(sosId, reason);
      await get().fetchSosRequests();
    } catch (error) {
      console.error('Failed to cancel SOS:', error);
      throw error;
    }
  },
}));
