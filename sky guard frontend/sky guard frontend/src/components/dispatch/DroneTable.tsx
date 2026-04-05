import React from 'react';
import { useSystemStore } from '../../store/systemStore';
import { StatusBadge } from '../ui/StatusBadge';
import { EtaTimer } from '../ui/EtaTimer';

export const DroneTable: React.FC = () => {
  const drones = useSystemStore(state => state.drones || []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'IDLE': return 'green';
      case 'CHARGING': return 'amber';
      case 'RETURNING': return 'purple';
      case 'EN_ROUTE':
      case 'HOVERING':
      default: return 'blue';
    }
  };

  const getBatteryColor = (battery: number) => {
    if (battery > 60) return 'var(--accent-green)';
    if (battery >= 30) return 'var(--accent-amber)';
    return 'var(--accent-red)';
  };

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden w-full overflow-y-auto max-h-[40vh]">
      <table className="w-full text-left border-collapse">
        <thead className="sticky top-0 z-10">
          <tr className="bg-surface-raised border-b border-border font-body font-medium text-[11px] text-muted uppercase tracking-wider">
            <th className="py-3 px-4 w-[100px]">Drone</th>
            <th className="py-3 px-4 w-[120px]">Battery</th>
            <th className="py-3 px-4 w-[100px]">Speed</th>
            <th className="py-3 px-4 text-muted">Position</th>
            <th className="py-3 px-4 text-muted">Target</th>
            <th className="py-3 px-4 w-[110px]">Alert</th>
            <th className="py-3 px-4 w-[80px]">ETA</th>
            <th className="py-3 px-4 w-[120px]">Status</th>
            <th className="py-3 px-4 w-[100px]">Distance</th>
          </tr>
        </thead>
        <tbody>
          {drones.length === 0 ? (
            <tr>
              <td colSpan={9} className="py-8 text-center font-display tracking-widest text-[12px] text-muted uppercase">
                No drones available
              </td>
            </tr>
          ) : (
            drones.map((drone, idx) => {
              const isEven = idx % 2 === 0;
              const statusColor = getStatusColor(drone.status);
              const batteryColor = getBatteryColor(drone.battery);
              
              return (
                <tr 
                  key={drone.drone_id} 
                  className={`group ${isEven ? 'bg-surface' : 'bg-surface-raised'} hover:translate-x-1 transition-transform border-l-[3px] border-transparent hover:border-accent-blue`}
                >
                  <td className="py-3 px-4 font-mono text-[12px] text-primary">{drone.drone_id}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-[60px] h-[4px] bg-border rounded-full overflow-hidden">
                        <div style={{ width: `${drone.battery}%`, backgroundColor: batteryColor, height: '100%' }} />
                      </div>
                      <span className="font-mono text-[11px]" style={{ color: batteryColor }}>{Math.round(drone.battery)}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 font-mono text-[12px] text-secondary">
                    {drone.speed_ms ? `${drone.speed_ms.toFixed(1)} m/s` : '—'}
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-muted">
                    {drone.position.lat.toFixed(4)}, {drone.position.lon.toFixed(4)}
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-muted">
                    {drone.target_location 
                      ? `${drone.target_location.lat.toFixed(4)}, ${drone.target_location.lon.toFixed(4)}` 
                      : '—'}
                  </td>
                  <td className="py-3 px-4 text-secondary text-[13px]">
                    {drone.assigned_alert_id ? drone.assigned_alert_id : <span className="text-muted">—</span>}
                  </td>
                  <td className="py-3 px-4">
                    {drone.eta_seconds !== null && drone.eta_seconds !== undefined ? (
                      <EtaTimer seconds={Math.floor(drone.eta_seconds)} />
                    ) : (
                      <span className="font-mono text-[12px] text-muted">—</span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <StatusBadge status={drone.status.replace('_', ' ')} color={statusColor as any} />
                  </td>
                  <td className="py-3 px-4 font-mono text-[12px] text-secondary">
                    {drone.distance_remaining_m 
                      ? `${(drone.distance_remaining_m / 1000).toFixed(1)} km` 
                      : '—'}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
};
