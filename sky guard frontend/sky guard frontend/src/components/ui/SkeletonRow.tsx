import React from 'react';

interface SkeletonRowProps {
  columns?: number;
  height?: number;
}

export const SkeletonRow: React.FC<SkeletonRowProps> = ({ columns = 5, height = 20 }) => {
  return (
    <div className="flex gap-4 w-full" style={{ height }}>
      {Array.from({ length: columns }).map((_, i) => (
        <div
          key={i}
          className="skeleton h-full"
          style={{ width: `${Math.random() * 40 + 60}%`, flex: 1 }}
        />
      ))}
    </div>
  );
};
