import React, { useState, useEffect } from 'react';

interface EtaTimerProps {
  seconds: number;
  onExpire?: () => void;
}

export const EtaTimer: React.FC<EtaTimerProps> = ({ seconds, onExpire }) => {
  const [timeLeft, setTimeLeft] = useState(seconds);

  useEffect(() => {
    setTimeLeft(seconds); // catch prop updates
  }, [seconds]);

  useEffect(() => {
    if (timeLeft <= 0) {
      onExpire?.();
      return;
    }
    const interval = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          onExpire?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [timeLeft, onExpire]);

  const mins = Math.floor(timeLeft / 60);
  const secs = timeLeft % 60;
  const formatted = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

  let color = 'var(--text-muted)';
  if (timeLeft > 0) {
    if (timeLeft > 60) color = 'var(--accent-green)';
    else if (timeLeft >= 15) color = 'var(--accent-amber)';
    else color = 'var(--accent-red)';
  }

  return (
    <span className="font-mono" style={{ color }}>
      {timeLeft > 0 ? formatted : '00:00'}
    </span>
  );
};
