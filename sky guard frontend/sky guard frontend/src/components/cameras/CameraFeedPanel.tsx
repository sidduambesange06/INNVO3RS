import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { StatusBadge } from '../ui/StatusBadge';
import type { Camera } from '../../types';

interface CameraFeedPanelProps {
  camera: Camera;
  streamUrl: string;
  fullWidth?: boolean;
}

export const CameraFeedPanel: React.FC<CameraFeedPanelProps> = ({ camera, streamUrl, fullWidth }) => {
  const [imageError, setImageError] = useState(false);
  const isConnected = camera.status === 'connected';
  const statusColor = camera.status === 'connected' ? 'green' : 'red';

  return (
    <motion.div 
      className="relative rounded-lg overflow-hidden bg-surface-raised border border-border"
      style={{ aspectRatio: fullWidth ? '32/9' : '16/9' }}
    >
      {/* Camera Stream - MJPEG from backend */}
      {!imageError && isConnected ? (
        <img 
          src={streamUrl}
          alt={`Camera ${camera.cam_id}`}
          className="absolute inset-0 w-full h-full object-cover"
          onError={() => {
            console.error(`Failed to load stream for ${camera.cam_id}`);
            setImageError(true);
          }}
          style={{ imageRendering: 'auto' }}
        />
      ) : (
        /* Fallback placeholder */
        <div className="absolute inset-0 bg-surface-raised flex items-center justify-center">
          <div className="text-center">
            <div className="font-mono text-[14px] text-muted">{camera.cam_id}</div>
            <div className="font-body text-[12px] text-secondary mt-1">Zone: {camera.zone_id}</div>
            <div className="font-body text-[10px] text-muted mt-2">
              {imageError ? 'Stream unavailable' : 'Connecting...'}
            </div>
          </div>
        </div>
      )}

      {/* Scanlines overlay */}
      <div 
        className="absolute inset-0 pointer-events-none z-10"
        style={{ 
          background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.04) 2px, rgba(0,0,0,0.05) 4px)' 
        }}
      />

      {/* Top Left OSD */}
      <div className="absolute top-2 left-2 z-20 flex gap-2">
        <div className="bg-black/70 backdrop-blur-sm px-2 py-1 rounded font-mono text-[11px] text-white">
          {camera.cam_id}
        </div>
        <div className="bg-black/70 backdrop-blur-sm px-2 py-1 rounded font-mono text-[11px] text-white">
          {camera.zone_id}
        </div>
      </div>

      {/* Top Right OSD - FPS */}
      <div className="absolute top-2 right-2 z-20">
        <div className="bg-black/70 backdrop-blur-sm px-2 py-1 rounded font-mono text-[11px] text-white">
          {camera.fps.toFixed(1)} FPS
        </div>
      </div>

      {/* Bottom Left OSD - Status */}
      <div className="absolute bottom-2 left-2 z-20">
        <StatusBadge 
          status={camera.status.toUpperCase()} 
          color={statusColor as any} 
        />
      </div>

      {/* Bottom Right OSD - REC indicator */}
      {isConnected && !imageError && (
        <div className="absolute bottom-2 right-2 z-20 bg-black/70 backdrop-blur-sm px-2 py-1 rounded flex items-center gap-2">
          <motion.div 
            className="w-2 h-2 rounded-full bg-accent-red"
            animate={{ opacity: [1, 0.3] }}
            transition={{ duration: 1, repeat: Infinity, repeatType: 'reverse' }}
          />
          <span className="font-mono text-[11px] text-white">REC</span>
        </div>
      )}

      {/* Resolution indicator */}
      <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 z-20">
        <div className="bg-black/70 backdrop-blur-sm px-2 py-1 rounded font-mono text-[10px] text-white">
          {camera.resolution}
        </div>
      </div>
    </motion.div>
  );
};
