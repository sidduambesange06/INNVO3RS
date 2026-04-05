import React from 'react';
import { HeatmapView } from '../components/heatmap/HeatmapView';
import { ZoneTable } from '../components/heatmap/ZoneTable';

const Heatmap: React.FC = () => {
  return (
    <div className="flex flex-col gap-6">
      <HeatmapView />
      <ZoneTable />
    </div>
  );
};

export default Heatmap;
