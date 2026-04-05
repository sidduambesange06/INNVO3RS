import React from 'react';
import { CameraFeedPanel } from './CameraFeedPanel';
import { useSystemStore } from '../../store/systemStore';
import { apiService } from '../../services/api';

export const CameraFeedGrid: React.FC = () => {
  const cameras = useSystemStore(state => state.cameras || []);

  // Split first 4 for top grid, rest for bottom
  const topCameras = cameras.slice(0, 4);
  const bottomCameras = cameras.slice(4);

  return (
    <div className="flex flex-col gap-4 w-full">
      {cameras.length === 0 ? (
        <div className="bg-surface border border-border rounded-lg p-8 text-center">
          <div className="font-display text-[14px] text-muted tracking-widest">NO CAMERAS AVAILABLE</div>
          <div className="font-body text-[12px] text-secondary mt-2">Waiting for camera connections...</div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4">
            {topCameras.map(cam => (
              <CameraFeedPanel 
                key={cam.cam_id} 
                camera={cam}
                streamUrl={apiService.getCameraStreamUrl(cam.cam_id)}
              />
            ))}
          </div>
          {bottomCameras.length > 0 && (
            <div className="grid grid-cols-2 gap-4">
              {bottomCameras.map(cam => (
                <CameraFeedPanel 
                  key={cam.cam_id} 
                  camera={cam}
                  streamUrl={apiService.getCameraStreamUrl(cam.cam_id)}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};
