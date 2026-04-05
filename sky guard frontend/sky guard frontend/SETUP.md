# SkyGuard Frontend - Complete Setup Guide

## Prerequisites

- Node.js v18+ (you have v18.18.0)
- Backend server running on `http://localhost:8000`
- npm or yarn package manager

---

## Step-by-Step Setup

### 1. Install Dependencies

```bash
npm install
```

This installs all required packages including:
- React 19
- Socket.io-client (WebSocket)
- Zustand (State management)
- React Router
- Leaflet (Maps)
- And more...

### 2. Configure Environment

The `.env` file is already created with default values:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

**If your backend runs on a different port or host, update these values.**

### 3. Start Backend Server

In your backend directory:

```bash
cd skyguard-v2
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify backend is running:
```bash
curl http://localhost:8000/health
```

### 4. Start Frontend Development Server

```bash
npm run dev
```

The app will open at `http://localhost:5173`

---

## What Happens on Startup

1. **App Initialization** (`src/App.tsx`)
   - Shows loading screen
   - Calls `initialize()` from store

2. **Store Initialization** (`src/store/systemStore.ts`)
   - Connects to WebSocket server
   - Sets up real-time event listeners
   - Fetches initial data from API:
     - Drones
     - Alerts
     - Cameras
     - SOS requests
     - Zones
     - Heatmap

3. **WebSocket Connection** (`src/services/websocket.ts`)
   - Establishes Socket.io connection
   - Subscribes to all real-time events
   - Auto-reconnects on disconnect

4. **Real-Time Updates**
   - Drone positions update every 500ms
   - Alerts appear instantly
   - Camera feeds stream continuously
   - Heatmap updates every 30s

---

## Verification Checklist

### ✅ Backend Health
```bash
curl http://localhost:8000/health
```
Expected: `{"status": "healthy", ...}`

### ✅ WebSocket Connection
Open browser console and look for:
```
Connecting to WebSocket: ws://localhost:8000
WebSocket connected
```

### ✅ API Calls
Check Network tab in DevTools:
- `/drones` - Should return drone list
- `/alerts` - Should return alerts
- `/cameras` - Should return cameras

### ✅ Real-Time Updates
Watch the connection status indicator in the top-right:
- 🟢 LIVE = Connected
- 🔴 DISCONNECTED = Not connected

---

## Project Structure

```
sky-guard-frontend/
├── .env                          # ⚙️ ONLY FILE YOU NEED TO EDIT
├── .env.example                  # Template for .env
├── src/
│   ├── config/
│   │   └── api.ts               # API endpoints configuration
│   ├── services/
│   │   ├── api.ts               # REST API service
│   │   └── websocket.ts         # WebSocket service
│   ├── store/
│   │   └── systemStore.ts       # Zustand state management
│   ├── hooks/
│   │   └── useWebSocket.ts      # WebSocket hooks
│   ├── types/
│   │   └── index.ts             # TypeScript types
│   ├── components/              # React components
│   ├── pages/                   # Page components
│   └── App.tsx                  # Main app
├── API_DOCUMENTATION.md          # Backend API reference
├── INTEGRATION_GUIDE.md          # Detailed integration guide
└── SETUP.md                      # This file
```

---

## Available Scripts

```bash
# Development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

---

## Features Implemented

### ✅ Real-Time Communication
- WebSocket connection with auto-reconnect
- Live drone position updates (500ms)
- Instant alert notifications
- Real-time camera detection streams
- SOS countdown timers

### ✅ API Integration
- All REST endpoints connected
- Type-safe API calls
- Error handling with toast notifications
- Automatic data refresh

### ✅ State Management
- Centralized Zustand store
- Automatic state updates from WebSocket
- Optimistic UI updates
- Persistent connection status

### ✅ UI Components
- Connection status indicator
- Loading states
- Toast notifications
- Action modals
- Real-time data displays

---

## Common Issues & Solutions

### Issue: "Cannot connect to backend"

**Solution:**
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify `.env` has correct URL
3. Check firewall/antivirus not blocking port 8000

### Issue: "WebSocket disconnected"

**Solution:**
1. Backend might have crashed - check backend logs
2. Network issue - check internet connection
3. Will auto-reconnect in 2 seconds (max 5 attempts)

### Issue: "Data not updating"

**Solution:**
1. Check connection status indicator (top-right)
2. Open browser console for errors
3. Verify backend is emitting WebSocket events
4. Refresh page to reinitialize

### Issue: "Camera streams not loading"

**Solution:**
1. Check camera endpoints: `curl http://localhost:8000/cameras`
2. Verify MJPEG stream URL is accessible
3. Check browser supports MJPEG (all modern browsers do)

