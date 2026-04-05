import React from 'react';
import { DispatchMap } from '../components/dispatch/DispatchMap';
import { DroneTable } from '../components/dispatch/DroneTable';

const Dispatch: React.FC = () => {
  return (
    <div className="flex flex-col gap-6">
      <DispatchMap />
      <DroneTable />
    </div>
  );
};

export default Dispatch;
