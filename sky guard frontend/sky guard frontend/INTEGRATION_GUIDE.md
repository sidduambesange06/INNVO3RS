# SkyGuard Frontend - Backend Integration Guide

## Quick Setup

### 1. Environment Configuration

Create a `.env` file in the project root (already created):

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

That's it! This is the ONLY configuration file you need to modify.

### 2. Install Dependencies

```bash
npm install
```

### 3. Start Backend Server

Make sure your SkyGuard V2 backend is running:

```bash
cd skyguard-v2
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Start Frontend

```bash
npm run dev
```

The frontend will automatically connect to the backend at `http://localhost:8000`.

---

## Architecture Overview

### Real-Time Communication

The application uses **WebSocket** for real-time updates with automatic reconnection:

- **Drone positions**: Updated every 500ms
- **Alerts**: Instant notifications
- **Camera detections**: Real-time stream
- **SOS events**: Immediate updates with countdown
- **Heatmap**: Updated every 30 seconds
- **Baseline stats**: Updated every 5 seconds

### API Integration

All API calls are centralized in `src/services/api.ts`:

```typescript
import { apiService } from './services/api';

// Example: Fetch drones
const drones = await apiService.getDrones();

// Example: Dispatch drone
await apiService.dispatchDrone('DR-01', {
  lat: 18.5204,
  lon: 73.8567,
  zone_id: 'Zone-A'
});
```

### State Management

Zustand store (`src/store/systemStore.ts`) manages all application state:

```typescript
import { useSystemStore } from './store/systemStore';

function MyComponent() {
  const drones = useSystemStore(state => state.drones);
  const fetchDrones = useSystemStore(state => state.fetchDrones);
  
  // Use drones data...
}
```

---

## Key Features

### ✅ Automatic Reconnection
- WebSocket automatically reconnects on connection loss
- Maximum 5 reconnection attempts with 2-second delay
- Visual connection status indicator

### ✅ Real-Time Updates
- No manual refresh needed
- All data updates automatically via WebSocket
- Optimistic UI updates for better UX

### ✅ Error Handling
- Graceful degradation on API failures
- Toast notifications for errors
- Console logging for debugging

### ✅ Type Safety
- Full TypeScript support
- API response types match backend schema
- Compile-time error checking

---

## API Endpoints Used

### Drones
- `GET /drones` - List all drones
- `POST /drones/{drone_id}/dispatch` - Dispatch drone
- `POST /drones/{drone_id}/reroute` - Reroute drone
- `POST /drones/{drone_id}/rtl` - Return to launch

### Alerts
- `GET /alerts` - List alerts
- `POST /alerts/manual` - Create manual alert
- `PATCH /alerts/{alert_id}/resolve` - Resolve alert

### Cameras
- `GET /cameras` - List cameras
- `GET /cameras/{cam_id}/stream` - MJPEG stream
- `GET /cameras/{cam_id}/detections` - Latest detections

### SOS
- `GET /sos` - List SOS events
- `POST /sos` - Create SOS
- `POST /sos/{sos_id}/cancel` - Cancel SOS

### Zones & Heatmap
- `GET /zones` - List zones with stats
- `GET /heatmap` - Get heatmap data
- `GET /heatmap/predict` - AI predictions

---

## WebSocket Events

### Subscribed Events

The frontend automatically subscribes to these events:

| Event | Description | Update Frequency |
|-------|-------------|------------------|
| `drone_update` | Drone positions & status | 500ms |
| `alert_created` | New alert detected | Instant |
| `alert_updated` | Alert status changed | Instant |
| `baseline_update` | Zone statistics | 5s |
| `heatmap_update` | Heatmap data | 30s |
| `sos_received` | New SOS request | Instant |
| `sos_countdown` | SOS buffer countdown | 1s |
| `sos_dispatched` | SOS auto-dispatched | Instant |
| `sos_cancelled` | SOS cancelled | Instant |
| `drone_reallocated` | Drone reassigned | Instant |
| `camera_offline` | Camera disconnected | Instant |
| `camera_online` | Camera reconnected | Instant |
| `detection_stream` | Per-camera detections | Real-time |
| `system_error` | System errors | Instant |

---

## Component Integration Examples

