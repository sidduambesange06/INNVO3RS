"""SkyGuard V2 — Priority Queue with Mid-Flight Reallocation.

Heap-based queue that re-evaluates every 500ms.
Supports severity decay, reallocation thresholds, and weapon/person_down priority override.
"""

import heapq
import time
import uuid
from typing import Optional
from dataclasses import dataclass, field

from app.models.enums import DroneStatus, AnomalyType
from app.db import crud
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass(order=True)
class QueueItem:
    neg_score: float  # Negative for max-heap behavior
    created_at: float = field(compare=False)
    alert_id: str = field(compare=False)
    zone_id: str = field(compare=False)
    anomaly_type: str = field(compare=False)
    severity: float = field(compare=False)
    location: dict = field(compare=False, default_factory=dict)
    primary_drone: Optional[str] = field(compare=False, default=None)
    secondary_drone: Optional[str] = field(compare=False, default=None)
    assigned: bool = field(compare=False, default=False)
    dispatched: bool = field(compare=False, default=False)  # Track if drones are actually flying


class DroneDispatchQueue:
    """Priority queue for drone dispatch with reallocation."""

    def __init__(self, severity_decay: float = 0.995, reallocation_threshold: float = 0.15):
        self._heap: list[QueueItem] = []
        self._items: dict[str, QueueItem] = {}  # alert_id -> QueueItem
        self.severity_decay = severity_decay
        self.reallocation_threshold = reallocation_threshold
        self._drone_sim = None  # Set by main.py
        self._airspace_graph = None  # Set by main.py
        self._geofence = None  # Set by main.py

    def set_drone_simulator(self, drone_sim) -> None:
        self._drone_sim = drone_sim

    def set_airspace_graph(self, graph) -> None:
        """Set reference to airspace graph for route computation during reroute."""
        self._airspace_graph = graph

    def set_geofence(self, geofence) -> None:
        """Set geofence for NFZ-aware routing."""
        self._geofence = geofence

    def push(self, alert_id: str, zone_id: str, anomaly_type: str, severity: float,
             location: dict, primary_drone: str = None, secondary_drone: str = None) -> None:
        """Add an alert to the priority queue."""
        item = QueueItem(
            neg_score=-severity,
            created_at=time.time(),
            alert_id=alert_id,
            zone_id=zone_id,
            anomaly_type=anomaly_type,
            severity=severity,
            location=location,
            primary_drone=primary_drone,
            secondary_drone=secondary_drone,
            assigned=primary_drone is not None,
            dispatched=primary_drone is not None,  # If drone was assigned at push, it's dispatched
        )
        heapq.heappush(self._heap, item)
        self._items[alert_id] = item
        logger.info(f"📋 Queue push: {alert_id} severity={severity:.2f} drones=[{primary_drone}, {secondary_drone}]")

    async def re_evaluate(self) -> list[dict]:
        """Called every 500ms. Update drone positions + re-evaluate queue."""
        reallocations = []

        if not self._drone_sim:
            return reallocations

        # Update drone positions
        self._drone_sim.update_positions()

        # Clean up stale items (resolved/cancelled alerts, or items older than 10 minutes)
        stale_cutoff = time.time() - 600
        stale_ids = [
            aid for aid, item in self._items.items()
            if item.created_at < stale_cutoff and not item.assigned
        ]
        for aid in stale_ids:
            del self._items[aid]

        # Decay severity for all items
        for item in self._items.values():
            item.severity *= self.severity_decay
            item.neg_score = -item.severity

        # --- Phase 1: Check reallocation for assigned en-route drones ---
        for alert_id, item in list(self._items.items()):
            if not item.assigned or not item.primary_drone:
                continue

            drone = self._drone_sim.get_drone(item.primary_drone)
            if not drone:
                # Drone doesn't exist, mark unassigned
                item.primary_drone = None
                item.assigned = False
                item.dispatched = False
                continue

            # Skip if hovering, returning, or idle (mission completed or returned)
            if drone.status not in (DroneStatus.EN_ROUTE, DroneStatus.REROUTING):
                # If drone is idle/returning but alert is still assigned, clean up
                if drone.status in (DroneStatus.IDLE, DroneStatus.RETURNING):
                    if drone.assigned_alert_id != alert_id:
                        item.primary_drone = None
                        item.assigned = False
                        item.dispatched = False
                continue

            # Check all unassigned higher-priority alerts for reallocation
            for candidate_id, candidate in self._items.items():
                if candidate_id == alert_id or candidate.assigned:
                    continue

                should = self._should_reallocate(drone, item, candidate)
                if should:
                    old_eta = drone.eta_seconds
                    new_route = None
                    new_eta = 0

                    # Compute new route from drone's CURRENT position to candidate's location
                    cand_lat = candidate.location.get("lat", 0)
                    cand_lon = candidate.location.get("lon", 0)

                    if self._airspace_graph and cand_lat and cand_lon:
                        from app.core.routing import clsp_shortest_path
                        new_route = clsp_shortest_path(
                            self._airspace_graph,
                            drone.position["lat"], drone.position["lon"],
                            cand_lat, cand_lon
                        )
                        new_eta = new_route.get("estimated_time_s", 0)
                        waypoints = new_route.get("waypoints", [])
                    else:
                        # Direct route fallback
                        waypoints = [{"lat": cand_lat, "lon": cand_lon}]

                    # Actually reroute the drone in the simulator
                    rerouted = self._drone_sim.reroute_drone(
                        drone.id, cand_lat, cand_lon, waypoints, candidate_id
                    )

                    if rerouted:
                        # Update queue bookkeeping
                        item.primary_drone = None
                        item.assigned = False
                        item.dispatched = False
                        candidate.primary_drone = drone.id
                        candidate.assigned = True
                        candidate.dispatched = True

                        realloc = {
                            "drone_id": drone.id,
                            "from_alert_id": alert_id,
                            "to_alert_id": candidate_id,
                            "reason": f"Severity diff: {candidate.severity - item.severity:.2f}",
                            "old_eta": round(old_eta, 1),
                            "new_eta": round(new_eta, 1),
                        }
                        reallocations.append(realloc)

                        # Log mission for reroute
                        try:
                            mission_id = f"MSN-{candidate_id}-{drone.id}"
                            await crud.create_mission(
                                mission_id=mission_id,
                                alert_id=candidate_id,
                                drone_id=drone.id,
                                role="primary_reroute",
                                waypoints=waypoints,
                                nfz_avoided=new_route.get("no_fly_zones_avoided", []) if new_route else [],
                                algorithm="CLSP_reroute",
                                distance_m=new_route.get("total_distance_m", 0) if new_route else 0,
                                eta_s=new_eta,
                            )
                        except Exception as e:
                            logger.debug(f"Mission log failed: {e}")

                        # Log to DB
                        await crud.log_reallocation(
                            drone.id, alert_id, candidate_id,
                            realloc["reason"], old_eta, new_eta
                        )
                        logger.info(f"🔄 Reallocated {drone.id}: {alert_id} → {candidate_id} "
                                    f"(old ETA={old_eta:.0f}s, new ETA={new_eta:.0f}s)")
                        break
                    else:
                        logger.warning(f"Reroute failed for {drone.id}")

        # --- Phase 2: Assign IDLE drones to unassigned alerts ---
        unassigned = sorted(
            [item for item in self._items.values() if not item.assigned],
            key=lambda x: x.neg_score
        )
        for item in unassigned:
            if not self._drone_sim:
                break
            lat = item.location.get("lat", 0)
            lon = item.location.get("lon", 0)
            if not lat or not lon:
                continue

            primary, secondary = self._drone_sim.select_drone_pair(lat, lon)
            if primary:
                drone = self._drone_sim.get_drone(primary)
                if drone and drone.status == DroneStatus.IDLE:
                    # Compute route and actually dispatch
                    if self._airspace_graph:
                        from app.core.routing import clsp_shortest_path
                        route = clsp_shortest_path(
                            self._airspace_graph,
                            drone.position["lat"], drone.position["lon"],
                            lat, lon
                        )
                        waypoints = route.get("waypoints", [])
                    else:
                        waypoints = [{"lat": lat, "lon": lon}]
                        route = {"total_distance_m": 0, "estimated_time_s": 0, "no_fly_zones_avoided": []}

                    dispatched = self._drone_sim.dispatch_drone(
                        primary, item.alert_id, item.zone_id, lat, lon, waypoints
                    )
                    if dispatched:
                        item.primary_drone = primary
                        item.secondary_drone = secondary
                        item.assigned = True
                        item.dispatched = True

                        # Log mission
                        try:
                            mission_id = f"MSN-{item.alert_id}-{primary}"
                            await crud.create_mission(
                                mission_id=mission_id,
                                alert_id=item.alert_id,
                                drone_id=primary,
                                role="primary_queue",
                                waypoints=waypoints,
                                nfz_avoided=route.get("no_fly_zones_avoided", []),
                                algorithm="CLSP",
                                distance_m=route.get("total_distance_m", 0),
                                eta_s=route.get("estimated_time_s", 0),
                            )
                        except Exception as e:
                            logger.debug(f"Mission log failed: {e}")

                        logger.info(f"🚀 Queue dispatched {primary} to {item.alert_id}")

                    # Dispatch secondary if available and idle
                    if secondary and dispatched:
                        sec_drone = self._drone_sim.get_drone(secondary)
                        if sec_drone and sec_drone.status == DroneStatus.IDLE:
                            if self._airspace_graph:
                                sec_route = clsp_shortest_path(
                                    self._airspace_graph,
                                    sec_drone.position["lat"], sec_drone.position["lon"],
                                    lat, lon
                                )
                                sec_waypoints = sec_route.get("waypoints", [])
                            else:
                                sec_waypoints = [{"lat": lat, "lon": lon}]
                                sec_route = {"total_distance_m": 0, "estimated_time_s": 0, "no_fly_zones_avoided": []}

                            self._drone_sim.dispatch_drone(
                                secondary, item.alert_id, item.zone_id, lat, lon, sec_waypoints
                            )
                            try:
                                await crud.create_mission(
                                    mission_id=f"MSN-{item.alert_id}-{secondary}",
                                    alert_id=item.alert_id,
                                    drone_id=secondary,
                                    role="secondary_queue",
                                    waypoints=sec_waypoints,
                                    nfz_avoided=sec_route.get("no_fly_zones_avoided", []),
                                    algorithm="CLSP",
                                    distance_m=sec_route.get("total_distance_m", 0),
                                    eta_s=sec_route.get("estimated_time_s", 0),
                                )
                            except Exception:
                                pass

        return reallocations

    def _should_reallocate(self, drone, current_item: QueueItem, candidate_item: QueueItem) -> bool:
        """Check if a drone should be reallocated to a new alert."""
        severity_diff = candidate_item.severity - current_item.severity

        # Standard threshold check
        if (severity_diff > self.reallocation_threshold and
                drone.eta_seconds > 30 and
                drone.battery > 30 and
                drone.status != DroneStatus.HOVERING):
            return True

        # Critical anomaly override — weapon or person down always escalate
        if (candidate_item.anomaly_type in (AnomalyType.WEAPON_DETECT.value, AnomalyType.PERSON_DOWN.value) and
                drone.eta_seconds > 10):
            return True

        return False

    def get_queue_snapshot(self) -> list[dict]:
        """Get current queue state for API response."""
        items = sorted(self._items.values(), key=lambda x: x.neg_score)
        return [{
            "alert_id": item.alert_id,
            "zone_id": item.zone_id,
            "anomaly_type": item.anomaly_type,
            "severity": round(item.severity, 2),
            "primary_drone": item.primary_drone,
            "secondary_drone": item.secondary_drone,
            "assigned": item.assigned,
            "dispatched": item.dispatched,
            "age_s": round(time.time() - item.created_at, 1),
        } for item in items]

    def remove(self, alert_id: str) -> None:
        """Remove an alert from the queue."""
        if alert_id in self._items:
            del self._items[alert_id]
