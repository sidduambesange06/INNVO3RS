import React from 'react';
import { Activity, Wifi, Cpu, Battery } from 'lucide-react';
import { useSystemStore } from '../../../store/systemStore';

export const DashboardEngineStats: React.FC = () => {
  const drones = useSystemStore((state) => state.drones || []);
  
  const avgBattery = drones.length > 0 
    ? Math.floor(drones.reduce((acc, d) => acc + d.battery, 0) / drones.length)
    : 0;

  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <h3 className="font-display text-[13px] tracking-widest uppercase text-secondary flex items-center gap-2 mb-4">
        <Activity size={14} /> Global Telemetry Baseline
      </h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-muted text-[11px] uppercase tracking-wider">
            <Wifi size={12} /> Network Latency
          </div>
          <div className="font-mono text-[16px] text-primary">24<span className="text-[12px] text-muted">ms</span></div>
        </div>
        
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-muted text-[11px] uppercase tracking-wider">
            <Cpu size={12} /> Compute Load
          </div>
          <div className="font-mono text-[16px] text-primary">42<span className="text-[12px] text-muted">%</span></div>
        </div>

        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-muted text-[11px] uppercase tracking-wider">
            <Battery size={12} /> Fleet Battery
          </div>
          <div className="font-mono text-[16px] text-primary">{avgBattery}<span className="text-[12px] text-muted">%</span></div>
        </div>
        
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 text-muted text-[11px] uppercase tracking-wider">
            <Activity size={12} /> Protocol
          </div>
          <div className="font-mono text-[12px] mt-1 text-accent-green">ENCRYPTED</div>
        </div>
      </div>
    </div>
  );
};
