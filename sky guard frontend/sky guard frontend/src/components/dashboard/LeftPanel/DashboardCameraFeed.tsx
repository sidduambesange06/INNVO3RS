import React from 'react';
import { Camera, Radio } from 'lucide-react';
import { useSystemStore } from '../../../store/systemStore';
import { StatusBadge } from '../../ui/StatusBadge';

export const DashboardCameraFeed: React.FC = () => {
  const alerts = useSystemStore((state) => state.alerts || []);
  const activeAlerts = alerts.filter(a => a.status === 'ACTIVE').slice(0, 5);

  return (
    <div className="flex flex-col gap-3">
      {/* Empty Video Box for Future Stream */}
      <div className="relative w-full aspect-video bg-surface-raised border border-border rounded-lg overflow-hidden flex flex-col items-center justify-center">
        <Camera size={32} className="text-border mb-2 opacity-50" />
        <div className="font-mono text-[11px] text-muted tracking-widest uppercase text-center">
          Incoming Stream <br/>
          <span className="text-[10px] opacity-70">(Awaiting Video Feed Injection)</span>
        </div>
        
        {/* Mock OSD */}
        <div className="absolute top-3 left-3 bg-black/60 backdrop-blur-md px-2 py-1 rounded text-[10px] text-white font-mono flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-accent-red animate-pulse" />
          REC • CAM-MAIN
        </div>
      </div>

      {/* Incident Details underneath */}
      <div className="bg-surface border border-border rounded-lg p-4 flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between mb-3 shrink-0">
          <h3 className="font-display text-[13px] tracking-widest uppercase text-secondary">Active Incidents</h3>
          <Radio size={14} className="text-muted" />
        </div>
        
        <div className="flex flex-col gap-3 overflow-y-auto pr-2 custom-scrollbar">
          {activeAlerts.length > 0 ? (
            activeAlerts.map(alert => (
              <div key={alert.alert_id} className="flex flex-col gap-1 pb-2 border-b border-border/50 last:border-0 last:pb-0">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[12px] font-medium text-primary">{alert.alert_id}</span>
                  <StatusBadge status={
                    alert.severity > 0.8 ? 'CRITICAL' : 
                    alert.severity > 0.6 ? 'HIGH' : 
                    alert.severity > 0.4 ? 'MEDIUM' : 'LOW'
                  } color={
                    alert.severity > 0.7 ? 'red' :
                    alert.severity > 0.4 ? 'amber' : 'green'
                  } />
                </div>
                <div className="text-[13px] text-primary truncate">{alert.anomaly_type}</div>
                <div className="text-[11px] text-secondary">Zone: {alert.zone_name}</div>
              </div>
            ))
          ) : (
            <div className="text-[12px] text-muted italic text-center mt-2">No active incidents reported.</div>
          )}
        </div>
      </div>
    </div>
  );
};
