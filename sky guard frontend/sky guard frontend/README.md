# SkyGuard Frontend - Urban Drone Response Platform

A real-time web application for monitoring and controlling autonomous drone responses to urban incidents, built with React, TypeScript, and WebSocket integration.

![SkyGuard](https://img.shields.io/badge/Status-Production%20Ready-green)
![React](https://img.shields.io/badge/React-19.2-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue)
![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-orange)

---

## 🚀 Quick Start

### Prerequisites
- Node.js v18+ 
- Backend server running on `http://localhost:8000`

### Installation

```bash
# 1. Install dependencies
npm install

# 2. Configure environment (already done)
# Edit .env if backend URL is different

# 3. Start development server
npm run dev
```

**That's it!** Open `http://localhost:5173` in your browser.

---

## 📚 Documentation

- **[SETUP.md](./SETUP.md)** - Complete setup guide with troubleshooting
- **[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)** - Detailed API integration documentation
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - Backend API reference

---

## ✨ Features

### Real-Time Monitoring
- 🚁 Live drone position tracking (500ms updates)
- 🚨 Instant alert notifications
- 📹 Real-time camera detection streams
- 🗺️ Dynamic heatmap with AI predictions
- 📊 Live system metrics and statistics

### Drone Operations
- Dispatch drones to incidents
- Reroute drones mid-flight
- Return to launch (RTL)
- Battery and status monitoring
- Mission history tracking

### Incident Management
- Automatic anomaly detection
- Manual alert creation
- Alert resolution workflow
- Severity-based prioritization
- Multi-drone coordination

### SOS System
- 30-second cancellation buffer
- GPS location tracking
- Automatic drone dispatch
- Real-time countdown timer
- Status tracking

### Analytics
- KDE-based heatmap visualization
- AI-powered risk predictions
- Historical incident analysis
- Zone-based statistics
- Baseline anomaly detection

---

## 🏗️ Architecture

### Tech Stack
- **Frontend**: React 19, TypeScript, Vite
- **State Management**: Zustand
- **Real-Time**: Socket.io-client
- **Maps**: Leaflet, React-Leaflet
- **Routing**: React Router v7
- **Styling**: Tailwind CSS
- **Icons**: Lucide React

### Project Structure
```
src/
├── config/          # API configuration
├── services/        # API & WebSocket services
├── store/           # Zustand state management
├── hooks/           # Custom React hooks
├── types/           # TypeScript definitions
├── components/      # React components
│   ├── cameras/     # Camera feed components
│   ├── dashboard/   # Dashboard widgets
│   ├── dispatch/    # Drone dispatch UI
│   ├── heatmap/     # Heatmap visualization
│   ├── layout/      # App layout components
│   ├── modals/      # Modal dialogs
│   ├── sos/         # SOS management
│   └── ui/          # Reusable UI components
└── pages/           # Route pages
```

---

## 🔌 API Integration

### Environment Configuration

Single `.env` file controls all API connections:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### WebSocket Events

Automatically subscribed events:
- `drone_update` - Drone positions (500ms)
- `alert_created` - New alerts (instant)
- `alert_updated` - Alert status changes
- `baseline_update` - Zone statistics (5s)
- `heatmap_update` - Heatmap data (30s)
- `sos_received` - SOS requests (instant)
- `sos_countdown` - SOS timer (1s)
- `drone_reallocated` - Drone reassignments
- `camera_offline/online` - Camera status
- `detection_stream` - Per-camera detections
- `system_error` - Error notifications

### API Services

```typescript
import { apiService } from './services/api';

// Fetch drones
const drones = await apiService.getDrones();

// Dispatch drone
await apiService.dispatchDrone('DR-01', {
  lat: 18.5204,
  lon: 73.8567,
  zone_id: 'Zone-A'
});

// Create SOS
await apiService.createSos({
  sender_id: 'user_123',
  message: 'Emergency',
  lat: 18.5286,
  lon: 73.8395,
  location_type: 'gps'
});
```

---

## 🎯 Key Components

### Dashboard
- Real-time drone map with trails
- Active incidents list
- System statistics
- Recent alerts feed
- Camera feed preview
- Engine performance metrics

### Cameras
- Multi-camera grid view
- MJPEG video streams
- Detection overlays
- Camera status table
- Real-time person counting

### Dispatch
- Interactive drone map
- Drone status table
- Manual dispatch controls
- Route visualization
- No-fly zone display

### Heatmap
- KDE-based visualization
- Hotspot identification
- AI risk predictions
- Zone statistics table
- Historical trends

### SOS
- SOS request map
- 30-second cancellation buffer
- Status tracking table
- Manual SOS creation
- Countdown timers

---

## 🔧 Development

### Available Scripts

```bash
npm run dev      # Start dev server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Lint code
```

### Adding New Features

1. **New API Endpoint**
   - Add to `src/config/api.ts`
   - Implement in `src/services/api.ts`
   - Add store action in `src/store/systemStore.ts`

2. **New WebSocket Event**
   - Add listener in `src/services/websocket.ts`
   - Handle in `src/store/systemStore.ts`
   - Update UI components

3. **New Component**
   - Create in appropriate `src/components/` subdirectory
   - Use Zustand hooks for state
   - Follow existing patterns

---

## 🐛 Troubleshooting

### WebSocket Not Connecting
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `.env` has correct URLs
3. Look for connection errors in browser console
4. Check firewall/antivirus settings

### Data Not Updating
1. Check connection status indicator (top-right)
2. Verify WebSocket is connected
3. Check backend is emitting events
4. Refresh page to reinitialize

### Camera Streams Not Loading
1. Verify camera endpoints: `curl http://localhost:8000/cameras`
2. Check MJPEG stream URLs are accessible
3. Ensure backend cameras are configured

See **[SETUP.md](./SETUP.md)** for detailed troubleshooting.

---

## 📦 Production Deployment

### Build

```bash
npm run build
```

Output: `dist/` directory

### Environment

Update `.env` for production:

```env
VITE_API_BASE_URL=https://api.skyguard.example.com
VITE_WS_URL=wss://api.skyguard.example.com
```

### Deploy

Upload `dist/` contents to your web server. Ensure:
- SPA routing configured (serve `index.html` for all routes)
- WebSocket support enabled
- CORS configured for API domain
- HTTPS/WSS in production

---

## 🔒 Security

- HTTPS/WSS in production
- No sensitive data in localStorage
- Input validation on all forms
- CORS configured on backend
- Type-safe API calls

---

## 📊 Performance

- WebSocket for real-time updates (no polling)
- Efficient state management with Zustand
- Vite for fast builds and HMR
- Lazy loading for routes
- Optimized re-renders with React.memo

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

This project is part of the SkyGuard V2 system.

---

## 🙏 Acknowledgments

- React team for React 19
- Leaflet for mapping
- Socket.io for WebSocket
- Zustand for state management
- Tailwind CSS for styling

---

## 📞 Support

For issues or questions:
1. Check [SETUP.md](./SETUP.md) for common issues
2. Review [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)
3. Check backend logs
4. Open an issue on GitHub

---

**Built with ❤️ for urban safety and rapid response**
