import React, { useState } from 'react';
import { useSystemStore } from '../store/systemStore';
import { StatusBadge } from '../components/ui/StatusBadge';

type FilterTab = 'All' | 'Info' | 'Warning' | 'Critical';

const Logs: React.FC = () => {
  const alerts = useSystemStore(state => state.alerts || []);
  const [activeTab, setActiveTab] = useState<FilterTab>('All');

  const tabs: FilterTab[] = ['All', 'Info', 'Warning', 'Critical'];

  const filteredAlerts = alerts.filter(alert => {
    if (activeTab === 'All') return true;
    if (activeTab === 'Info') return alert.severity <= 0.4;
    if (activeTab === 'Warning') return alert.severity > 0.4 && alert.severity <= 0.7;
    if (activeTab === 'Critical') return alert.severity > 0.7;
    return true;
  });

  const getSeverityColor = (severity: number) => {
    if (severity > 0.7) return 'red';
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
    <div className="flex flex-col gap-6 h-full">
      <div className="flex gap-6 border-b border-border">
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 font-display text-[13px] tracking-wider transition-colors border-b-2 ${
              activeTab === tab 
                ? 'border-accent-blue text-primary' 
                : 'border-transparent text-muted hover:text-secondary'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="bg-surface border border-border rounded-lg overflow-hidden flex-1 overflow-y-auto">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 z-10 bg-surface-raised border-b border-border">
            <tr className="font-body font-medium text-[11px] text-muted uppercase tracking-wider">
              <th className="py-3 px-4 w-[120px]">Timestamp</th>
              <th className="py-3 px-4 w-[180px]">Alert ID</th>
              <th className="py-3 px-4 w-[120px]">Zone</th>
              <th className="py-3 px-4 w-[120px]">Severity</th>
              <th className="py-3 px-4">Type</th>
              <th className="py-3 px-4 w-[100px]">Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredAlerts.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center font-display tracking-widest text-[12px] text-muted uppercase">
                  No logs found for this filter
                </td>
              </tr>
            ) : (
              filteredAlerts.map((alert, idx) => {
                const isEven = idx % 2 === 0;
                const color = getSeverityColor(alert.severity);
                const severityLabel = getSeverityLabel(alert.severity);

                return (
                  <tr 
                    key={alert.alert_id}
                    className={`group ${isEven ? 'bg-surface' : 'bg-surface-raised'} hover:translate-x-1 transition-transform border-l-[3px] border-transparent hover:border-accent-blue`}
                  >
                    <td className="py-3 px-4 font-mono text-[12px] text-muted">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-4 font-mono text-[12px] text-secondary">{alert.alert_id}</td>
                    <td className="py-3 px-4 font-mono text-[12px] text-primary">{alert.zone_name}</td>
                    <td className="py-3 px-4">
                      <StatusBadge status={severityLabel} color={color as any} />
                    </td>
                    <td className="py-3 px-4 font-body text-[13px] text-primary">{alert.anomaly_type}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full font-mono text-[10px] ${
                        alert.status === 'ACTIVE' ? 'bg-accent-red/10 text-accent-red' : 'bg-accent-green/10 text-accent-green'
                      }`}>
                        {alert.status}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Logs;
