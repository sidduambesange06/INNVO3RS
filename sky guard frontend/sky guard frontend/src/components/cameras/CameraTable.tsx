import React from 'react';
import { useSystemStore } from '../../store/systemStore';
import { StatusBadge } from '../ui/StatusBadge';

export const CameraTable: React.FC = () => {
  const cameras = useSystemStore(state => state.cameras || []);
  
  const getStatusColor = (status: string) => {
    if (status === 'connected') return 'green';
    if (status === 'error') return 'red';
    return 'amber';
  };

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden w-full">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-surface-raised border-b border-border font-body font-medium text-[11px] text-muted uppercase tracking-wider">
            <th className="py-3 px-4 w-[100px]">Camera ID</th>
            <th className="py-3 px-4">Zone</th>
            <th className="py-3 px-4 w-[100px]">Type</th>
            <th className="py-3 px-4 w-[120px]">Status</th>
            <th className="py-3 px-4 w-[100px]">FPS</th>
            <th className="py-3 px-4 w-[120px]">Resolution</th>
          </tr>
        </thead>
        <tbody>
          {cameras.length === 0 ? (
            <tr>
              <td colSpan={6} className="py-8 text-center font-display tracking-widest text-[12px] text-muted uppercase">
                No cameras available
              </td>
            </tr>
          ) : (
            cameras.map((cam, idx) => {
              const isEven = idx % 2 === 0;
              const statusColor = getStatusColor(cam.status);
              
              return (
                <tr 
                  key={cam.cam_id} 
                  className={`group ${isEven ? 'bg-surface' : 'bg-surface-raised'} hover:translate-x-1 transition-transform border-l-[3px] border-transparent hover:border-accent-blue`}
                >
                  <td className="py-3 px-4 font-mono text-[12px] text-primary">{cam.cam_id}</td>
                  <td className="py-3 px-4 font-body text-[13px] text-primary">{cam.zone_id}</td>
                  <td className="py-3 px-4 font-mono text-[12px] text-secondary">{cam.type}</td>
                  <td className="py-3 px-4">
                    <StatusBadge status={cam.status.toUpperCase()} color={statusColor as any} />
                  </td>
                  <td className="py-3 px-4 font-mono text-[12px] text-secondary">
                    {cam.fps.toFixed(1)}
                  </td>
                  <td className="py-3 px-4 font-mono text-[12px] text-muted">
                    {cam.resolution}
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
