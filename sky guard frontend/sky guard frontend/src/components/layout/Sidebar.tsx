import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutGrid, Cctv, Navigation, Map, AlertTriangle, SlidersHorizontal, ScrollText, Crosshair } from 'lucide-react';

const navItems = [
  { path: '/dashboard',  Icon: LayoutGrid,         label: 'Dashboard'      },
  { path: '/cameras',    Icon: Cctv,               label: 'Camera Feeds'   },
  { path: '/dispatch',   Icon: Navigation,         label: 'Drone Dispatch' },
  { path: '/heatmap',    Icon: Map,                label: 'Heatmap'        },
  { path: '/sos',        Icon: AlertTriangle,      label: 'SOS Requests'   },
  { path: '/simulation', Icon: SlidersHorizontal,  label: 'Simulation'     },
  { path: '/logs',       Icon: ScrollText,         label: 'System Logs'    },
];

export const Sidebar: React.FC = () => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div 
      className="bg-bg border-r border-border h-full flex flex-col flex-shrink-0 z-30"
      style={{
        width: expanded ? '220px' : '64px',
        transition: 'width 200ms cubic-bezier(0.4, 0, 0.2, 1)',
        overflow: 'hidden'
      }}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      <div className="h-[44px] w-[64px] flex items-center justify-center flex-shrink-0 shrink-0">
        <Crosshair size={20} className="text-blue" />
      </div>

      <div className="flex flex-col mt-4">
        {navItems.map(({ path, Icon, label }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) => `
              h-[48px] px-[20px] flex items-center gap-[14px] w-full
              border-l-[3px] transition-colors overflow-hidden
              ${isActive 
                ? 'border-accent-blue bg-badge-blue-bg text-blue' 
                : 'border-transparent text-muted hover:text-secondary hover:bg-surface'
              }
            `}
          >
            {({ isActive }) => (
              <>
                <Icon size={18} className="flex-shrink-0 min-w-[18px]" style={{ color: isActive ? 'var(--accent-blue)' : undefined }} />
                <span 
                  className="font-body text-[13px] whitespace-nowrap transition-all duration-200"
                  style={{
                    opacity: expanded ? 1 : 0,
                    width: expanded ? 'auto' : 0,
                    color: isActive ? 'var(--text-primary)' : 'inherit'
                  }}
                >
                  {label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </div>
  );
};
