import React from 'react';
import { CameraFeedGrid } from '../components/cameras/CameraFeedGrid';
import { CameraTable } from '../components/cameras/CameraTable';

const Cameras: React.FC = () => {
  return (
    <div className="flex flex-col gap-6">
      <CameraFeedGrid />
      <CameraTable />
    </div>
  );
};

export default Cameras;
