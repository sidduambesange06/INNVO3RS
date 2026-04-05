import React from 'react';
import { motion } from 'framer-motion';

interface PulseIndicatorProps {
  color: string;
  size?: number;
  speed?: 'slow' | 'normal' | 'fast';
}

export const PulseIndicator: React.FC<PulseIndicatorProps> = ({ 
  color, 
  size = 8, 
  speed = 'normal' 
}) => {
  const duration = speed === 'slow' ? 2.2 : speed === 'fast' ? 0.8 : 1.4;

  // Resolve color token if it matches our accent names
  const resolvedColor = ['green', 'red', 'amber', 'blue', 'purple'].includes(color) 
    ? `var(--accent-${color})` 
    : color;

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <motion.div
        className="absolute rounded-full"
        style={{ 
          width: '100%', 
          height: '100%', 
          backgroundColor: resolvedColor 
        }}
        animate={{ scale: [1, 2.2], opacity: [0.8, 0] }}
        transition={{
          duration,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      <div 
        className="absolute rounded-full" 
        style={{ 
          width: size, 
          height: size, 
          backgroundColor: resolvedColor 
        }} 
      />
    </div>
  );
};
