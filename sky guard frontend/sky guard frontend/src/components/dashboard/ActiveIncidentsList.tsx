import React from 'react';
import { useNavigate } from 'react-router-dom';
import { SectionHeader } from '../ui/SectionHeader';
import { PulseIndicator } from '../ui/PulseIndicator';
import { StatusBadge } from '../ui/StatusBadge';
import { EtaTimer } from '../ui/EtaTimer';
import { useSystemStore } from '../../store/systemStore';
import { CheckCircle2 } from 'lucide-react';

export const ActiveIncidentsList: React.FC = () => {
  const navigate = useNavigate();
  const alerts = useSystemStore(state => state.alerts || []);
  const cameras = useSystemStore(state => state.cameras || []);
  const drones = useSystemStore(state => state.drones || []);

  const activeIncidents = alerts.filter(a => a.status === 'ACTIVE');

  const getSeverityColor = (severity: number) => {
    if (severity > 0.7) return 'red';
    if (severity > 0.4) return 'amber';
    return 'green';
  };

  const getSeverityLabel = (severity: number) => {
    if (severity > 0.8) return 'CRITICAL';
    if (severity > 0.6) return 'HIGH';
    if (severity > 0.4) return 'MEDIUM';
    return 'LOW';
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-5 overflow-y-auto flex-1 h-full">
      <SectionHeader 
        title="ACTIVE INCIDENTS" 
        action={{ label: "VIEW ALL →", onClick: () => navigate('/dispatch') }} 
      />

      {activeIncidents.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-[200px] text-accent-green">
          <CheckCircle2 size={32} className="mb-2" />
          <span className="font-display tracking-widest text-[12px] uppercase">NO ACTIVE INCIDENTS</span>
        </div>
      ) : (
        <div className="flex flex-col">
          {activeIncidents.map(alert => {
            const cam = cameras.find(c => c.cam_id === alert.cam_id);
            const drone = drones.find(d => d.drone_id === alert.primary_drone);
            const colorName = getSeverityColor(alert.severity);
            const severityLabel = getSeverityLabel(alert.severity);

            return (
              <div 
                key={alert.alert_id}
                className={`group flex items-center gap-4 py-3 border-b border-border-subtle last:border-0 hover:translate-x-1 transition-transform border-l-2 border-l-transparent hover:border-l-accent-blue pl-2 -ml-2`}
              >
                <div className="w-[16px] flex justify-center">
                  <PulseIndicator color={colorName} size={10} />
                </div>
                
                <div className="flex flex-col flex-1 gap-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[12px] text-muted">{alert.alert_id}</span>
                    <span className="font-body text-[14px] text-primary font-medium">{alert.anomaly_type}</span>
                  </div>
                  <div className="font-body text-[12px] text-secondary">
                    {alert.cam_id} · {alert.zone_name}
                  </div>
                </div>

                <div className="flex flex-col items-end gap-1 min-w-[100px]">
                  <StatusBadge status={severityLabel} color={colorName as any} />
                  <div className="flex items-center gap-2">
                    {alert.primary_drone ? (
                      <>
                        <span className="font-mono text-[12px] text-blue">{alert.primary_drone}</span>
                        {alert.primary_eta !== null && alert.primary_eta !== undefined ? (
                          <EtaTimer seconds={Math.floor(alert.primary_eta)} />
                        ) : (
                          <span className="font-mono text-[12px] text-muted">ETA --:--</span>
                        )}
                      </>
                    ) : (
                      <span className="font-mono text-[12px] text-muted">UNASSIGNED</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