### Dashboard - Real-Time Drone Tracking

```typescript
import { useSystemStore } from '../store/systemStore';

function Dashboard() {
  const drones = useSystemStore(state => state.drones);
  const alerts = useSystemStore(state => state.alerts);
  
  return (
    <div>
      {drones.map(drone => (
        <DroneMarker 
          key={drone.drone_id}
          position={[drone.position.lat, drone.position.lon]}
          status={drone.status}
          battery={drone.battery}
        />
      ))}
    </div>
  );
}
```

### Camera Feed - MJPEG Stream

```typescript
import { apiService } from '../services/api';

function CameraFeed({ camId }: { camId: string }) {
  const streamUrl = apiService.getCameraStreamUrl(camId);
  
  return (
    <img 
      src={streamUrl} 
      alt={`Camera ${camId}`}
      className="w-full h-auto"
    />
  );
}
```

### SOS - Create & Cancel

```typescript
import { useSystemStore } from '../store/systemStore';

function SosButton() {
  const createSos = useSystemStore(state => state.createSos);
  
  const handleSos = async () => {
    await createSos({
      sender_id: 'user_123',
      message: 'Emergency',
      lat: 18.5286,
      lon: 73.8395,
      location_type: 'gps'
    });
  };
  
  return <button onClick={handleSos}>Send SOS</button>;
}
```

---

## Troubleshooting

### WebSocket Not Connecting

1. Check backend is running: `curl http://localhost:8000/health`
2. Verify `.env` file has correct URLs
3. Check browser console for connection errors
4. Ensure no firewall blocking WebSocket connections

### API Calls Failing

1. Verify backend URL in `.env`
2. Check CORS settings in backend
3. Inspect network tab in browser DevTools
4. Check backend logs for errors

### Data Not Updating

1. Check WebSocket connection status
2. Verify backend is emitting events
3. Check browser console for errors
4. Refresh page to reinitialize connection

### Performance Issues

1. Reduce WebSocket update frequency in backend
2. Implement data pagination for large lists
3. Use React.memo for expensive components
4. Check browser performance profiler

---

## Production Deployment

### Environment Variables

Update `.env` for production:

```env
VITE_API_BASE_URL=https://api.skyguard.example.com
VITE_WS_URL=wss://api.skyguard.example.com
```

### Build

```bash
npm run build
```

Output will be in `dist/` directory.

### Serve

```bash
npm run preview
```

Or use any static file server (nginx, Apache, etc.).

---

## Development Tips

### Hot Reload
- Frontend: Vite HMR (automatic)
- Backend: `--reload` flag (automatic)

### Debugging
- Use React DevTools for component inspection
- Use Redux DevTools for Zustand (with middleware)
- Check Network tab for API calls
- Monitor WebSocket frames in DevTools

### Testing API Integration

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test drones endpoint
curl http://localhost:8000/drones

# Create manual alert
curl -X POST http://localhost:8000/alerts/manual \
  -H "Content-Type: application/json" \
  -d '{"zone_id": "Zone-A", "anomaly_type": "crowd_anomaly", "severity": 0.85}'
```

---

## File Structure

```
src/
├── config/
│   └── api.ts              # API configuration & endpoints
├── services/
│   ├── api.ts              # REST API service
│   ├── websocket.ts        # WebSocket service
│   └── mockData.ts         # Mock data (legacy)
├── store/
│   └── systemStore.ts      # Zustand state management
├── types/
│   └── index.ts            # TypeScript types
├── components/             # React components
├── pages/                  # Page components
└── App.tsx                 # Main app with initialization

.env                        # Environment variables (ONLY FILE TO EDIT)
```

---

## Support

For issues or questions:
1. Check backend logs: `tail -f skyguard-v2/logs/app.log`
2. Check frontend console: Browser DevTools
3. Verify API documentation: `API_DOCUMENTATION.md`
4. Test endpoints manually with curl/Postman

---

## Summary

✅ Single `.env` file configuration  
✅ Automatic WebSocket reconnection  
✅ Real-time updates without manual refresh  
✅ Type-safe API integration  
✅ Centralized state management  
✅ Error handling & notifications  
✅ Production-ready architecture  

**You're all set! Just start the backend and frontend, and everything will work automatically.**
