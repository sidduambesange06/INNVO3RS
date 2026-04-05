import React from 'react';

interface SectionHeaderProps {
  title: string;
  action?: { label: string; onClick: () => void };
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({ title, action }) => {
  return (
    <div className="flex justify-between items-center border-b border-border-subtle pb-2 mb-4">
      <h2 className="font-display text-[11px] text-muted uppercase tracking-[0.25em]">
        {title}
      </h2>
      {action && (
        <button 
          onClick={action.onClick}
          className="font-body text-[11px] text-blue hover:text-primary transition-colors uppercase tracking-wider"
        >
          {action.label}
        </button>
      )}
    </div>
  );
};
