import React from 'react';
import { SosMap } from '../components/sos/SosMap';
import { SosTable } from '../components/sos/SosTable';

const Sos: React.FC = () => {
  return (
    <div className="flex flex-col gap-6">
      <SosMap />
      <SosTable />
    </div>
  );
};

export default Sos;
