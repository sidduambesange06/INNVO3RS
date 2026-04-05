import React from 'react';
import { Outlet } from 'react-router-dom';
import { StatusStrip } from './StatusStrip';
import { Sidebar } from './Sidebar';
import { ActionModal } from '../modals/ActionModal';
import { ToastContainer } from '../ui/ToastContainer';

const AppShell: React.FC = () => {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <StatusStrip />
      
      <div className="flex flex-1 overflow-hidden relative">
        <Sidebar />
        
        <div className="flex-1 overflow-y-auto p-6 bg-bg relative">
          <Outlet />
        </div>
      </div>
      
      <ActionModal />
      <ToastContainer />
    </div>
  );
};

export default AppShell;
