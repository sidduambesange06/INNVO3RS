import React, { useState, useEffect } from 'react';
import { Navigation, AlertCircle, AlertTriangle, Cctv, Clock } from 'lucide-react';
import { StatCard } from '../ui/StatCard';
import { useSystemStore } from '../../store/systemStore';

export const SystemStatsBar: React.FC = () => {
  const drones = useSystemStore((state) => state.drones || []);
  const alerts = useSystemStore((state) => state.alerts || []);
  const sosRequests = useSystemStore((state) => state.sosRequests || []);
  const cameras = useSystemStore((state) => state.cameras || []);
  const [uptime, setUptime] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setUptime(prev => prev + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const activeDrones = drones.filter(d => ['EN_ROUTE', 'HOVERING'].includes(d.status)).length;
  const activeIncidents = alerts.filter(a => a.status === 'ACTIVE').length;
  const pendingSos = sosRequests.filter(s => s.status === 'PENDING').length;
  const onlineCameras = cameras.filter(c => c.status === 'connected').length;

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex gap-3 w-full">
      <StatCard 
        icon={Navigation} 
        iconColor="text-blue" 
        value={activeDrones} 
        label="Active Drones" 
      />
      <StatCard 
        icon={AlertCircle} 
        iconColor={activeIncidents > 0 ? "text-red" : "text-muted"} 
        statusDotColor={activeIncidents > 0 ? "red" : undefined}
        value={activeIncidents} 
        label="Active Incidents" 
      />
      <StatCard 
        icon={AlertTriangle} 
        iconColor="text-amber" 
        value={pendingSos} 
        label="SOS Pending" 
      />
      <StatCard 
        icon={Cctv} 
        iconColor="text-green" 
        value={onlineCameras} 
        label="Cameras Online" 
      />
      <StatCard 
        icon={Clock} 
        iconColor="text-secondary" 
        value={formatUptime(uptime)} 
        label="System Uptime" 
      />
    </div>
  );
};
