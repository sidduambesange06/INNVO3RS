"""
SkyGuard V2 — Alert Manager Service
Complete alert lifecycle: creation, drone assignment, SOS handling, and tracking.
"""
import asyncio
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from app.models.alert import Alert, AlertStatus
from app.models.sos import SOSEvent, SOSCreate, SOSStatus
from app.utils.logger import setup_logger
from app.db import crud

logger = setup_logger(__name__)


class AlertManager:
    """
    Complete alert lifecycle manager with SOS support.
    """
    def __init__(self, priority_queue=None, baseline_engine=None, drone_sim=None, geofence=None, airspace_graph=None):
        self.priority_queue = priority_queue
        self.baseline_engine = baseline_engine
        self.drone_sim = drone_sim
        self.geofence = geofence
        self.airspace_graph = airspace_graph
        self._alerts: Dict[str, Alert] = {}
        self._sos_events: Dict[str, SOSEvent] = {}
        self._sos_tasks: Dict[str, asyncio.Task] = {}
        self._alert_counter = 0
        self._sos_counter = 0
        self._lock = threading.Lock()
        self.severity_threshold = 0.4

    async def create_from_detection(
        self,
        cam_id: str,
        zone_id: str,
        zone_name: str,
        anomaly_type: str,
        severity: float,
        current_count: int,
        baseline_mean: float,
        z_score: float,
        location_lat: float,
        location_lon: float,
    ) -> Optional[Alert]:
        """Create alert from camera detection with full drone dispatch."""
        if severity < self.severity_threshold:
            return None

        # Check for recent alert in same zone (deduplication)
        recent = await crud.get_active_alert_for_zone(zone_id, seconds_ago=30)
        if recent:
            logger.info(f"Skipping alert for {zone_id} - recent alert exists")
            return None

        with self._lock:
            self._alert_counter += 1
            now = datetime.now(timezone.utc)
            alert_id = f"AL-{now.strftime('%Y%m%d-%H%M%S')}-{self._alert_counter:03d}"

        location = {"lat": location_lat, "lon": location_lon}

        # Select drone pair
        primary_drone, secondary_drone = None, None
        primary_eta, secondary_eta = None, None
        routes = []

        if self.drone_sim:
            primary_id, secondary_id = self.drone_sim.select_drone_pair(location_lat, location_lon)

            if primary_id and self.airspace_graph:
                from app.core.routing import clsp_shortest_path
                drone = self.drone_sim.get_drone(primary_id)
                route = clsp_shortest_path(
                    self.airspace_graph,
                    drone.position["lat"], drone.position["lon"],
                    location_lat, location_lon
                )
                primary_drone = primary_id
                primary_eta = route.get("estimated_time_s", 0)
                routes.append({"drone_id": primary_id, "role": "primary", **route})

                # Dispatch primary drone
                dispatched = self.drone_sim.dispatch_drone(
                    primary_id, alert_id, zone_id,
                    location_lat, location_lon,
                    route.get("waypoints", [])
                )

                if dispatched:
                    # Log mission
                    try:
                        mission_id = f"MSN-{alert_id}-{primary_id}"
                        await crud.create_mission(
                            mission_id=mission_id,
                            alert_id=alert_id,
                            drone_id=primary_id,
                            role="primary",
                            waypoints=route.get("waypoints", []),
                            nfz_avoided=route.get("no_fly_zones_avoided", []),
                            algorithm="CLSP",
                            distance_m=route.get("total_distance_m", 0),
                            eta_s=primary_eta,
                        )
                    except Exception as e:
                        logger.debug(f"Mission log failed: {e}")
                else:
                    primary_drone = None
                    primary_eta = None
                    logger.warning(f"Failed to dispatch primary drone {primary_id}")

            if secondary_id and self.airspace_graph:
                drone = self.drone_sim.get_drone(secondary_id)
                route = clsp_shortest_path(
                    self.airspace_graph,
                    drone.position["lat"], drone.position["lon"],
                    location_lat, location_lon
                )
                secondary_drone = secondary_id
                secondary_eta = route.get("estimated_time_s", 0)
                routes.append({"drone_id": secondary_id, "role": "secondary", **route})

                # Dispatch secondary drone
                dispatched = self.drone_sim.dispatch_drone(
                    secondary_id, alert_id, zone_id,
                    location_lat, location_lon,
                    route.get("waypoints", [])
                )

                if dispatched:
                    try:
                        mission_id = f"MSN-{alert_id}-{secondary_id}"
                        await crud.create_mission(
                            mission_id=mission_id,
                            alert_id=alert_id,
                            drone_id=secondary_id,
                            role="secondary",
                            waypoints=route.get("waypoints", []),
                            nfz_avoided=route.get("no_fly_zones_avoided", []),
                            algorithm="CLSP",
                            distance_m=route.get("total_distance_m", 0),
                            eta_s=secondary_eta,
                        )
                    except Exception as e:
                        logger.debug(f"Mission log failed: {e}")
                else:
                    secondary_drone = None
                    secondary_eta = None

        # Create alert
        alert = Alert(
            alert_id=alert_id,
            zone_id=zone_id,
            zone_name=zone_name,
            cam_id=cam_id,
            anomaly_type=anomaly_type,
            severity=round(severity, 2),
            current_count=current_count,
            baseline_mean=round(baseline_mean, 2),
            z_score=round(z_score, 2),
            location=location,
            primary_drone=primary_drone,
            secondary_drone=secondary_drone,
            primary_eta=primary_eta,
            secondary_eta=secondary_eta,
            status=AlertStatus.ACTIVE,
            source="camera",
            routes=routes,
        )

        # Store alert
        self._alerts[alert_id] = alert

        # Save to database
        await crud.create_alert(
            alert_id=alert_id,
            zone_id=zone_id,
            cam_id=cam_id,
            anomaly_type=anomaly_type,
            severity=severity,
            current_count=current_count,
            baseline_mean=baseline_mean,
            z_score=z_score,
            location_lat=location_lat,
            location_lon=location_lon,
            source="camera",
        )

        # Save to heatmap events
        await crud.create_heatmap_event(
            lat=location_lat,
            lon=location_lon,
            zone_id=zone_id,
            anomaly_type=anomaly_type,
            severity=severity,
            hour=now.hour,
            day_of_week=now.weekday(),
        )

        # Emit WebSocket event
        from app.services.websocket import emit_alert_created
        await emit_alert_created(alert.to_ws_dict())

        # Add to priority queue
        if self.priority_queue:
            self.priority_queue.push(
                alert_id, zone_id, anomaly_type, severity,
                location, primary_drone, secondary_drone
            )

        drones_info = f"drones=[{primary_drone}, {secondary_drone}]"
        logger.info(
            f"🚨 Alert {alert_id}: {zone_name} severity={severity:.2f} "
            f"{drones_info}"
        )

        return alert

    async def create_manual_alert(
        self,
        zone_id: str,
        anomaly_type: str,
        severity: float,
    ) -> Optional[Alert]:
        """Create manual alert for testing/demo."""
        # Get zone info from database
        zone = await crud.get_zone(zone_id)
        if not zone:
            logger.error(f"Zone {zone_id} not found")
            return None

        return await self.create_from_detection(
            cam_id=zone.get("cam_id", f"CAM-{zone_id}"),
            zone_id=zone_id,
            zone_name=zone.get("name", zone_id),
            anomaly_type=anomaly_type,
            severity=severity,
            current_count=0,
            baseline_mean=0.0,
            z_score=0.0,
            location_lat=zone.get("centroid_lat", 18.52),
            location_lon=zone.get("centroid_lon", 73.85),
        )

    async def create_from_sos(self, sos_data: SOSCreate) -> SOSEvent:
        """Create SOS event with 30s countdown buffer."""
        with self._lock:
            self._sos_counter += 1
            now = datetime.now(timezone.utc)
            sos_id = f"SOS-{now.strftime('%Y%m%d-%H%M%S')}-{self._sos_counter:03d}"

        # Create SOS event
        sos = SOSEvent(
            sos_id=sos_id,
            sender_id=sos_data.sender_id,
            message=sos_data.message,
            location={"lat": sos_data.lat, "lon": sos_data.lon},
            location_type=sos_data.location_type,
            zone_id=sos_data.zone_id,
            status=SOSStatus.PENDING,
            buffer_seconds=30,
            seconds_remaining=30,
            created_at=now,
        )

        # Store SOS
        self._sos_events[sos_id] = sos

        # Save to database
        await crud.create_sos(
            sos_id=sos_id,
            sender_id=sos_data.sender_id,
            message=sos_data.message,
            lat=sos_data.lat,
            lon=sos_data.lon,
            location_type=sos_data.location_type,
            zone_id=sos_data.zone_id,
        )

        # Emit WebSocket event
        from app.services.websocket import emit_sos_received
        await emit_sos_received(sos.to_ws_dict())

        # Start countdown task
        task = asyncio.create_task(self._sos_countdown(sos_id))
        self._sos_tasks[sos_id] = task

        logger.info(f"📱 SOS {sos_id} created from {sos_data.sender_id}")
        return sos

    async def _sos_countdown(self, sos_id: str):
        """30-second countdown for SOS cancellation buffer."""
        from app.services.websocket import emit_sos_countdown, emit_sos_dispatched

        for seconds in range(30, 0, -1):
            sos = self._sos_events.get(sos_id)
            if not sos or sos.status != SOSStatus.PENDING:
                return  # Cancelled

            sos.seconds_remaining = seconds
            await emit_sos_countdown(sos_id, seconds)
            await asyncio.sleep(1)

        # Buffer expired - auto-dispatch
        sos = self._sos_events.get(sos_id)
        if sos and sos.status == SOSStatus.PENDING:
            # Create high-priority alert
            alert = await self.create_from_detection(
                cam_id="SOS",
                zone_id=sos.zone_id or "SOS-Zone",
                zone_name="SOS Location",
                anomaly_type="sos_emergency",
                severity=0.90,
                current_count=0,
                baseline_mean=0.0,
                z_score=0.0,
                location_lat=sos.location["lat"],
                location_lon=sos.location["lon"],
            )

            if alert:
                sos.status = SOSStatus.DISPATCHED
                sos.alert_id = alert.alert_id
                await crud.update_sos(sos_id, status="DISPATCHED", alert_id=alert.alert_id)
                await emit_sos_dispatched(sos.to_ws_dict(), alert.to_ws_dict())
                logger.info(f"📱 SOS {sos_id} auto-dispatched → {alert.alert_id}")

    async def cancel_sos(self, sos_id: str, reason: str) -> bool:
        """Cancel SOS within buffer window."""
        sos = self._sos_events.get(sos_id)
        if not sos or sos.status != SOSStatus.PENDING:
            return False

        # Cancel countdown task
        task = self._sos_tasks.get(sos_id)
        if task:
            task.cancel()
            del self._sos_tasks[sos_id]

        # Update status
        sos.status = SOSStatus.CANCELLED
        await crud.update_sos(sos_id, status="CANCELLED", cancel_reason=reason)

        # Emit WebSocket event
        from app.services.websocket import emit_sos_cancelled
        await emit_sos_cancelled(sos.to_ws_dict())

        logger.info(f"📱 SOS {sos_id} cancelled: {reason}")
        return True

    async def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """Resolve an alert and return drones."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None

        alert.status = AlertStatus.RESOLVED
        await crud.update_alert(alert_id, status="RESOLVED", resolved_at=datetime.now(timezone.utc).isoformat())

        # Return drones to base
        if self.drone_sim:
            if alert.primary_drone:
                self.drone_sim.rtl(alert.primary_drone)
            if alert.secondary_drone:
                self.drone_sim.rtl(alert.secondary_drone)

        # Remove from priority queue
        if self.priority_queue:
            self.priority_queue.remove(alert_id)

        # Emit WebSocket event
        from app.services.websocket import emit_alert_updated
        await emit_alert_updated(alert.to_ws_dict())

        logger.info(f"✅ Alert {alert_id} resolved")
        return alert

    def get_all_alerts(self) -> List[Alert]:
        """Get all alerts."""
        return list(self._alerts.values())

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID."""
        return self._alerts.get(alert_id)

    def get_sos_event(self, sos_id: str) -> Optional[SOSEvent]:
        """Get SOS event by ID."""
        return self._sos_events.get(sos_id)

    def get_all_sos(self) -> List[SOSEvent]:
        """Get all SOS events."""
        return list(self._sos_events.values())
