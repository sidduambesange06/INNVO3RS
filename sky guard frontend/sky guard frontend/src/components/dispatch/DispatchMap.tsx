import React from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Tooltip, Polygon } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useSystemStore } from '../../store/systemStore';

interface DispatchMapProps {
  className?: string;
}

export const DispatchMap: React.FC<DispatchMapProps> = ({ className }) => {
  const drones = useSystemStore((state) => state.drones || []);
  const alerts = useSystemStore((state) => state.alerts || []);

  // Convert alerts to incidents format for compatibility
  const incidents = alerts
    .filter(alert => alert.location && alert.location.lat && alert.location.lon)
    .map(alert => ({
      id: alert.alert_id,
      lat: alert.location.lat,
      lng: alert.location.lon,
      severity: alert.severity > 0.8 ? 'CRITICAL' : alert.severity > 0.6 ? 'HIGH' : alert.severity > 0.4 ? 'MEDIUM' : 'LOW',
      type: alert.anomaly_type,
      cameraId: alert.cam_id,
      assignedDrone: alert.primary_drone,
      timestamp: new Date(alert.timestamp)
    }));

  const noFlyZones = [
    [[18.535, 73.855], [18.540, 73.862], [18.533, 73.868], [18.527, 73.860]] as [number, number][],
    [[18.510, 73.835], [18.516, 73.845], [18.508, 73.850], [18.503, 73.840]] as [number, number][],
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'IDLE': return 'var(--accent-green)';
      case 'CHARGING': return 'var(--accent-amber)';
      case 'RETURNING': return 'var(--accent-purple)';
      case 'EN_ROUTE':
      case 'HOVERING':
      default: return 'var(--accent-blue)';
    }
  };

  const getIncidentSize = (sev: string) => {
    if (sev === 'CRITICAL') return 20;
    if (sev === 'HIGH') return 16;
    if (sev === 'MEDIUM') return 12;
    return 10;
  };

  return (
    <div className={`relative rounded-lg overflow-hidden border border-border bg-surface w-full ${className || 'h-[60vh]'}`}>
      <MapContainer 
        center={[18.5204, 73.8567]} 
        zoom={13} 
        style={{ height: '100%', width: '100%', background: 'var(--bg)' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
        />

        {noFlyZones.map((polygon, i) => (
          <Polygon 
            key={i} 
            positions={polygon} 
            pathOptions={{ color: 'var(--accent-purple)', fillColor: 'var(--accent-purple)', fillOpacity: 0.12, weight: 1 }} 
          />
        ))}

        {incidents.map(inc => {
          const size = getIncidentSize(inc.severity);
          const icon = L.divIcon({
            html: `<div style="width: ${size}px; height: ${size}px; border-radius: 50%; background: var(--accent-red); border: 2px solid white; display: flex; align-items: center; justify-content: center; color: white; font-size: ${size-6}px; font-family: 'JetBrains Mono'; box-shadow: 0 0 10px rgba(255,59,59,0.8);">!</div>`,
            className: '',
            iconSize: [size, size],
            iconAnchor: [size/2, size/2]
          });
          return (
            <Marker key={inc.id} position={[inc.lat, inc.lng]} icon={icon}>
              <Tooltip className="font-mono bg-surface border border-border text-primary">{inc.id}: {inc.type}</Tooltip>
            </Marker>
          );
        })}

        {drones.map(drone => {
          const color = getStatusColor(drone.status);
          const animationClass = drone.status === 'HOVERING' ? 'animate-pulse' : '';
          
          const icon = L.divIcon({
            html: `<div class="${animationClass}" style="width: 28px; height: 28px; border-radius: 50%; background: ${color}22; border: 2px solid ${color}; display: flex; align-items: center; justify-center;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 11 22 2 13 21 11 13 3 11"></polygon></svg></div>`,
            className: '',
            iconSize: [28, 28],
            iconAnchor: [14, 14]
          });

          return (
            <React.Fragment key={drone.drone_id}>
              {drone.target_location && (
                <Polyline 
                  positions={[
                    [drone.position.lat, drone.position.lon], 
                    [drone.target_location.lat, drone.target_location.lon]
                  ]}
                  pathOptions={{ color, weight: 1.5, dashArray: '6 4' }}
                />
              )}
              <Marker position={[drone.position.lat, drone.position.lon]} icon={icon}>
                <Tooltip permanent direction="bottom" offset={[0, 12]} className="bg-transparent border-0 shadow-none font-mono text-[10px]">
                  <span style={{ color }}>
                    {drone.drone_id}
                    {drone.eta_seconds ? ` · ${Math.floor(drone.eta_seconds/60)}m` : ''}
                  </span>
                </Tooltip>
              </Marker>
            </React.Fragment>
          );
        })}
      </MapContainer>

      <div className="absolute bottom-4 right-4 z-[1000] bg-surface-raised border border-border rounded-lg p-3 w-[200px] shadow-lg pointer-events-none">
        <div className="font-display text-[10px] uppercase tracking-widest text-muted mb-2">MAP LEGEND</div>
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-accent-blue border border-accent-blue opacity-50" />
            <span className="font-body text-[11px] text-secondary">Drone Active</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-accent-green border border-accent-green opacity-50" />
            <span className="font-body text-[11px] text-secondary">Drone Available</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-3 h-3 rounded-full bg-accent-red text-white text-[8px] font-bold">!</div>
            <span className="font-body text-[11px] text-secondary">Incident Zone</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-accent-purple opacity-20 border border-accent-purple" />
            <span className="font-body text-[11px] text-secondary">No-Fly Zone</span>
          </div>
        </div>
      </div>
    </div>
  );
};
