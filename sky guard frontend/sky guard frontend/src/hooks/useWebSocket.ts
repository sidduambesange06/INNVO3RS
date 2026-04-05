import { useEffect } from 'react';
import { wsService } from '../services/websocket';

type EventHandler = (data: any) => void;

/**
 * Hook for subscribing to WebSocket events
 * Automatically cleans up on unmount
 */
export function useWebSocketEvent(event: string, handler: EventHandler) {
  useEffect(() => {
    wsService.on(event, handler);
    
    return () => {
      wsService.off(event, handler);
    };
  }, [event, handler]);
}

/**
 * Hook for subscribing to camera detection stream
 */
export function useCameraStream(camId: string | null) {
  useEffect(() => {
    if (camId) {
      wsService.subscribeToCamera(camId);
    }
  }, [camId]);
}

/**
 * Hook to check WebSocket connection status
 */
export function useWebSocketStatus() {
  return wsService.isConnected();
}
