import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useSystemStore } from '../../store/systemStore';

export const SosMap: React.FC = () => {
  const sosRequests = useSystemStore(state => state.sosRequests || []);

  return (
    <div className="relative rounded-lg overflow-hidden border border-border bg-surface w-full h-[45vh]">
      <MapContainer 
        center={[18.5204, 73.8567]} 
        zoom={13} 
        style={{ height: '100%', width: '100%', background: 'var(--bg)' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; CARTO'
        />

        {sosRequests.map(sos => {
          const isPending = sos.status === 'PENDING';
          const animationClass = isPending ? 'animate-pulse' : '';
          const icon = L.divIcon({
            html: `<div class="${animationClass}" style="width: 24px; height: 24px; border-radius: 50%; background: var(--accent-red); border: 2px solid white; display: flex; align-items: center; justify-content: center; color: white; font-family: 'JetBrains Mono'; font-weight: bold; box-shadow: 0 0 10px rgba(255,59,59,0.5);">!</div>`,
            className: '',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
          });

          return (
            <Marker key={sos.sos_id} position={[sos.location.lat, sos.location.lon]} icon={icon}>
              <Popup className="font-body text-primary">
                <div className="bg-surface-raised p-2 rounded -m-4">
                  <div className="font-mono text-[12px] text-muted mb-1">{sos.sos_id}</div>
                  <div className="font-body text-[14px] text-primary mb-2">{sos.message}</div>
                  <div className="flex items-center gap-2">
                    <span className="font-body text-[11px] text-muted uppercase">Status:</span>
                    <span className={`font-mono text-[11px] ${isPending ? 'text-accent-amber' : 'text-accent-green'}`}>{sos.status}</span>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {sosRequests.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-surface/80 z-[999]">
          <div className="text-center">
            <div className="font-display text-[14px] text-muted tracking-widest">NO SOS REQUESTS</div>
            <div className="font-body text-[12px] text-secondary mt-2">All clear</div>
          </div>
        </div>
      )}
    </div>
  );
};
