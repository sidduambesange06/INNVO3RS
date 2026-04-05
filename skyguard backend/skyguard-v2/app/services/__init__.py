"""SkyGuard V2 — Services Module."""

def _state_snapshot() -> dict:
    """Generate state snapshot for reconnecting clients."""
    from app.services import background_tasks
    
    snapshot = {}
    
    # Drones
    if background_tasks.drone_sim:
        snapshot["drones"] = background_tasks.drone_sim.get_all_api()
    
    # Baseline stats
    if background_tasks.baseline_engine and background_tasks.baseline_engine.is_loaded:
        snapshot["baseline_stats"] = background_tasks.baseline_engine.get_all_zone_stats()
    
    # Camera statuses
    if background_tasks.camera_manager:
        snapshot["cameras"] = background_tasks.camera_manager.get_all_statuses()
    
    # Recent alerts
    if background_tasks.alert_manager:
        snapshot["recent_alerts"] = list(background_tasks.alert_manager._alerts.values())[-5:]
        snapshot["recent_alerts"] = [a.to_ws_dict() for a in snapshot["recent_alerts"]]
    
    return snapshot
