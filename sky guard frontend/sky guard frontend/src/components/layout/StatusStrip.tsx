import React, { useState, useEffect } from 'react';
import { Navigation, AlertCircle } from 'lucide-react';
import { useSystemStore } from '../../store/systemStore';
import { PulseIndicator } from '../ui/PulseIndicator';
import ConnectionStatus from '../ui/ConnectionStatus';

export const StatusStrip: React.FC = () => {
  const systemStatus = useSystemStore((state) => state.systemStatus);
  const drones = useSystemStore((state) => state.drones);
  const alerts = useSystemStore((state) => state.alerts);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const activeDroneCount = drones?.filter(d => ['EN_ROUTE', 'HOVERING'].includes(d.status)).length || 0;
  const activeAlertCount = alerts?.filter(a => a.status === 'ACTIVE').length || 0;

  const statusColorMap = {
    NOMINAL: 'var(--accent-green)',
    ALERT: 'var(--accent-red)',
    SIMULATION: 'var(--accent-amber)'
  };
  const color = statusColorMap[systemStatus];
  const pulseSpeed = systemStatus === 'ALERT' ? 'fast' : systemStatus === 'NOMINAL' ? 'slow' : 'normal';

  return (
    <div className="h-[44px] bg-surface border-b border-border px-6 flex items-center justify-between flex-shrink-0">
      <div className="flex items-center gap-3">
        <span className="font-display text-[13px] text-blue tracking-[0.3em]">SKYGUARD</span>
        <span className="text-muted">|</span>
        <span className="font-body text-[10px] text-muted tracking-widest">URBAN RESPONSE PLATFORM</span>
      </div>

      <div className="flex items-center gap-2">
        <PulseIndicator color={color} size={8} speed={pulseSpeed} />
        <span className="font-mono text-[11px] tracking-[0.2em] uppercase" style={{ color }}>
          {systemStatus}
        </span>
      </div>

      <div className="flex items-center gap-6">
        <ConnectionStatus />
        <div className="flex items-center gap-2 text-secondary">
          <Navigation size={14} />
          <span className="font-mono text-[12px]">{activeDroneCount} ACTIVE</span>
        </div>
        <div className="flex items-center gap-2" style={{ color: activeAlertCount > 0 ? 'var(--accent-red)' : 'var(--text-muted)' }}>
          <AlertCircle size={14} />
          <span className="font-mono text-[12px]">{activeAlertCount} ALERTS</span>
        </div>
        <span className="text-muted">|</span>
        <span className="font-mono text-[13px] text-primary">
          {time.toLocaleTimeString('en-US', { hour12: false })}
        </span>
      </div>
    </div>
  );
};
