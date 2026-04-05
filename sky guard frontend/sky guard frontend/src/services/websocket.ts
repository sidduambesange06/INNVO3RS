import { io, Socket } from 'socket.io-client';
import { API_CONFIG } from '../config/api';

type WebSocketEventHandler = (data: any) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;
  private eventHandlers: Map<string, Set<WebSocketEventHandler>> = new Map();
  private isConnecting = false;

  connect() {
    if (this.socket?.connected || this.isConnecting) {
      console.log('WebSocket already connected or connecting');
      return;
    }

    this.isConnecting = true;
    console.log('Connecting to WebSocket:', API_CONFIG.WS_URL);
    
    this.socket = io(API_CONFIG.WS_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: this.reconnectDelay,
      reconnectionAttempts: this.maxReconnectAttempts,
    });

    this.setupEventListeners();
  }

  private setupEventListeners() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.isConnecting = false;
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.isConnecting = false;
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.reconnectAttempts++;
      this.isConnecting = false;
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
      }
    });

    // Real-time event listeners
    this.socket.on('drone_update', (data) => this.emit('drone_update', data));
    this.socket.on('alert_created', (data) => this.emit('alert_created', data));
    this.socket.on('alert_updated', (data) => this.emit('alert_updated', data));
    this.socket.on('baseline_update', (data) => this.emit('baseline_update', data));
    this.socket.on('heatmap_update', (data) => this.emit('heatmap_update', data));
    this.socket.on('sos_received', (data) => this.emit('sos_received', data));
    this.socket.on('sos_countdown', (data) => this.emit('sos_countdown', data));
    this.socket.on('sos_dispatched', (data) => this.emit('sos_dispatched', data));
    this.socket.on('sos_cancelled', (data) => this.emit('sos_cancelled', data));
    this.socket.on('drone_reallocated', (data) => this.emit('drone_reallocated', data));
    this.socket.on('camera_offline', (data) => this.emit('camera_offline', data));
    this.socket.on('camera_online', (data) => this.emit('camera_online', data));
    this.socket.on('detection_stream', (data) => this.emit('detection_stream', data));
    this.socket.on('system_error', (data) => this.emit('system_error', data));
  }

  private emit(event: string, data: any) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in ${event} handler:`, error);
        }
      });
    }
  }

  on(event: string, handler: WebSocketEventHandler) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);
  }

  off(event: string, handler: WebSocketEventHandler) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  subscribeToCamera(camId: string) {
    if (this.socket?.connected) {
      this.socket.emit('subscribe_camera', { cam_id: camId });
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.eventHandlers.clear();
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const wsService = new WebSocketService();
