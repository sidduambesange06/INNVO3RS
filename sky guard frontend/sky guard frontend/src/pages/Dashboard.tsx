import React from 'react';
import { SystemStatsBar } from '../components/dashboard/SystemStatsBar';
import { DashboardCameraFeed } from '../components/dashboard/LeftPanel/DashboardCameraFeed';
import { DashboardSeverityMeter } from '../components/dashboard/LeftPanel/DashboardSeverityMeter';
import { DashboardEngineStats } from '../components/dashboard/LeftPanel/DashboardEngineStats';
import { DashboardDroneTable } from '../components/dashboard/DashboardDroneTable';
import { DispatchMap } from '../components/dispatch/DispatchMap';
import { RecentAlertsFeed } from '../components/dashboard/RecentAlertsFeed';

const Dashboard: React.FC = () => {
  return (
    <div 
      className="w-full h-full flex flex-col gap-4"
      style={{
        height: 'calc(100vh - 44px - 48px)'
      }}
    >
      {/* Top Bar */}
      <div>
        <SystemStatsBar />
      </div>
      
      {/* Middle Map & Telemetry Row */}
      <div 
        className="w-full flex-1 min-h-0"
        style={{
          display: 'grid',
          gridTemplateColumns: '550px 1fr',
          gap: '16px'
        }}
      >
        {/* Left Panel */}
        <div className="flex flex-col gap-4 overflow-y-auto pr-1 custom-scrollbar">
          <DashboardCameraFeed />
          <DashboardSeverityMeter />
          <DashboardEngineStats />
        </div>
        
        {/* Right Panel - Map */}
        <div className="h-full rounded-lg overflow-hidden border border-border">
          <DispatchMap className="h-full" />
        </div>
      </div>
      
      {/* Bottom Row */}
      <div className="h-[250px] shrink-0" style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '16px' }}>
        <DashboardDroneTable />
        <div className="h-full overflow-hidden">
          <RecentAlertsFeed />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
