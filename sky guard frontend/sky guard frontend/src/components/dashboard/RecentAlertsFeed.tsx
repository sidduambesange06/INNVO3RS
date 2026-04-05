import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { SectionHeader } from '../ui/SectionHeader';
import { StatusBadge } from '../ui/StatusBadge';
import { useSystemStore } from '../../store/systemStore';

export const RecentAlertsFeed: React.FC = () => {
  const navigate = useNavigate();
  const alerts = useSystemStore(state => state.alerts || []);

  const displayAlerts = alerts.slice(0, 10);

  const getSeverityColor = (severity: number) => {
    if (severity > 0.8) return 'var(--accent-red)';
    if (severity > 0.6) return 'var(--accent-red)';
    if (severity > 0.4) return 'var(--accent-amber)';
    return 'var(--accent-blue)';
  };

  const getBadgeColor = (severity: number) => {
    if (severity > 0.8) return 'red';
    if (severity > 0.6) return 'red';
    if (severity > 0.4) return 'amber';
    return 'blue';
  };

  const getSeverityLabel = (severity: number) => {
    if (severity > 0.8) return 'CRITICAL';
    if (severity > 0.6) return 'HIGH';
    if (severity > 0.4) return 'MEDIUM';
    return 'LOW';
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-5 overflow-y-auto h-full">
      <SectionHeader 
        title="RECENT ALERTS" 
        action={{ label: "FULL LOG →", onClick: () => navigate('/logs') }} 
      />

      <div className="flex flex-col gap-1">
        <AnimatePresence>
          {displayAlerts.map(alert => (
            <motion.div 
              key={alert.alert_id}
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-3 py-2 hover:translate-x-1 transition-transform border-l-2 border-transparent hover:border-accent-blue px-2 -ml-2"
            >
              <div className="font-mono text-[10px] text-muted w-[50px] flex-shrink-0 text-right">
                {new Date(alert.timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </div>
              <div 
                className="w-1.5 h-1.5 rounded-full flex-shrink-0" 
                style={{ backgroundColor: getSeverityColor(alert.severity) }} 
              />
              <div className="flex flex-col flex-1 min-w-0">
                <div className="font-mono text-[10px] text-secondary truncate">
                  {alert.anomaly_type} - {alert.zone_name}
                </div>
              </div>
              <div className="flex-shrink-0 ml-auto scale-[0.8] origin-right">
                <StatusBadge status={getSeverityLabel(alert.severity)} color={getBadgeColor(alert.severity) as any} />
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};
