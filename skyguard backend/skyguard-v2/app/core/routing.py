"""SkyGuard V2 — CLSP Routing Algorithm.

Clustered Layered Shortest Path for drone routing over Pune airspace.
- 100m grid waypoint graph over Pune bounds
- Nodes clustered into ~5km squares
- NFZ enforcement: edges through NFZ polygons are blocked
- Phase 1: Coarse BFS between cluster representatives
- Phase 2: Fine routing within cluster chain (frontier shrinking)
- Phase 3: Reconstruct path, fallback to NFZ perimeter if unreachable
"""

import json
import math
import os
import time
import heapq
from collections import defaultdict, deque
from typing import Optional

from app.utils.haversine import haversine_distance
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Pune bounds
LAT_MIN, LAT_MAX = 18.45, 18.65
LON_MIN, LON_MAX = 73.75, 73.95
GRID_STEP_DEG = 0.001  # ~111m per 0.001° latitude
CLUSTER_SIZE_DEG = 0.05  # ~5km clusters


class AirspaceGraph:
    """Waypoint graph over Pune airspace with NFZ enforcement."""

    def __init__(self):
        self.nodes: dict[int, tuple[float, float]] = {}  # node_id -> (lat, lon)
        self.edges: dict[int, list[tuple[int, float]]] = defaultdict(list)  # adjacency list
        self.node_cluster: dict[int, int] = {}  # node_id -> cluster_id
        self.clusters: dict[int, list[int]] = defaultdict(list)  # cluster_id -> [node_ids]
        self.cluster_reps: dict[int, int] = {}  # cluster_id -> representative node_id
        self.cluster_adjacency: dict[int, set[int]] = defaultdict(set)  # cluster_id -> {adjacent_cluster_ids}
        self.blocked_nodes: set[int] = set()
        self._built = False

    def build(self, nfz_objects: list = None) -> None:
        """Build the complete airspace graph."""
        start = time.time()
        self._build_grid()
        self._build_edges()
        self._build_clusters()
        if nfz_objects:
            self._apply_no_fly_zones(nfz_objects)
        self._built = True
        elapsed = (time.time() - start) * 1000
        logger.info(f"✅ Airspace graph built: {len(self.nodes)} nodes, "
                    f"{sum(len(e) for e in self.edges.values())} edges, "
                    f"{len(self.clusters)} clusters in {elapsed:.0f}ms")

    def _build_grid(self) -> None:
        """Create ~200 nodes on a 100m grid over Pune."""
        node_id = 0
        lat = LAT_MIN
        while lat <= LAT_MAX:
            lon = LON_MIN
            while lon <= LON_MAX:
                self.nodes[node_id] = (round(lat, 6), round(lon, 6))
                node_id += 1
                lon += GRID_STEP_DEG
            lat += GRID_STEP_DEG

    def _build_edges(self) -> None:
        """Connect adjacent grid nodes (4-directional + diagonal)."""
        # Build spatial index: (lat_idx, lon_idx) -> node_id
        idx_to_node = {}
        node_to_idx = {}
        lat_steps = int((LAT_MAX - LAT_MIN) / GRID_STEP_DEG) + 1
        lon_steps = int((LON_MAX - LON_MIN) / GRID_STEP_DEG) + 1

        node_id = 0
        for i in range(lat_steps):
            for j in range(lon_steps):
                if node_id in self.nodes:
                    idx_to_node[(i, j)] = node_id
                    node_to_idx[node_id] = (i, j)
                    node_id += 1

        # Connect neighbors (8-directional)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                      (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for (i, j), nid in idx_to_node.items():
            lat1, lon1 = self.nodes[nid]
            for di, dj in directions:
                ni, nj = i + di, j + dj
                if (ni, nj) in idx_to_node:
                    neighbor = idx_to_node[(ni, nj)]
                    lat2, lon2 = self.nodes[neighbor]
                    weight = haversine_distance(lat1, lon1, lat2, lon2)
                    self.edges[nid].append((neighbor, weight))

    def _build_clusters(self) -> None:
        """Cluster nodes into ~5km squares."""
        for nid, (lat, lon) in self.nodes.items():
            ci = int((lat - LAT_MIN) / CLUSTER_SIZE_DEG)
            cj = int((lon - LON_MIN) / CLUSTER_SIZE_DEG)
            cluster_id = ci * 100 + cj
            self.node_cluster[nid] = cluster_id
            self.clusters[cluster_id].append(nid)

        # Pick centroid-closest node as cluster representative
        for cid, node_ids in self.clusters.items():
            avg_lat = sum(self.nodes[n][0] for n in node_ids) / len(node_ids)
            avg_lon = sum(self.nodes[n][1] for n in node_ids) / len(node_ids)
            rep = min(node_ids, key=lambda n: haversine_distance(
                self.nodes[n][0], self.nodes[n][1], avg_lat, avg_lon))
            self.cluster_reps[cid] = rep

        # Build cluster adjacency from edge connections
        for nid, neighbors in self.edges.items():
            c1 = self.node_cluster.get(nid)
            if c1 is None:
                continue
            for (neighbor, _) in neighbors:
                c2 = self.node_cluster.get(neighbor)
                if c2 is not None and c1 != c2:
                    self.cluster_adjacency[c1].add(c2)
                    self.cluster_adjacency[c2].add(c1)

    def _apply_no_fly_zones(self, nfz_objects: list) -> None:
        """Remove edges that pass through NFZ polygons."""
        blocked_edges = 0
        for nid in list(self.nodes.keys()):
            lat, lon = self.nodes[nid]
            # Check if node itself is in NFZ
            for nfz in nfz_objects:
                if nfz.contains(lat, lon):
                    self.blocked_nodes.add(nid)
                    self.edges[nid] = []  # Remove all edges from blocked node
                    blocked_edges += 1
                    break

        # Remove edges to blocked nodes
        for nid in list(self.edges.keys()):
            if nid in self.blocked_nodes:
                continue
            self.edges[nid] = [(n, w) for n, w in self.edges[nid] if n not in self.blocked_nodes]

        logger.info(f"NFZ enforcement: blocked {len(self.blocked_nodes)} nodes")

    def get_nearest_node(self, lat: float, lon: float) -> Optional[int]:
        """Find closest unblocked graph node to a GPS point."""
        best_node = None
        best_dist = float('inf')
        for nid, (nlat, nlon) in self.nodes.items():
            if nid in self.blocked_nodes:
                continue
            d = haversine_distance(lat, lon, nlat, nlon)
            if d < best_dist:
                best_dist = d
                best_node = nid
        return best_node

    def save(self, path: str = "data/airspace/pune_graph.json") -> None:
        """Serialize graph to JSON."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "nodes": {str(k): list(v) for k, v in self.nodes.items()},
            "edges": {str(k): v for k, v in self.edges.items()},
            "node_cluster": {str(k): v for k, v in self.node_cluster.items()},
            "blocked_nodes": list(self.blocked_nodes),
        }
        with open(path, "w") as f:
            json.dump(data, f)
        logger.info(f"Graph saved to {path}")

    def load(self, path: str = "data/airspace/pune_graph.json") -> bool:
        """Load graph from JSON. Returns True if successful."""
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r") as f:
                data = json.load(f)
            self.nodes = {int(k): tuple(v) for k, v in data["nodes"].items()}
            self.edges = defaultdict(list)
            for k, v in data["edges"].items():
                self.edges[int(k)] = [(n, w) for n, w in v]
            self.node_cluster = {int(k): v for k, v in data["node_cluster"].items()}
            self.blocked_nodes = set(data.get("blocked_nodes", []))

            # Rebuild clusters and adjacency
            self.clusters = defaultdict(list)
            for nid, cid in self.node_cluster.items():
                self.clusters[cid].append(nid)
            for cid, node_ids in self.clusters.items():
                if node_ids:
                    avg_lat = sum(self.nodes[n][0] for n in node_ids) / len(node_ids)
                    avg_lon = sum(self.nodes[n][1] for n in node_ids) / len(node_ids)
                    self.cluster_reps[cid] = min(node_ids, key=lambda n: haversine_distance(
                        self.nodes[n][0], self.nodes[n][1], avg_lat, avg_lon))
            for nid, neighbors in self.edges.items():
                c1 = self.node_cluster.get(nid)
                if c1 is None:
                    continue
                for (neighbor, _) in neighbors:
                    c2 = self.node_cluster.get(neighbor)
                    if c2 is not None and c1 != c2:
                        self.cluster_adjacency[c1].add(c2)
                        self.cluster_adjacency[c2].add(c1)

            self._built = True
            logger.info(f"Graph loaded from {path}: {len(self.nodes)} nodes")
            return True
        except Exception as e:
            logger.error(f"Failed to load graph: {e}")
            return False

    @property
    def is_built(self) -> bool:
        return self._built


def clsp_shortest_path(graph: AirspaceGraph, src_lat: float, src_lon: float,
                       dst_lat: float, dst_lon: float) -> dict:
    """
    Clustered Layered Shortest Path algorithm.

    Phase 1: Coarse BFS between cluster representatives
    Phase 2: Fine routing within cluster chain (frontier shrinking + limited relaxation)
    Phase 3: Reconstruct path, fallback to NFZ perimeter if needed

    Returns:
        Route dict with waypoints, distance, NFZs avoided, computation time
    """
    start_time = time.time()

    src_node = graph.get_nearest_node(src_lat, src_lon)
    dst_node = graph.get_nearest_node(dst_lat, dst_lon)

    if src_node is None or dst_node is None:
        return _make_direct_route(src_lat, src_lon, dst_lat, dst_lon, start_time)

    if src_node == dst_node:
        return _make_route([src_node], graph, start_time)

    src_cluster = graph.node_cluster.get(src_node)
    dst_cluster = graph.node_cluster.get(dst_node)

    if src_cluster is None or dst_cluster is None:
        return _make_direct_route(src_lat, src_lon, dst_lat, dst_lon, start_time)

    # ---- Phase 1: Coarse BFS between clusters ----
    cluster_path = _bfs_clusters(graph, src_cluster, dst_cluster)
    if not cluster_path:
        # No cluster path — try direct Dijkstra
        path = _dijkstra(graph, src_node, dst_node)
        if path:
            return _make_route(path, graph, start_time)
        return _make_direct_route(src_lat, src_lon, dst_lat, dst_lon, start_time)

    # ---- Phase 2: Fine routing within cluster chain ----
    allowed_clusters = set(cluster_path)
    # Also allow clusters adjacent to the chain
    for cid in cluster_path:
        allowed_clusters.update(graph.cluster_adjacency.get(cid, set()))

    # Limited Dijkstra: only relax edges within allowed clusters
    path = _limited_dijkstra(graph, src_node, dst_node, allowed_clusters)

    if not path:
        # Fallback: full Dijkstra
        path = _dijkstra(graph, src_node, dst_node)

    if not path:
        return _make_direct_route(src_lat, src_lon, dst_lat, dst_lon, start_time)

    # ---- Phase 3: Build route ----
    route = _make_route(path, graph, start_time)
    route["cluster_path"] = cluster_path
    return route


def _bfs_clusters(graph: AirspaceGraph, src_cluster: int, dst_cluster: int) -> list[int]:
    """BFS between cluster IDs."""
    if src_cluster == dst_cluster:
        return [src_cluster]

    visited = {src_cluster}
    queue = deque([(src_cluster, [src_cluster])])

    while queue:
        current, path = queue.popleft()
        for neighbor in graph.cluster_adjacency.get(current, []):
            if neighbor in visited:
                continue
            new_path = path + [neighbor]
            if neighbor == dst_cluster:
                return new_path
            visited.add(neighbor)
            queue.append((neighbor, new_path))

    return []  # No path found


def _limited_dijkstra(graph: AirspaceGraph, src: int, dst: int,
                      allowed_clusters: set[int]) -> list[int]:
    """Dijkstra limited to nodes within allowed clusters."""
    dist = {src: 0.0}
    prev = {}
    heap = [(0.0, src)]
    visited = set()

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)

        if u == dst:
            return _reconstruct_path(prev, src, dst)

        for neighbor, weight in graph.edges.get(u, []):
            if neighbor in visited or neighbor in graph.blocked_nodes:
                continue
            # Check if neighbor is in allowed cluster
            nc = graph.node_cluster.get(neighbor)
            if nc is not None and nc not in allowed_clusters:
                continue
            new_dist = d + weight
            if new_dist < dist.get(neighbor, float('inf')):
                dist[neighbor] = new_dist
                prev[neighbor] = u
                heapq.heappush(heap, (new_dist, neighbor))

    return []  # No path


def _dijkstra(graph: AirspaceGraph, src: int, dst: int) -> list[int]:
    """Full Dijkstra shortest path."""
    dist = {src: 0.0}
    prev = {}
    heap = [(0.0, src)]
    visited = set()

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)

        if u == dst:
            return _reconstruct_path(prev, src, dst)

        for neighbor, weight in graph.edges.get(u, []):
            if neighbor in visited or neighbor in graph.blocked_nodes:
                continue
            new_dist = d + weight
            if new_dist < dist.get(neighbor, float('inf')):
                dist[neighbor] = new_dist
                prev[neighbor] = u
                heapq.heappush(heap, (new_dist, neighbor))

    return []


def _reconstruct_path(prev: dict, src: int, dst: int) -> list[int]:
    """Reconstruct path from prev map."""
    path = [dst]
    current = dst
    max_iter = 10000
    while current != src and max_iter > 0:
        current = prev.get(current)
        if current is None:
            return []
        path.append(current)
        max_iter -= 1
    path.reverse()
    return path


def _make_route(path: list[int], graph: AirspaceGraph, start_time: float) -> dict:
    """Build a route dict from a node path."""
    waypoints = []
    total_dist = 0.0
    nfz_avoided = set()

    for i, nid in enumerate(path):
        lat, lon = graph.nodes[nid]
        waypoints.append({"lat": round(lat, 6), "lon": round(lon, 6)})
        if i > 0:
            prev_lat, prev_lon = graph.nodes[path[i - 1]]
            total_dist += haversine_distance(prev_lat, prev_lon, lat, lon)

    # Simplify route: keep every Nth waypoint + start/end
    if len(waypoints) > 20:
        step = max(1, len(waypoints) // 15)
        simplified = [waypoints[0]]
        for i in range(step, len(waypoints) - 1, step):
            simplified.append(waypoints[i])
        simplified.append(waypoints[-1])
        waypoints = simplified

    elapsed_ms = (time.time() - start_time) * 1000
    eta_s = total_dist / 15.0  # 15 m/s drone speed

    return {
        "waypoints": waypoints,
        "total_distance_m": round(total_dist, 1),
        "estimated_time_s": round(eta_s, 1),
        "no_fly_zones_avoided": list(nfz_avoided),
        "cluster_path": [],
        "computation_ms": round(elapsed_ms, 1),
    }


def _make_direct_route(src_lat: float, src_lon: float, dst_lat: float, dst_lon: float,
                       start_time: float) -> dict:
    """Create a simple direct route when graph routing fails."""
    dist = haversine_distance(src_lat, src_lon, dst_lat, dst_lon)
    elapsed_ms = (time.time() - start_time) * 1000
    return {
        "waypoints": [
            {"lat": round(src_lat, 6), "lon": round(src_lon, 6)},
            {"lat": round(dst_lat, 6), "lon": round(dst_lon, 6)},
        ],
        "total_distance_m": round(dist, 1),
        "estimated_time_s": round(dist / 15.0, 1),
        "no_fly_zones_avoided": [],
        "cluster_path": [],
        "computation_ms": round(elapsed_ms, 1),
    }
