import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Circle, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.heat';
import { useSystemStore } from '../../store/systemStore';

// Custom component to add heat layer to react-leaflet
const HeatLayer: React.FC<{ points: [number, number, number][] }> = ({ points }) => {
  const map = useMap();

  useEffect(() => {
    if (points.length === 0) return;
    
    // @ts-ignore - leaflet.heat adds heatLayer to L
    const heat = L.heatLayer(points, {
      radius: 40,
      blur: 25,
      maxZoom: 14,
      gradient: { 0.4: '#F5D020', 0.65: '#E8A020', 1.0: '#FF3B3B' }
    }).addTo(map);

    return () => {
      map.removeLayer(heat);
    };
  }, [map, points]);

  return null;
};

export const HeatmapView: React.FC = () => {
  const heatmapPoints = useSystemStore(state => state.heatmapPoints || []);
  const hotspots = useSystemStore(state => state.hotspots || []);
  const [showHotspots, setShowHotspots] = useState(true);

  const heatPoints: [number, number, number][] = heatmapPoints.map(point => [
    point.lat,
    point.lon,
    point.intensity
  ]);

  const getIntensityColor = (intensity: number) => {
    if (intensity >= 0.7) return 'var(--accent-red)';
    if (intensity >= 0.4) return 'var(--accent-amber)';
    return 'var(--accent-green)';
  };

  return (
    <div className="relative rounded-lg overflow-hidden border border-border bg-surface w-full h-[55vh]">
      <MapContainer 
        center={[18.5204, 73.8567]} 
        zoom={12} 
        style={{ height: '100%', width: '100%', background: 'var(--bg)' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; CARTO'
        />

        {heatPoints.length > 0 && <HeatLayer points={heatPoints} />}

        {showHotspots && hotspots.map((hotspot, index) => {
          const color = getIntensityColor(hotspot.intensity);
          return (
            <Circle 
              key={`${hotspot.zone_id}-${index}`}
              center={[hotspot.lat, hotspot.lon]} 
              radius={300} 
              pathOptions={{ color, fillColor: color, weight: 2, opacity: 0.6, fillOpacity: 0.2 }}
            >
              <Tooltip className="font-mono bg-surface border border-border text-primary">
                <div>
                  <div className="font-bold">{hotspot.zone_name}</div>
                  <div>Intensity: {(hotspot.intensity * 100).toFixed(0)}%</div>
                  <div>Incidents: {hotspot.incident_count}</div>
                </div>
              </Tooltip>
            </Circle>
          );
        })}
      </MapContainer>

      <div className="absolute top-4 right-4 z-[1000]">
        <button
          onClick={() => setShowHotspots(!showHotspots)}
          className={`px-4 py-2 rounded font-display text-[11px] tracking-wider transition-colors border ${
            showHotspots 
              ? 'bg-badge-blue-bg border-accent-blue text-accent-blue' 
              : 'bg-surface-raised border-border text-secondary hover:text-primary'
          }`}
        >
          {showHotspots ? 'HIDE HOTSPOTS' : 'SHOW HOTSPOTS'}
        </button>
      </div>

      {heatmapPoints.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-surface/80 z-[999]">
          <div className="text-center">
            <div className="font-display text-[14px] text-muted tracking-widest">NO HEATMAP DATA</div>
            <div className="font-body text-[12px] text-secondary mt-2">Waiting for incident data...</div>
          </div>
        </div>
      )}
    </div>
  );
};
