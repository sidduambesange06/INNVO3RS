import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useSystemStore } from './store/systemStore';
import AppShell from './components/layout/AppShell';
import Dashboard from './pages/Dashboard';
import Cameras from './pages/Cameras';
import Dispatch from './pages/Dispatch';
import Heatmap from './pages/Heatmap';
import Sos from './pages/Sos';
import Simulation from './pages/Simulation';
import Logs from './pages/Logs';

export default function App() {
  const initialize = useSystemStore((state) => state.initialize);
  const isLoading = useSystemStore((state) => state.isLoading);

  useEffect(() => {
    // Only initialize once
    let initialized = false;
    if (!initialized) {
      initialized = true;
      initialize();
    }
  }, []); // Empty dependency array - only run once

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0a0a0f]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400 mx-auto mb-4"></div>
          <p className="text-cyan-400 font-mono">Initializing SkyGuard System...</p>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"  element={<Dashboard />} />
          <Route path="cameras"    element={<Cameras />} />
          <Route path="dispatch"   element={<Dispatch />} />
          <Route path="heatmap"    element={<Heatmap />} />
          <Route path="sos"        element={<Sos />} />
          <Route path="simulation" element={<Simulation />} />
          <Route path="logs"       element={<Logs />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
