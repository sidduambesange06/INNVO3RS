import React from 'react';
import { useSystemStore } from '../../store/systemStore';
import { StatusBadge } from '../ui/StatusBadge';
import { PulseIndicator } from '../ui/PulseIndicator';

export const SosTable: React.FC = () => {
  const sosRequests = useSystemStore(state => state.sosRequests || []);

  const getStatusColor = (status: string) => {
    if (status === 'PENDING') return 'amber';
    if (status === 'CANCELLED') return 'red';
    if (status === 'DISPATCHED') return 'blue';
    return 'green';
  };

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden w-full">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-surface-raised border-b border-border font-body font-medium text-[11px] text-muted uppercase tracking-wider">
            <th className="py-3 px-4 w-[150px]">SOS ID</th>
            <th className="py-3 px-4">Message</th>
            <th className="py-3 px-4 w-[120px]">Time</th>
            <th className="py-3 px-4 w-[120px]">Zone</th>
            <th className="py-3 px-4 w-[120px]">Sender</th>
            <th className="py-3 px-4 w-[150px]">Alert ID</th>
            <th className="py-3 px-4 w-[150px]">Status</th>
          </tr>
        </thead>
        <tbody>
          {sosRequests.length === 0 ? (
            <tr>
              <td colSpan={7} className="py-8 text-center font-display tracking-widest text-[12px] text-muted uppercase">
                No SOS requests
              </td>
            </tr>
          ) : (
            sosRequests.map((sos, idx) => {
              const isEven = idx % 2 === 0;
              const statusColor = getStatusColor(sos.status);
              const isPending = sos.status === 'PENDING';
              
              return (
                <tr 
                  key={sos.sos_id} 
                  className={`group ${isEven ? 'bg-surface' : 'bg-surface-raised'} hover:translate-x-1 transition-transform border-l-[3px] border-transparent hover:border-accent-${statusColor}`}
                >
                  <td className="py-3 px-4 font-mono text-[12px] text-primary">{sos.sos_id}</td>
                  <td className="py-3 px-4 font-body text-[13px] text-primary">{sos.message}</td>
                  <td className="py-3 px-4 font-mono text-[12px] text-muted">
                    {new Date(sos.created_at).toLocaleTimeString()}
                  </td>
                  <td className="py-3 px-4 font-mono text-[12px] text-secondary">
                    {sos.zone_id || '—'}
                  </td>
                  <td className="py-3 px-4 font-mono text-[12px] text-secondary">
                    {sos.sender_id}
                  </td>
                  <td className="py-3 px-4 font-mono text-[12px] text-blue">
                    {sos.alert_id || <span className="text-muted">—</span>}
                  </td>
                  <td className="py-3 px-4 flex items-center gap-2">
                    {isPending && <PulseIndicator color="var(--accent-amber)" />}
                    <StatusBadge status={sos.status.replace('_', ' ')} color={statusColor as any} />
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
};