---

## Development Workflow

### Making Changes

1. **Edit code** - Vite will hot-reload automatically
2. **Check console** - Look for errors
3. **Test API calls** - Use Network tab
4. **Verify WebSocket** - Check WS frames in DevTools

### Adding New API Endpoints

1. Add endpoint to `src/config/api.ts`
2. Add method to `src/services/api.ts`
3. Add action to `src/store/systemStore.ts`
4. Use in components

### Adding New WebSocket Events

1. Add event listener in `src/services/websocket.ts`
2. Add handler in `src/store/systemStore.ts` initialize()
3. Update state based on event data

---

## Production Deployment

### 1. Update Environment

Create `.env.production`:

```env
VITE_API_BASE_URL=https://api.skyguard.example.com
VITE_WS_URL=wss://api.skyguard.example.com
```

### 2. Build

```bash
npm run build
```

Output: `dist/` directory

### 3. Deploy

Upload `dist/` contents to your web server (nginx, Apache, Vercel, Netlify, etc.)

### 4. Configure Server

Ensure your server:
- Serves `index.html` for all routes (SPA routing)
- Supports WebSocket connections
- Has CORS configured for API domain

---

## Testing

### Manual Testing

1. **Drone Dispatch**
   - Go to Dispatch page
   - Click on a drone
   - Dispatch to location
   - Verify drone moves on map

2. **Alert Creation**
   - Backend will auto-create alerts
   - Or use API: `POST /alerts/manual`
   - Verify alert appears in dashboard

3. **SOS Flow**
   - Go to SOS page
   - Create SOS request
   - Wait 30 seconds or cancel
   - Verify drone dispatches

4. **Camera Feeds**
   - Go to Cameras page
   - Verify video streams load
   - Check detection overlays

### API Testing

```bash
# Create manual alert
curl -X POST http://localhost:8000/alerts/manual \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": "Zone-A",
    "anomaly_type": "crowd_anomaly",
    "severity": 0.85
  }'

# Dispatch drone
curl -X POST http://localhost:8000/drones/DR-01/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 18.5204,
    "lon": 73.8567,
    "zone_id": "Zone-A"
  }'

# Create SOS
curl -X POST http://localhost:8000/sos \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "test_user",
    "message": "Emergency",
    "lat": 18.5286,
    "lon": 73.8395,
    "location_type": "gps"
  }'
```

---

## Performance Optimization

### Current Optimizations

- WebSocket for real-time updates (no polling)
- Zustand for efficient state management
- React.memo for expensive components
- Lazy loading for routes
- Vite for fast builds

### Future Optimizations

- Implement data pagination
- Add virtual scrolling for large lists
- Use Web Workers for heavy computations
- Implement service worker for offline support

---

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Responsive design

---

## Security Considerations

- API calls use HTTPS in production
- WebSocket uses WSS in production
- No sensitive data in localStorage
- CORS configured on backend
- Input validation on all forms

---

## Support & Documentation

- **API Reference**: `API_DOCUMENTATION.md`
- **Integration Guide**: `INTEGRATION_GUIDE.md`
- **Backend Docs**: Check backend repository
- **React Docs**: https://react.dev
- **Vite Docs**: https://vitejs.dev

---

## Quick Start Summary

```bash
# 1. Install
npm install

# 2. Start backend (in backend directory)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Start frontend
npm run dev

# 4. Open browser
# http://localhost:5173
```

**That's it! Everything is configured and ready to go.**

---

## Next Steps

1. ✅ Backend running
2. ✅ Frontend running
3. ✅ WebSocket connected
4. ✅ Data flowing

Now you can:
- View real-time drone positions
- Monitor alerts and incidents
- Watch camera feeds
- Dispatch drones
- Handle SOS requests
- View heatmap analytics

**Enjoy using SkyGuard! 🚁**
