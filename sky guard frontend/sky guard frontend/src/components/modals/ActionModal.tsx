import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSystemStore } from '../../store/systemStore';
import { StatusBadge } from '../ui/StatusBadge';
import { X, Check, ArrowRight } from 'lucide-react';

export const ActionModal: React.FC = () => {
  const actionModal = useSystemStore((state) => state.actionModal);
  const confirmAction = useSystemStore((state) => state.confirmAction);
  const declineAction = useSystemStore((state) => state.declineAction);
  const [timeLeft, setTimeLeft] = useState(10);
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    if (actionModal.visible) {
      setTimeLeft(10);
      setExecuting(false);
    }
  }, [actionModal.visible]);

  useEffect(() => {
    if (!actionModal.visible || executing) return;

    if (timeLeft <= 0) {
      setExecuting(true);
      setTimeout(() => {
        confirmAction();
      }, 1000);
      return;
    }

    const interval = setInterval(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [timeLeft, actionModal.visible, executing, confirmAction]);

  if (!actionModal.payload) return null;
  const { payload } = actionModal;

  const isDispatch = payload.modalType === 'DISPATCH';
  const color = isDispatch ? 'var(--accent-blue)' : 'var(--accent-amber)';
  const badgeText = isDispatch ? 'AI DISPATCH REQUEST' : 'AI REROUTE REQUEST';
  const titleText = isDispatch ? 'DRONE DISPATCH CONFIRMATION' : 'REROUTE CONFIRMATION';
  const subtitleText = isDispatch 
    ? 'AI system has identified an incident requiring drone deployment.'
    : 'AI system recommends redirecting drone to a higher-priority incident.';

  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - timeLeft / 10);

  return (
    <AnimatePresence>
      {actionModal.visible && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 bg-white/70 backdrop-blur-md"
          />
          <motion.div
            initial={{ scale: 0.92, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.92, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="relative w-[600px] bg-surface-raised rounded-xl p-[40px]"
            style={{ 
              border: `2px solid ${color}`,
              boxShadow: `0 15px 40px rgba(0,0,0,0.15), 0 0 0 1px var(--border)`
            }}
          >
            {executing && (
              <motion.div
                initial={{ opacity: 0 }} animate={{ opacity: [0, 0.15, 0] }} transition={{ duration: 0.6 }}
                className="absolute inset-0 bg-accent-green rounded-xl pointer-events-none z-10"
              />
            )}
            
            {executing ? (
              <div className="absolute inset-0 flex items-center justify-center z-20">
                <div className="font-display text-[24px] text-accent-green tracking-widest flex items-center gap-4">
                  <Check size={32} />
                  AI DECISION EXECUTED
                </div>
              </div>
            ) : (
              <>
                <div className="text-center mb-6">
                  <div 
                    className="inline-block px-3 py-1 rounded-full font-display text-[11px] tracking-[0.3em] uppercase mb-4"
                    style={{ backgroundColor: isDispatch ? 'var(--badge-blue-bg)' : 'var(--badge-amber-bg)', color }}
                  >
                    {badgeText}
                  </div>
                  <h2 className="font-display text-[22px] text-primary mb-2">{titleText}</h2>
                  <p className="font-body text-secondary text-[14px]">{subtitleText}</p>
                </div>

                <div className="w-full h-px bg-border my-6" />

                <div className="flex flex-col gap-3 mb-6">
                  <div className="flex">
                    <div className="w-[160px] font-body text-[12px] text-muted uppercase tracking-wider">Drone</div>
                    <div className="font-mono text-[14px] text-blue">{payload.droneId}</div>
                  </div>
                  
                  {isDispatch ? (
                    <>
                      <div className="flex items-center">
                        <div className="w-[160px] font-body text-[12px] text-muted uppercase tracking-wider">Incident ID</div>
                        <div className="font-mono text-[14px] text-primary">{payload.incidentId}</div>
                      </div>
                      <div className="flex items-center">
                        <div className="w-[160px] font-body text-[12px] text-muted uppercase tracking-wider">Incident Type</div>
                        <div className="font-body text-[14px] text-primary">{payload.incidentType}</div>
                      </div>
                      <div className="flex items-center">
                        <div className="w-[160px] font-body text-[12px] text-muted uppercase tracking-wider">Severity</div>
                        <div>
                          {payload.incidentSeverity && (
                            <StatusBadge status={payload.incidentSeverity} color={
                              payload.incidentSeverity === 'CRITICAL' || payload.incidentSeverity === 'HIGH' ? 'red' : 'amber'
                            } />
                          )}
                        </div>
                      </div>
                      <div className="flex items-center">
                        <div className="w-[160px] font-body text-[12px] text-muted uppercase tracking-wider">Location</div>
                        <div className="font-body text-[14px] text-primary">{payload.incidentLocation}</div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex items-center">
                        <div className="w-[160px] font-body text-[12px] text-muted uppercase tracking-wider">Current Assignment</div>
                        <div className="flex items-center gap-3">
                          <span className="font-body text-[14px] text-primary">{payload.fromIncidentType}</span>
                          {payload.fromSeverity && <StatusBadge status={payload.fromSeverity} color={
                            payload.fromSeverity === 'CRITICAL' || payload.fromSeverity === 'HIGH' ? 'red' :
                            payload.fromSeverity === 'MEDIUM' ? 'amber' : 'green'
                          } />}
                        </div>
                      </div>
                      <div className="flex items-center mt-1">
                        <div className="w-[160px] font-body text-[12px] text-muted uppercase tracking-wider">New Assignment</div>
                        <div className="flex items-center gap-3">
                          <span className="font-body text-[14px] text-primary">{payload.toIncidentType}</span>
                          {payload.toSeverity && <StatusBadge status={payload.toSeverity} color={
                            payload.toSeverity === 'CRITICAL' || payload.toSeverity === 'HIGH' ? 'red' :
                            payload.toSeverity === 'MEDIUM' ? 'amber' : 'green'
                          } />}
                        </div>
                      </div>
                      <div className="flex items-center mt-1">
                        <div className="w-[160px] font-body text-[12px] text-muted uppercase tracking-wider">Priority Change</div>
                        <div className="flex items-center gap-2">
                          {payload.fromSeverity && <StatusBadge status={payload.fromSeverity} color={
                            payload.fromSeverity === 'CRITICAL' || payload.fromSeverity === 'HIGH' ? 'red' : 'amber'
                          } />}
                          <ArrowRight size={14} className="text-secondary" />
                          {payload.toSeverity && <StatusBadge status={payload.toSeverity} color={
                            payload.toSeverity === 'CRITICAL' || payload.toSeverity === 'HIGH' ? 'red' : 'amber'
                          } />}
                        </div>
                      </div>
                      <div className="flex items-center">
                        <div className="w-[160px] font-body text-[12px] text-muted uppercase tracking-wider">New Location</div>
                        <div className="font-body text-[14px] text-primary">{payload.toLocation}</div>
                      </div>
                      <div className="flex items-start mt-1">
                        <div className="w-[160px] font-body text-[12px] text-muted uppercase tracking-wider">AI Recommendation</div>
                        <div className="font-body text-[13px] text-secondary italic flex-1">{payload.aiRecommendation}</div>
                      </div>
                    </>
                  )}
                  
                  <div className="flex items-center mt-2">
                    <div className="w-[160px] font-body text-[12px] text-muted uppercase tracking-wider">Est. ETA</div>
                    <div className="font-mono text-[14px] text-green">{Math.floor((payload.estimatedEta || 0) / 60)}m {(payload.estimatedEta || 0) % 60}s</div>
                  </div>
                </div>

                <div className="w-full h-px bg-border my-6" />

                <div className="flex flex-col items-center justify-center mb-8">
                  <div className="relative w-[120px] h-[120px] flex items-center justify-center mb-4">
                    <svg className="absolute inset-0 transform -rotate-90" width="120" height="120">
                      <circle cx="60" cy="60" r="50" fill="none" stroke="var(--border)" strokeWidth="6" />
                      <circle 
                        cx="60" cy="60" r="50" fill="none" stroke={color} strokeWidth="6"
                        strokeDasharray={circumference} strokeDashoffset={strokeDashoffset}
                        strokeLinecap="round"
                        className="transition-all duration-1000 ease-linear"
                      />
                    </svg>
                    <span className="font-mono text-[28px] text-primary font-bold">{timeLeft}</span>
                  </div>
                  <div className="text-center">
                    <div className="font-body text-[11px] text-muted uppercase tracking-widest mb-1">AUTO-CONFIRMING IN</div>
                    <div className="font-mono text-[14px]" style={{ color }}>{timeLeft} SECONDS</div>
                  </div>
                </div>

                <div className="flex gap-4 mb-4">
                  <motion.button
                    whileTap={{ scale: 0.97 }}
                    onClick={declineAction}
                    className="flex-1 h-[56px] rounded-md border-[1.5px] border-accent-red bg-badge-red-bg text-accent-red flex items-center justify-center gap-3 font-display text-[14px] tracking-[0.15em] uppercase hover:bg-[rgba(255,59,59,0.18)] transition-all"
                  >
                    <X size={18} /> DECLINE
                  </motion.button>
                  <motion.button
                    whileTap={{ scale: 0.97 }}
                    onClick={confirmAction}
                    className="flex-1 h-[56px] rounded-md border-[1.5px] border-accent-green bg-badge-green-bg text-accent-green flex items-center justify-center gap-3 font-display text-[14px] tracking-[0.15em] uppercase hover:bg-[rgba(0,217,126,0.18)] transition-all"
                  >
                    <Check size={18} /> CONFIRM
                  </motion.button>
                </div>

                <div className="text-center font-body text-[11px] text-muted italic">
                  No response within 10 seconds will auto-confirm the AI recommendation
                </div>
              </>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
