import React from 'react';
import { motion } from 'framer-motion';
import { SectionHeader } from '../ui/SectionHeader';
import { StatusBadge } from '../ui/StatusBadge';
import { EtaTimer } from '../ui/EtaTimer';
import { useSystemStore } from '../../store/systemStore';

export const ActiveDronesList: React.FC = () => {
  const drones = useSystemStore(state => state.drones || []);
  const alerts = useSystemStore(state => state.alerts || []);

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
    <div className="bg-surface border border-border rounded-lg p-5 overflow-y-auto w-full h-full">
      <SectionHeader title="DRONE FLEET" />

      <div className="flex flex-col gap-2">
        {drones.map(drone => {
          const assignment = alerts.find(a => a.alert_id === drone.assigned_alert_id);
          const batteryColor = getBatteryColor(drone.battery);

          return (
            <div key={drone.drone_id} className="bg-surface-raised border border-border rounded-md px-3.5 py-3 flex flex-col gap-2">
              <div className="flex justify-between items-center">
                <span className="font-mono text-[13px] text-primary">{drone.drone_id}</span>
                <StatusBadge status={drone.status.replace('_', ' ')} color={getStatusColor(drone.status) as any} />
              </div>
              
              <div className="h-px w-full bg-border" />

              <div className="flex items-center gap-2">
                <span className="font-body text-[11px] text-muted w-[50px]">Battery</span>
                <div className="flex-1 h-[3px] bg-border rounded-full overflow-hidden flex">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${drone.battery}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    style={{ backgroundColor: batteryColor, height: '100%' }}
                  />
                </div>
                <span className="font-mono text-[11px]" style={{ color: batteryColor }}>
                  {Math.round(drone.battery)}%
                </span>
              </div>

              <div className="flex justify-between items-end mt-1">
                <div className="font-body text-[12px] text-secondary flex-1 truncate pr-2">
                  {assignment ? `Assignment: ${assignment.alert_id} · ${assignment.anomaly_type}` : 'No active assignment'}
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-body text-[11px] text-muted uppercase tracking-wider">ETA</span>
                  {drone.eta_seconds !== null && drone.eta_seconds !== undefined ? (
                    <EtaTimer seconds={Math.floor(drone.eta_seconds)} />
                  ) : (
                    <span className="font-mono text-[12px] text-muted">—</span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
