import React from 'react';
import { motion } from 'framer-motion';
import { MapPin, Zap, PhoneCall, ShieldOff, Layers, RotateCcw } from 'lucide-react';
import { useSystemStore } from '../../store/systemStore';
import { PulseIndicator } from '../ui/PulseIndicator';
import { apiService } from '../../services/api';

export const SimulationControls: React.FC = () => {
  const alerts = useSystemStore(state => state.alerts || []);
  const addToast = useSystemStore(state => state.addToast);

  const triggerIncidentZoneA = async () => {
    try {
      await apiService.createManualAlert({
        zone_id: 'Zone-A',
        anomaly_type: 'crowd_anomaly',
        severity: 0.85
      });
      addToast({
        type: 'INCIDENT_DETECTED',
        title: 'Incident Triggered',
        description: 'Zone Alpha incident created'
      });
    } catch (error) {
      console.error('Failed to trigger incident:', error);
    }
  };

  const triggerIncidentZoneB = async () => {
    try {
      await apiService.createManualAlert({
        zone_id: 'Zone-B',
        anomaly_type: 'traffic_anomaly',
        severity: 0.65
      });
      addToast({
        type: 'INCIDENT_DETECTED',
        title: 'Incident Triggered',
        description: 'Zone Beta incident created'
      });
    } catch (error) {
      console.error('Failed to trigger incident:', error);
    }
  };

  const triggerHighSeverity = async () => {
    try {
      await apiService.createManualAlert({
        zone_id: 'Zone-C',
        anomaly_type: 'critical_event',
        severity: 0.95
      });
      addToast({
        type: 'INCIDENT_DETECTED',
        title: 'Critical Alert',
        description: 'High severity incident created'
      });
    } catch (error) {
      console.error('Failed to trigger incident:', error);
    }
  };

  const triggerSOS = async () => {
    try {
      await apiService.createSos({
        sender_id: 'sim_user_' + Date.now(),
        message: 'Simulated emergency request',
        lat: 18.5286,
        lon: 73.8395,
        location_type: 'gps'
      });
      addToast({
        type: 'SOS_RECEIVED',
        title: 'SOS Triggered',
        description: 'Emergency request created'
      });
    } catch (error) {
      console.error('Failed to trigger SOS:', error);
    }
  };

  const triggerNoFlyZone = () => {
    addToast({
      type: 'NO_FLY_ZONE',
      title: 'No-Fly Zone',
      description: 'Airspace restriction activated (simulated)'
    });
  };

  const triggerMultiIncident = async () => {
    await triggerIncidentZoneA();
    setTimeout(() => triggerIncidentZoneB(), 2000);
  };

  const buttons = [
    { 
      id: 'z-a', title: 'Trigger Incident', subtitle: 'Zone Alpha — Shivajinagar', 
      icon: MapPin, color: 'var(--accent-red)', action: triggerIncidentZoneA 
    },
    { 
      id: 'z-b', title: 'Trigger Incident', subtitle: 'Zone Beta — Koregaon', 
      icon: MapPin, color: 'var(--accent-amber)', action: triggerIncidentZoneB 
    },
    { 
      id: 'hi-sev', title: 'High Severity Incident', subtitle: 'Priority Override', 
      icon: Zap, color: 'var(--accent-red)', action: triggerHighSeverity 
    },
    { 
      id: 'sos', title: 'Trigger SOS Request', subtitle: 'Civilian Emergency', 
      icon: PhoneCall, color: 'var(--accent-amber)', action: triggerSOS 
    },
    { 
      id: 'nofly', title: 'No-Fly Zone Event', subtitle: 'Airspace Restriction', 
      icon: ShieldOff, color: 'var(--accent-purple)', action: triggerNoFlyZone 
    },
    { 
      id: 'multi', title: 'Multi-Incident Scenario', subtitle: 'Mass Event Simulation', 
      icon: Layers, color: 'var(--accent-blue)', action: triggerMultiIncident 
    },
  ];

  return (
    <div className="flex flex-col gap-6 w-full">
      <div className="grid grid-cols-2 gap-3 w-full">
        {buttons.map(btn => (
          <motion.button
            key={btn.id}
            whileTap={{ scale: 0.97 }}
            onClick={btn.action}
            className="flex flex-col items-start gap-2 bg-surface-raised border border-border rounded-lg px-6 py-5 text-left hover:bg-surface transition-colors focus:outline-none"
            style={{ boxShadow: 'inset 0 2px 6px rgba(0,0,0,0.5)' }}
          >
            <btn.icon size={22} style={{ color: btn.color }} className="mb-1" />
            <span className="font-body font-medium text-[14px] text-primary">{btn.title}</span>
            <span className="font-body text-[11px] text-muted">{btn.subtitle}</span>
          </motion.button>
        ))}

        <div className="col-span-2">
          <motion.button
            whileTap={{ scale: 0.98 }}
            onClick={() => window.location.reload()}
            className="w-full flex justify-center items-center gap-3 bg-surface-raised border border-accent-red rounded-lg px-6 py-5 text-left hover:bg-surface transition-colors focus:outline-none"
            style={{ boxShadow: 'inset 0 2px 6px rgba(0,0,0,0.5)' }}
          >
            <RotateCcw size={20} className="text-accent-red" />
            <div className="flex flex-col">
              <span className="font-body font-medium text-[14px] text-accent-red">Reset Simulation</span>
              <span className="font-body text-[11px] text-accent-red opacity-80 text-center">Reload Page</span>
            </div>
          </motion.button>
        </div>
      </div>

      <div className="bg-surface border border-border rounded-lg p-5">
        <div className="flex items-center gap-2 border-b border-border-subtle pb-2 mb-4">
          <h2 className="font-display text-[11px] text-muted uppercase tracking-[0.25em]">RECENT ALERTS</h2>
          {alerts.length > 0 && <PulseIndicator color="var(--accent-amber)" />}
        </div>
        
        <div className="flex flex-col gap-1 max-h-[300px] overflow-y-auto">
          {alerts.length === 0 ? (
            <div className="text-center py-8 text-muted font-mono text-[12px]">
              No alerts yet. Trigger a simulation above.
            </div>
          ) : (
            alerts.slice(0, 10).map((alert, idx) => (
              <div
                key={`${alert.alert_id}-${idx}`}
                className="flex gap-4 py-2 border-b border-border-subtle last:border-0"
              >
                <div className="font-mono text-[11px] text-muted w-[60px] flex-shrink-0">
                  {new Date(alert.timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </div>
                <div className="font-mono text-[11px] text-secondary w-[130px] flex-shrink-0">
                  {alert.anomaly_type}
                </div>
                <div className="font-body text-[13px] text-primary flex-1">
                  {alert.zone_name} - Severity: {(alert.severity * 100).toFixed(0)}%
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
