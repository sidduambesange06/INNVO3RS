# SkyGuard Frontend - Quick Reference Card

## 🚀 One-Command Setup

```bash
npm install && npm run dev
```

**Prerequisites**: Backend running on `http://localhost:8000`

---

## 📁 Single Configuration File

**`.env`** - The ONLY file you need to edit:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## 🔌 Connection Status

Look for indicator in top-right corner:
- 🟢 **LIVE** = Connected and receiving real-time updates
- 🔴 **DISCONNECTED** = Not connected to backend

---

## 📡 Real-Time Update Frequencies

| Data | Update Frequency |
|------|------------------|
| Drone positions | 500ms |
| Alerts | Instant |
| Camera detections | Real-time stream |
| Heatmap | 30 seconds |
| Zone statistics | 5 seconds |
| SOS countdown | 1 second |

---

## 🛠️ Common Commands

```bash
# Development
npm run dev              # Start dev server (http://localhost:5173)

# Production
npm run build            # Build for production
npm run preview          # Preview production build

# Code Quality
npm run lint             # Lint code
```

---

## 🔍 Quick Debugging

### Check Backend Health
```bash
curl http://localhost:8000/health
```

### Check WebSocket Connection
Open browser console, look for:
```
Connecting to WebSocket: ws://localhost:8000
WebSocket connected
```

### Check API Calls
Open DevTools → Network tab → Filter by "Fetch/XHR"

### Check WebSocket Events
Open DevTools → Network tab → Filter by "WS" → Click connection → Messages

---

## 📊 Key API Endpoints

```bash
# Drones
GET    /drones
POST   /drones/{id}/dispatch
POST   /drones/{id}/reroute
POST   /drones/{id}/rtl

# Alerts
GET    /alerts
POST   /alerts/manual
PATCH  /alerts/{id}/resolve

# SOS
GET    /sos
POST   /sos
POST   /sos/{id}/cancel

# Cameras
GET    /cameras
GET    /cameras/{id}/stream
GET    /cameras/{id}/detections

# Heatmap
GET    /heatmap
GET    /heatmap/predict
```

---

## 🎯 Component Usage Examples

### Get Drones from Store
```typescript
import { useSystemStore } from './store/systemStore';

const drones = useSystemStore(state => state.drones);
```

### Dispatch Drone
```typescript
const dispatchDrone = useSystemStore(state => state.dispatchDrone);

await dispatchDrone('DR-01', 18.5204, 73.8567, 'Zone-A');
```

### Subscribe to WebSocket Event
```typescript
import { useWebSocketEvent } from './hooks/useWebSocket';

useWebSocketEvent('alert_created', (data) => {
  console.log('New alert:', data);
});
```

### Get Camera Stream URL
```typescript
import { apiService } from './services/api';

const streamUrl = apiService.getCameraStreamUrl('CAM-01');
```

---

## 🐛 Troubleshooting Checklist

- [ ] Backend running? → `curl http://localhost:8000/health`
- [ ] `.env` file exists? → Check project root
- [ ] Correct URLs in `.env`? → Verify backend URL
- [ ] Dependencies installed? → Run `npm install`
- [ ] Port 5173 available? → Check for conflicts
- [ ] Browser console errors? → Open DevTools
- [ ] WebSocket connected? → Check connection indicator

---

## 📦 Project Structure (Simplified)

```
.env                    ← EDIT THIS
src/
  ├── config/api.ts     ← API endpoints
  ├── services/
  │   ├── api.ts        ← REST API calls
  │   └── websocket.ts  ← WebSocket connection
  ├── store/
  │   └── systemStore.ts ← State management
  └── components/       ← UI components
```

---

## 🔐 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend REST API URL | `http://localhost:8000` |
| `VITE_WS_URL` | Backend WebSocket URL | `ws://localhost:8000` |

**Production**: Use `https://` and `wss://` instead

---

## 📱 Pages & Routes

| Route | Page | Description |
|-------|------|-------------|
| `/dashboard` | Dashboard | Main overview with map |
| `/cameras` | Cameras | Camera feeds grid |
| `/dispatch` | Dispatch | Drone dispatch control |
| `/heatmap` | Heatmap | Risk visualization |
| `/sos` | SOS | Emergency requests |
| `/simulation` | Simulation | Test scenarios |
| `/logs` | Logs | System logs |

---

## 🎨 Key Features

✅ Real-time drone tracking  
✅ Live camera feeds  
✅ Instant alert notifications  
✅ SOS with 30s cancellation  
✅ AI-powered heatmap  
✅ Automatic reconnection  
✅ Type-safe API calls  
✅ Responsive design  

---

## 📚 Documentation Files

- **README.md** - Project overview
- **SETUP.md** - Detailed setup guide
- **INTEGRATION_GUIDE.md** - API integration details
- **API_DOCUMENTATION.md** - Backend API reference
- **QUICK_REFERENCE.md** - This file

---

## 🆘 Getting Help

1. Check **SETUP.md** for detailed troubleshooting
2. Review **INTEGRATION_GUIDE.md** for API issues
3. Check backend logs
4. Open browser DevTools console
5. Verify backend health endpoint

---

## ⚡ Performance Tips

- WebSocket handles all real-time updates (no polling)
- Data updates automatically (no manual refresh)
- Optimized re-renders with Zustand
- Lazy loading for routes
- Efficient state management

---

## 🔄 Update Workflow

1. Backend emits WebSocket event
2. Frontend receives event
3. Store updates automatically
4. Components re-render with new data
5. UI updates instantly

**No manual refresh needed!**

---

**Quick Start**: `npm install && npm run dev`  
**Documentation**: See SETUP.md  
**Support**: Check browser console & backend logs
