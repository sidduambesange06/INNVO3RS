import React from 'react';
import { useSystemStore } from '../../store/systemStore';
import { EtaTimer } from '../ui/EtaTimer';

export const DashboardDroneTable: React.FC = () => {
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'IDLE': return 'var(--accent-green)';
      case 'EN_ROUTE': return 'var(--accent-blue)';
      case 'HOVERING': return 'var(--accent-blue)';
      case 'RETURNING': return 'var(--accent-purple)';
      case 'CHARGING': return 'var(--accent-amber)';
      default: return 'var(--text-primary)';
    }
  };

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden h-full flex flex-col">
      <div className="px-4 py-3 border-b border-border bg-surface-raised flex items-center justify-between">
        <h3 className="font-display text-[12px] tracking-widest uppercase text-secondary">Active Drone Telemetry</h3>
      </div>
      
      <div className="flex-1 overflow-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-raised/50">
              <th className="px-4 py-2 font-display text-[10px] tracking-widest uppercase text-muted font-normal">Drone ID</th>
              <th className="px-4 py-2 font-display text-[10px] tracking-widest uppercase text-muted font-normal">Battery</th>
              <th className="px-4 py-2 font-display text-[10px] tracking-widest uppercase text-muted font-normal">Assignment</th>
              <th className="px-4 py-2 font-display text-[10px] tracking-widest uppercase text-muted font-normal">Status</th>
              <th className="px-4 py-2 font-display text-[10px] tracking-widest uppercase text-muted font-normal">ETA</th>
              <th className="px-4 py-2 font-display text-[10px] tracking-widest uppercase text-muted font-normal">Speed</th>
              <th className="px-4 py-2 font-display text-[10px] tracking-widest uppercase text-muted font-normal">Distance</th>
            </tr>
          </thead>
          <tbody>
            {drones.map(drone => {
              const assignedIncident = incidents.find(i => i.assignedDrone === drone.drone_id);
              const color = getStatusColor(drone.status);
              const distance = drone.distance_remaining_m 
                ? `${(drone.distance_remaining_m / 1000).toFixed(1)} km` 
                : '—';

              return (
                <tr key={drone.drone_id} className="border-b border-border/50 hover:bg-surface-raised/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-[13px] text-primary">{drone.drone_id}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                       <div className="flex-1 h-1.5 bg-surface-raised rounded-full overflow-hidden w-[60px]">
                         <div className="h-full bg-primary" style={{ 
                           width: `${drone.battery}%`, 
                           opacity: drone.battery < 30 ? 0.5 : 1, 
                           backgroundColor: drone.battery < 30 ? 'var(--accent-red)' : 'var(--accent-green)' 
                         }} />
                       </div>
                       <span className="font-mono text-[11px] text-secondary w-[25px]">{drone.battery}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    {assignedIncident ? (
                      <div>
                        <div className="font-mono text-[12px] text-primary">{assignedIncident.id}</div>
                        <div className="font-body text-[11px] text-muted truncate max-w-[150px]">{assignedIncident.type}</div>
                      </div>
                    ) : (
                      <span className="font-body text-[12px] text-muted italic">Unassigned</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span 
                      className="px-2 py-0.5 rounded-full font-mono text-[10px] border"
                      style={{ color, borderColor: color, backgroundColor: `${color}15` }}
                    >
                      {drone.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-[13px]">
                    {drone.eta_seconds !== null && drone.eta_seconds !== undefined ? (
                      <EtaTimer seconds={Math.floor(drone.eta_seconds)} />
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-[13px] text-secondary">
                    {drone.speed_ms ? `${drone.speed_ms.toFixed(1)} m/s` : '—'}
                  </td>
                  <td className="px-4 py-3 font-mono text-[13px] text-secondary">{distance}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
