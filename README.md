# SkyGuard: AI Drone Response & Urban Safety Platform

**Best Pitch Award, Inspiron 5.0** (national hackathon by CSI COEP Tech Student Chapter & Simplify Healthcare). Built by team INNOV3RS.

SkyGuard is a command platform that connects camera detections to drone dispatch. It watches camera feeds for unusual activity, scores each event against a historical baseline, decides which drones to send, and routes them around no-fly zones. A live dashboard lets a human operator monitor and control everything.

## Screenshots

| Dashboard | Dispatch map | Heatmap |
|---|---|---|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Dispatch map](docs/screenshots/dispatch.png) | ![Heatmap](docs/screenshots/heatmap.png) |

## How it works

```
Camera feeds -> YOLO11n detection -> Anomaly rules -> Poisson baseline score
     -> Alert (severity above threshold) -> Priority queue -> Drone selection
     -> No-fly-zone-aware routing -> Simulated drone flight -> Live dashboard
```

| Component | What it does |
|---|---|
| Detection engine | YOLO11n inference with rule-based anomalies: crowd surge, fight, person down, suspicious dwell time, weapon-class flag |
| Baseline engine | Poisson-based anomaly scoring with severity weights per anomaly type |
| Priority queue | Heap-based dispatch queue with severity decay; re-evaluates every 500 ms and can reallocate a drone mid-flight |
| Routing (CLSP) | Clustered Layered Shortest Path over a 100 m grid of Pune airspace; edges through no-fly zones are blocked |
| Geofence | Two no-fly zones (airport and military cantonment) built with Shapely |
| Heatmap | Gaussian KDE over past incidents with time-decay weighting |
| SOS flow | 30-second cancellation window, then automatic dispatch |
| Dashboard | Live drone positions, alerts, camera feeds, dispatch map, heatmap, logs and a simulation panel |

## Scope and limitations

This is a hackathon prototype. To be clear about what it is:

- **Drones are simulated.** Four drones fly in memory at a configured speed. No real drone hardware is connected.
- **Cameras:** the demo uses 8 feeds (1 RTSP stream and 7 looped video files).
- **Detection model:** YOLO11n with the standard pretrained weights, not retrained. It has no firearm class, so the weapon rule only flags COCO classes such as knives and is approximate.
- **Performance:** frame rates in the config are targets. In our CPU-only test run the model processed about 3 frames per second.
- **Gemini triage** is an optional placeholder and is not required.

## Tech stack

- **Backend:** Python 3.11, FastAPI, python-socketio, SQLite (aiosqlite), Ultralytics YOLO11, OpenCV, NumPy, SciPy, Shapely
- **Frontend:** React 19, TypeScript, Vite, Zustand, Leaflet, Tailwind CSS, Socket.IO client
- **Deployment:** Docker (backend)

## Repository structure

```
.
├── backend/     # FastAPI app, detection, routing, queue, database (run from here)
├── frontend/    # React + TypeScript dashboard
└── docs/        # Screenshots and API notes
```

## Run locally

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # add your own values; never commit .env
python run_server.py
```

The API starts on port 8000 and picks the next free port if 8000 is busy.

**Frontend**

```bash
cd frontend
npm install
cp .env.example .env            # set VITE_API_BASE_URL and VITE_WS_URL
npm run dev
```

Open `http://localhost:5173`.

## Key API areas

Alerts, drones, cameras, detections, zones, heatmap, routes, SOS and health, with 40+ REST endpoints and real-time Socket.IO events for drone positions, alerts, heatmap updates and SOS countdowns. See `docs/API_DOCUMENTATION.md`.

## Team

Team INNOV3RS, GNDEC Bidar. Add each member's name and role here.

## License

Add a license (for example MIT) or state that the project is for demonstration only.
