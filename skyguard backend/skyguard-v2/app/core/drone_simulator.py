"""SkyGuard V2 — Drone Simulator.
Manages 4 drones in memory. Simulates flight along waypoints at 15 m/s.
"""
import time
from typing import Optional
from app.models.drone import DroneState, Waypoint
from app.models.enums import DroneStatus
from app.utils.haversine import haversine_distance, interpolate_position
from app.db import crud
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DroneSimulator:
    """Simulates 4 drones with position interpolation, battery drain, and hover timers."""

    def __init__(self, speed_ms: float = 15.0, min_battery: int = 20, hover_time_s: int = 30):
        self.speed_ms = speed_ms
        self.min_battery = min_battery
        self.hover_time_s = hover_time_s
        self.drones: dict[str, DroneState] = {}
        self._last_update = time.time()

    async def initialize_from_db(self) -> None:
        """Load drones from database."""
        rows = await crud.get_all_drones()
        for row in rows:
            drone = DroneState(
                id=row["drone_id"],
                position={"lat": row["current_lat"], "lon": row["current_lon"], "alt": row.get("altitude", 50.0)},
                home_base={"lat": row["home_lat"], "lon": row["home_lon"]},
                battery=row.get("battery", 100),
                status=DroneStatus(row.get("status", "IDLE")),
                speed_ms=row.get("speed_ms", self.speed_ms),
            )
            self.drones[drone.id] = drone
        logger.info(f"✅ DroneSimulator: {len(self.drones)} drones initialized")

    def update_positions(self) -> None:
        """Called every ~500ms. Move drones along routes using wall-clock dt (capped for stability)."""
        now = time.time()
        raw_dt = now - self._last_update
        self._last_update = now
        # Avoid huge jumps if the asyncio loop stalls
        dt = min(max(raw_dt, 0.0), 2.0)

        for drone_id, drone in self.drones.items():
            if drone.status == DroneStatus.EN_ROUTE:
                self._move_along_route(drone, dt)
            elif drone.status == DroneStatus.REROUTING:
                self._move_along_route(drone, dt)
                # After first successful waypoint advance, transition to EN_ROUTE
                if drone.route_index > 0:
                    drone.status = DroneStatus.EN_ROUTE
            elif drone.status == DroneStatus.HOVERING:
                self._handle_hover(drone, dt)
            elif drone.status == DroneStatus.RETURNING:
                self._move_to_home(drone, dt)
            elif drone.status == DroneStatus.IDLE:
                self._charge_battery(drone, dt)

            # Battery critical check
            if drone.battery < self.min_battery and drone.status not in (DroneStatus.RETURNING, DroneStatus.IDLE):
                logger.warning(f"🔋 {drone_id} battery critical ({drone.battery}%), forcing RTL")
                self._start_return(drone)

    def _move_along_route(self, drone: DroneState, dt: float) -> None:
        """Move drone along its route waypoints."""
        if not drone.current_route or drone.route_index >= len(drone.current_route):
            # Arrived at destination
            drone.status = DroneStatus.HOVERING
            drone.hover_timer = self.hover_time_s
            drone.eta_seconds = 0
            drone.distance_remaining_m = 0
            logger.info(f"🛸 {drone.id} arrived at target, hovering for {self.hover_time_s}s")
            return

        # Distance to move this tick
        move_distance = drone.speed_ms * dt

        # Consume waypoints until move_distance is exhausted
        while move_distance > 0 and drone.route_index < len(drone.current_route):
            target_wp = drone.current_route[drone.route_index]
            current_lat = drone.position["lat"]
            current_lon = drone.position["lon"]
            target_lat = target_wp.lat
            target_lon = target_wp.lon
            dist_to_target = haversine_distance(current_lat, current_lon, target_lat, target_lon)

            if dist_to_target <= move_distance:
                # Reached this waypoint, advance to next
                drone.position["lat"] = target_lat
                drone.position["lon"] = target_lon
                drone.route_index += 1
                move_distance -= dist_to_target
            else:
                # Interpolate position toward current waypoint
                fraction = move_distance / max(dist_to_target, 0.01)
                new_lat, new_lon = interpolate_position(current_lat, current_lon, target_lat, target_lon, fraction)
                drone.position["lat"] = round(new_lat, 6)
                drone.position["lon"] = round(new_lon, 6)
                move_distance = 0  # All movement consumed

        # Update remaining distance and ETA
        remaining = 0.0
        if drone.route_index < len(drone.current_route):
            lat, lon = drone.position["lat"], drone.position["lon"]
            for i in range(drone.route_index, len(drone.current_route)):
                wp = drone.current_route[i]
                remaining += haversine_distance(lat, lon, wp.lat, wp.lon)
                lat, lon = wp.lat, wp.lon

        drone.distance_remaining_m = round(remaining, 1)
        drone.eta_seconds = round(remaining / max(drone.speed_ms, 0.01), 1)

        # Battery drain: 0.05% per second flying
        drone.battery = max(0, int(drone.battery - 0.05 * dt))

    def _handle_hover(self, drone: DroneState, dt: float) -> None:
        """Count down hover timer, then return home."""
        drone.hover_timer -= dt
        drone.battery = max(0, int(drone.battery - 0.03 * dt))  # Lower drain hovering
        if drone.hover_timer <= 0:
            logger.info(f"🛸 {drone.id} hover complete, returning home")
            self._start_return(drone)

    def _move_to_home(self, drone: DroneState, dt: float) -> None:
        """Move drone toward home base."""
        home_lat = drone.home_base["lat"]
        home_lon = drone.home_base["lon"]
        current_lat = drone.position["lat"]
        current_lon = drone.position["lon"]
        dist = haversine_distance(current_lat, current_lon, home_lat, home_lon)

        if dist < 15:
            # Home
            drone.position["lat"] = home_lat
            drone.position["lon"] = home_lon
            drone.status = DroneStatus.IDLE
            drone.assigned_alert_id = None
            drone.mission_id = None
            drone.target_zone = None
            drone.target_location = None
            drone.current_route = []
            drone.route_index = 0
            drone.can_be_reassigned = True
            drone.rtl_distance_m = 0
            drone.rtl_time_seconds = 0
            logger.info(f"🏠 {drone.id} returned home")
            return

        move_distance = drone.speed_ms * dt
        fraction = min(1.0, move_distance / max(dist, 0.01))
        new_lat, new_lon = interpolate_position(current_lat, current_lon, home_lat, home_lon, fraction)
        drone.position["lat"] = round(new_lat, 6)
        drone.position["lon"] = round(new_lon, 6)
        drone.rtl_distance_m = round(max(0, dist - move_distance), 1)
        drone.rtl_time_seconds = round(drone.rtl_distance_m / max(drone.speed_ms, 0.01), 1)
        drone.battery = max(0, int(drone.battery - 0.05 * dt))

    def _charge_battery(self, drone: DroneState, dt: float) -> None:
        """Charge battery when idle (~5% per second → 0-100% in ~20s)."""
        if drone.battery < 100:
            drone.battery = min(100, int(drone.battery + 5 * dt))

    def _start_return(self, drone: DroneState) -> None:
        """Transition drone to RETURNING status."""
        drone.status = DroneStatus.RETURNING
        drone.can_be_reassigned = False
        drone.current_route = []
        drone.route_index = 0
        home_lat = drone.home_base["lat"]
        home_lon = drone.home_base["lon"]
        dist = haversine_distance(drone.position["lat"], drone.position["lon"], home_lat, home_lon)
        drone.rtl_distance_m = round(dist, 1)
        drone.rtl_time_seconds = round(dist / max(drone.speed_ms, 0.01), 1)

    def dispatch_drone(self, drone_id: str, alert_id: str, zone_id: str,
                       target_lat: float, target_lon: float, route_waypoints: list[dict]) -> bool:
        """Dispatch a drone to a target location with a pre-computed route."""
        drone = self.drones.get(drone_id)
        if not drone:
            return False

        # Only dispatch if drone is IDLE (or can be reassigned while EN_ROUTE)
        if drone.status not in (DroneStatus.IDLE, DroneStatus.EN_ROUTE, DroneStatus.REROUTING):
            logger.warning(f"Cannot dispatch {drone_id}: status is {drone.status.value}")
            return False

        waypoints = [Waypoint(lat=wp["lat"], lon=wp["lon"]) for wp in route_waypoints]
        drone.status = DroneStatus.EN_ROUTE
        drone.assigned_alert_id = alert_id
        drone.target_zone = zone_id
        drone.target_location = {"lat": target_lat, "lon": target_lon}
        drone.current_route = waypoints
        drone.route_index = 0
        drone.can_be_reassigned = True

        # Calculate initial ETA
        total_dist = 0.0
        lat, lon = drone.position["lat"], drone.position["lon"]
        for wp in waypoints:
            total_dist += haversine_distance(lat, lon, wp.lat, wp.lon)
            lat, lon = wp.lat, wp.lon
        drone.distance_remaining_m = round(total_dist, 1)
        drone.eta_seconds = round(total_dist / max(drone.speed_ms, 0.01), 1)
        logger.info(f"🚀 {drone_id} dispatched to {zone_id} (ETA: {drone.eta_seconds:.0f}s, dist: {total_dist:.0f}m)")
        return True

    def reroute_drone(self, drone_id: str, new_target_lat: float, new_target_lon: float,
                      route_waypoints: list[dict], alert_id: str = None) -> bool:
        """Reroute an en-route drone to a new target with a freshly computed route."""
        drone = self.drones.get(drone_id)
        if not drone:
            return False

        # Allow rerouting from EN_ROUTE, REROUTING, or even HOVERING (cancel hover)
        if drone.status not in (DroneStatus.EN_ROUTE, DroneStatus.REROUTING, DroneStatus.HOVERING):
            logger.warning(f"Cannot reroute {drone_id}: status is {drone.status.value}")
            return False

        waypoints = [Waypoint(lat=wp["lat"], lon=wp["lon"]) for wp in route_waypoints]
        drone.status = DroneStatus.REROUTING  # Will transition to EN_ROUTE after first waypoint
        drone.current_route = waypoints
        drone.route_index = 0
        drone.target_location = {"lat": new_target_lat, "lon": new_target_lon}
        if alert_id:
            drone.assigned_alert_id = alert_id
        drone.hover_timer = 0  # Cancel any active hover

        total_dist = 0.0
        lat, lon = drone.position["lat"], drone.position["lon"]
        for wp in waypoints:
            total_dist += haversine_distance(lat, lon, wp.lat, wp.lon)
            lat, lon = wp.lat, wp.lon
        drone.distance_remaining_m = round(total_dist, 1)
        drone.eta_seconds = round(total_dist / max(drone.speed_ms, 0.01), 1)
        logger.info(f"🔄 {drone_id} rerouted → alert={alert_id} (new ETA: {drone.eta_seconds:.0f}s, dist: {total_dist:.0f}m)")
        return True

    def rtl(self, drone_id: str) -> bool:
        """Return to launch."""
        drone = self.drones.get(drone_id)
        if not drone:
            return False
        if drone.status == DroneStatus.IDLE:
            return True
        self._start_return(drone)
        return True

    def score_drone(self, drone_id: str, alert_lat: float, alert_lon: float) -> float:
        """Score a drone for assignment: lower is better.
        Factors: distance/ETA (70%) + battery depletion (30%)
        """
        drone = self.drones.get(drone_id)
        if not drone:
            return float('inf')
        dist = haversine_distance(drone.position["lat"], drone.position["lon"], alert_lat, alert_lon)
        eta = dist / max(drone.speed_ms, 0.01)
        battery_penalty = 1 - drone.battery / 100
        return eta * 0.7 + battery_penalty * 0.3

    def select_drone_pair(self, alert_lat: float, alert_lon: float) -> tuple[Optional[str], Optional[str]]:
        """Select best 2 drones for dispatch.

        Priority: IDLE drones first (cheapest to assign), then EN_ROUTE drones
        that can be reassigned. This ensures all 4 drones are considered.
        """
        idle_candidates = []
        enroute_candidates = []

        for did, drone in self.drones.items():
            if drone.status == DroneStatus.IDLE and drone.battery > self.min_battery:
                idle_candidates.append((did, self.score_drone(did, alert_lat, alert_lon)))
            elif (drone.status in (DroneStatus.EN_ROUTE, DroneStatus.REROUTING) and
                    drone.can_be_reassigned and drone.battery > 30):
                enroute_candidates.append((did, self.score_drone(did, alert_lat, alert_lon)))

        # Sort each group by score
        idle_candidates.sort(key=lambda x: x[1])
        enroute_candidates.sort(key=lambda x: x[1])

        # Prefer idle drones, then fill with en-route
        all_candidates = idle_candidates + enroute_candidates

        primary = all_candidates[0][0] if len(all_candidates) >= 1 else None
        secondary = all_candidates[1][0] if len(all_candidates) >= 2 else None
        return primary, secondary

    def get_available_count(self) -> int:
        """Count drones that are IDLE or available for reassignment."""
        count = 0
        for drone in self.drones.values():
            if drone.status == DroneStatus.IDLE:
                count += 1
            elif drone.status in (DroneStatus.EN_ROUTE, DroneStatus.REROUTING) and drone.can_be_reassigned:
                count += 1
        return count

    def get_all(self) -> list[DroneState]:
        return list(self.drones.values())

    def get_all_api(self) -> list[dict]:
        return [d.to_api_dict() for d in self.drones.values()]

    def get_drone(self, drone_id: str) -> Optional[DroneState]:
        return self.drones.get(drone_id)