import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertCircle, Navigation, Repeat, AlertTriangle, CheckCircle, ShieldOff, Info } from 'lucide-react';
import { useSystemStore } from '../../store/systemStore';
import type { ToastNotification } from '../../types';

const TOAST_CONFIG = {
  INCIDENT_DETECTED: { color: 'var(--accent-red)',    Icon: AlertCircle },
  DRONE_DISPATCHED:  { color: 'var(--accent-blue)',   Icon: Navigation },
  DRONE_REROUTED:    { color: 'var(--accent-amber)',  Icon: Repeat },
  SOS_RECEIVED:      { color: 'var(--accent-red)',    Icon: AlertTriangle },
  DRONE_ARRIVED:     { color: 'var(--accent-green)',  Icon: CheckCircle },
  NO_FLY_ZONE:       { color: 'var(--accent-purple)', Icon: ShieldOff },
  SYSTEM_ALERT:      { color: 'var(--accent-amber)',  Icon: Info },
};

const Toast: React.FC<{ toast: ToastNotification; onRemove: (id: string) => void }> = ({ toast, onRemove }) => {
  const config = TOAST_CONFIG[toast.type];
  const { Icon, color } = config;

  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove(toast.id);
    }, 4000);
    return () => clearTimeout(timer);
  }, [toast.id, onRemove]);

  return (
    <motion.div
      initial={{ x: 80, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 80, opacity: 0 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      className="w-[360px] bg-surface-raised border border-border rounded-lg p-3.5 flex flex-row items-start gap-3"
      style={{ borderLeftWidth: '3px', borderLeftColor: color }}
    >
      <div className="mt-0.5"><Icon size={18} style={{ color }} /></div>
      <div className="flex-1">
        <h4 className="font-body font-medium text-[13px] text-primary mb-0.5">{toast.title}</h4>
        <p className="font-body text-[12px] text-secondary leading-snug">{toast.description}</p>
      </div>
      <button 
        onClick={() => onRemove(toast.id)} 
        className="text-muted hover:text-primary transition-colors mt-0.5"
      >
        <X size={16} />
      </button>
    </motion.div>
  );
};

export const ToastContainer: React.FC = () => {
  const toasts = useSystemStore(state => state.toasts);
  const removeToast = useSystemStore(state => state.removeToast);

  return (
    <div className="fixed top-[56px] right-4 z-40 flex flex-col gap-2 pointer-events-none">
      <div className="flex flex-col gap-2 pointer-events-auto">
        <AnimatePresence>
          {toasts.map(toast => (
            <Toast key={toast.id} toast={toast} onRemove={removeToast} />
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};
