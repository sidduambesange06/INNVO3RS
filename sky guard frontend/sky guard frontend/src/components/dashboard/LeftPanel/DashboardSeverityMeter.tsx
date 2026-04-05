import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { useSystemStore } from '../../../store/systemStore';

export const DashboardSeverityMeter: React.FC = () => {
  const alerts = useSystemStore((state) => state.alerts || []);
  
  // Calculate a mock threat level (0 to 100) based on active alerts
  const activeAlerts = alerts.filter(a => a.status === 'ACTIVE');
  const threatLevel = activeAlerts.length > 0
    ? Math.min(100, Math.floor(activeAlerts.reduce((acc, a) => acc + (a.severity * 100), 0) / activeAlerts.length))
    : 0;
  const criticalCount = incidents.filter(i => i.severity === 'CRITICAL').length;
  const highCount = incidents.filter(i => i.severity === 'HIGH').length;
  const mediumCount = incidents.filter(i => i.severity === 'MEDIUM').length;
  
  let threatScore = (criticalCount * 30) + (highCount * 15) + (mediumCount * 5);
  threatScore = Math.min(Math.max(threatScore, 10), 100); // Floor 10, Cap 100
  
  let color = 'var(--accent-green)';
  let label = 'NOMINAL';
  if (threatScore > 75) { color = 'var(--accent-red)'; label = 'CRITICAL'; }
  else if (threatScore > 40) { color = 'var(--accent-amber)'; label = 'ELEVATED'; }

  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-display text-[13px] tracking-widest uppercase text-secondary flex items-center gap-2">
          <ShieldAlert size={14} /> Global Threat Level
        </h3>
        <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-surface-raised font-bold border border-border" style={{ color }}>
          {label}
        </span>
      </div>
      
      <div className="flex items-end justify-between mb-2">
        <div className="font-mono text-[32px] font-bold leading-none" style={{ color }}>{threatScore}<span className="text-[14px] text-muted">%</span></div>
        <div className="text-[11px] text-muted uppercase tracking-wider text-right">
          {criticalCount} Critical<br/>
          {highCount} High
        </div>
      </div>
      
      <div className="w-full h-[6px] bg-surface-raised rounded-full overflow-hidden border border-border">
        <div 
          className="h-full transition-all duration-1000 ease-out"
          style={{ width: `${threatScore}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
};
