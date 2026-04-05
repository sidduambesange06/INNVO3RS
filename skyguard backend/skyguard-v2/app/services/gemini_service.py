"""SkyGuard V2 — Gemini AI Service (Placeholder).

Note: Gemini integration is optional. System works without it.
"""

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def predict_risk_zones(zone_stats: list, hour: int) -> list:
    """Predict risk zones for next 2 hours (placeholder)."""
    # Placeholder implementation - returns empty predictions
    # In production, this would call Gemini API
    logger.debug(f"Risk prediction requested for hour {hour}")
    return []


async def triage_alert(alert: dict, zone_history: list) -> dict:
    """Triage alert using Gemini (placeholder)."""
    # Placeholder - always returns DISPATCH for severity > 0.7
    severity = alert.get("severity", 0)
    if severity > 0.7:
        return {
            "action": "DISPATCH",
            "confidence": 0.9,
            "reasoning": "High severity alert",
        }
    return {
        "action": "MONITOR",
        "confidence": 0.7,
        "reasoning": "Moderate severity",
    }
