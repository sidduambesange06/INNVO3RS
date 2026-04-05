import React from 'react';
import { SimulationControls } from '../components/simulation/SimulationControls';
import { useSystemStore } from '../store/systemStore';
import { PulseIndicator } from '../components/ui/PulseIndicator';

const Simulation: React.FC = () => {
  const simulationActive = useSystemStore(state => state.simulationActive);

  return (
    <div className="flex flex-col gap-6 w-full max-w-4xl mx-auto">
      <div className="flex items-center justify-between border-b border-border pb-4">
        <h1 className="font-display text-[20px] text-primary">SIMULATION CONTROL PANEL</h1>
        <div className="flex items-center gap-2 bg-surface-raised px-4 py-1.5 rounded-full border border-border">
          {simulationActive ? (
            <PulseIndicator color="var(--accent-green)" />
          ) : (
            <div className="w-2 h-2 rounded-full bg-muted" />
          )}
          <span className={`font-mono text-[11px] uppercase ${simulationActive ? 'text-accent-green' : 'text-muted'}`}>
            {simulationActive ? 'SIMULATION ACTIVE' : 'STANDBY'}
          </span>
        </div>
      </div>
      
      <SimulationControls />
    </div>
  );
};

export default Simulation;
