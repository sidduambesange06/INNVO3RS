import React from 'react';
import { useSystemStore } from '../../store/systemStore';

export const ZoneTable: React.FC = () => {
  const zones = useSystemStore(state => state.zones || []);

  const getScoreColor = (severity: number) => {
    if (severity >= 0.7) return 'var(--accent-red)';
    if (severity >= 0.4) return 'var(--accent-amber)';
    return 'var(--accent-green)';
  };

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden w-full">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-surface-raised border-b border-border font-body font-medium text-[11px] text-muted uppercase tracking-wider">
            <th className="py-3 px-4">Zone</th>
            <th className="py-3 px-4 w-[150px]">Current Count</th>
            <th className="py-3 px-4 w-[150px]">Baseline Mean</th>
            <th className="py-3 px-4 w-[150px]">Anomaly Score</th>
            <th className="py-3 px-4 w-[150px]">Severity</th>
            <th className="py-3 px-4 w-[150px]">Camera</th>
          </tr>
        </thead>
        <tbody>
          {zones.length === 0 ? (
            <tr>
              <td colSpan={6} className="py-8 text-center font-display tracking-widest text-[12px] text-muted uppercase">
                No zone data available
              </td>
            </tr>
          ) : (
            zones.map((zone, idx) => {
              const isEven = idx % 2 === 0;
              const scoreColor = getScoreColor(zone.current_stats?.severity || 0);
              
              return (
                <tr 
                  key={zone.zone_id} 
                  className={`group ${isEven ? 'bg-surface' : 'bg-surface-raised'} hover:translate-x-1 transition-transform border-l-[3px] border-transparent`}
                >
                  <td className="py-3 px-4 font-body text-[13px] text-primary">{zone.name}</td>
                  <td className="py-3 px-4 font-mono text-[13px] text-secondary">
                    {zone.current_stats?.current || 0}
                  </td>
                  <td className="py-3 px-4 font-mono text-[12px] text-secondary">
                    {zone.baseline_mean.toFixed(1)}
                  </td>
                  <td className="py-3 px-4 font-mono text-[12px] text-secondary">
                    {((zone.current_stats?.anomaly_score || 0) * 100).toFixed(0)}%
                  </td>
                  <td className="py-3 px-4 font-mono text-[13px] font-bold" style={{ color: scoreColor }}>
                    {((zone.current_stats?.severity || 0) * 100).toFixed(0)}%
                  </td>
                  <td className="py-3 px-4 font-mono text-[12px] text-blue">{zone.cam_id}</td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
};
