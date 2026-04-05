import React from 'react';
import { PulseIndicator } from './PulseIndicator';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  icon: LucideIcon;
  iconColor: string;
  statusDotColor?: string;
  value: string | number;
  label: string;
}

export const StatCard: React.FC<StatCardProps> = ({ 
  icon: Icon, 
  iconColor, 
  statusDotColor, 
  value, 
  label 
}) => {
  return (
    <div className="flex-1 bg-surface border border-border rounded-lg py-4 px-5 flex flex-col justify-between h-full">
      <div className="flex justify-between items-center mb-3">
        <Icon size={20} className={iconColor} />
        {statusDotColor && <PulseIndicator color={statusDotColor} />}
      </div>
      <div className="font-mono text-[28px] text-primary leading-none mb-2">
        {value}
      </div>
      <div className="font-body text-[11px] text-muted uppercase tracking-wider">
        {label}
      </div>
    </div>
  );
};
