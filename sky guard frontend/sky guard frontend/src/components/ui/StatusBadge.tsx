import React from 'react';

interface StatusBadgeProps {
  status: string;
  color: 'green' | 'red' | 'amber' | 'blue' | 'purple';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, color }) => {
  return (
    <span 
      className="inline-flex items-center font-body font-medium text-[10px] uppercase tracking-wider px-[8px] py-[3px] rounded-full"
      style={{
        backgroundColor: `var(--badge-${color}-bg)`,
        border: `1px solid var(--accent-${color})`,
        color: `var(--accent-${color})`
      }}
    >
      {status}
    </span>
  );
};
