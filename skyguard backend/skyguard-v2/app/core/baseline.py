"""SkyGuard V2 — Baseline Engine.

Poisson-based anomaly scoring with severity weights per anomaly type.
"""

import math
from datetime import datetime
from typing import Optional
from collections import defaultdict

from scipy.stats import poisson

from app.db import crud
from app.models.baseline import BaselineResult
from app.models.enums import AnomalyType
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

SEVERITY_WEIGHTS = {
    AnomalyType.CROWD_ANOMALY.value: 1.0,
    AnomalyType.FIGHT_DETECTION.value: 1.4,
    AnomalyType.PERSON_DOWN.value: 1.5,
    AnomalyType.WEAPON_DETECT.value: 2.0,
    AnomalyType.SUSPICIOUS_BEHAVIOR.value: 1.2,
}


class BaselineEngine:
    """Poisson baseline anomaly detection engine with DB-backed baselines."""

    def __init__(self):
        self._cache: dict[str, dict[int, dict]] = defaultdict(dict)  # zone -> hour -> {mean, std}
        self._latest: dict[str, BaselineResult] = {}
        self._sample_counts: dict[str, dict[int, tuple]] = defaultdict(lambda: defaultdict(lambda: (0, 0.0, 0.0)))
        self._loaded = False

    async def load_from_db(self) -> None:
        """Load all baselines from database into memory cache."""
        rows = await crud.fetch_all("SELECT * FROM zone_baselines")
        for row in rows:
            zone_id = row["zone_id"]
            hour = row["hour"]
            self._cache[zone_id][hour] = {
                "mean": row["mean"],
                "std": row["std_dev"],
            }
        self._loaded = True
        total = sum(len(h) for h in self._cache.values())
        logger.info(f"✅ Baseline engine loaded: {len(self._cache)} zones, {total} records")

    def calculate(self, zone_id: str, current_count: int,
                  anomaly_type: str = "crowd_anomaly") -> BaselineResult:
        """Calculate anomaly severity using Poisson distribution."""
        hour = datetime.now().hour
        baseline = self._cache.get(zone_id, {}).get(hour, {"mean": 5.0, "std": 2.0})
        mean = baseline["mean"]
        std = baseline.get("std", math.sqrt(mean))

        lambda_val = max(mean, 0.01)

        # Z-score
        try:
            z_score = (current_count - lambda_val) / max(math.sqrt(lambda_val), 0.01)
        except (ZeroDivisionError, ValueError):
            z_score = 0.0

        # Poisson CDF anomaly score
        try:
            anomaly_score = float(1.0 - poisson.cdf(current_count, mu=max(lambda_val, 0.01)))
            anomaly_score = max(0.0, min(1.0, anomaly_score))
        except Exception:
            anomaly_score = 0.0

        # Severity: only when above baseline
        severity = anomaly_score if current_count > lambda_val else 0.0

        # Apply anomaly type weight
        weight = SEVERITY_WEIGHTS.get(anomaly_type, 1.0)
        final_severity = min(1.0, round(severity * weight, 2))

        # Handle NaN/Inf
        if math.isnan(z_score) or math.isinf(z_score):
            z_score = 0.0
        if math.isnan(final_severity):
            final_severity = 0.0

        result = BaselineResult(
            zone_id=zone_id,
            current_count=current_count,
            baseline_mean=round(lambda_val, 2),
            baseline_std=round(std, 2),
            z_score=round(z_score, 2),
            anomaly_score=round(anomaly_score, 2),
            severity=round(severity, 2),
            final_severity=final_severity,
        )

        self._latest[zone_id] = result
        return result

    async def update_baseline(self, zone_id: str, hour: int, new_count: int) -> None:
        """Welford online update — update DB every 100 samples."""
        key = (zone_id, hour)
        n, mean, M2 = self._sample_counts[zone_id][hour]
        n += 1
        delta = new_count - mean
        mean += delta / n
        delta2 = new_count - mean
        M2 += delta * delta2
        self._sample_counts[zone_id][hour] = (n, mean, M2)

        if n % 100 == 0:
            std = math.sqrt(M2 / n) if n > 1 else 1.0
            dow = datetime.now().weekday()
            await crud.upsert_baseline(zone_id, hour, dow, round(mean, 2), round(std, 2), n)
            self._cache[zone_id][hour] = {"mean": mean, "std": std}

    def get_all_zone_stats(self) -> list[dict]:
        """Get latest baseline results for all zones."""
        results = []
        for zone_id in self._cache:
            if zone_id in self._latest:
                results.append(self._latest[zone_id].to_ws_dict())
            else:
                hour = datetime.now().hour
                b = self._cache[zone_id].get(hour, {"mean": 5.0, "std": 2.0})
                results.append({
                    "zone_id": zone_id,
                    "current": 0,
                    "mean": round(b["mean"], 2),
                    "std_dev": round(b.get("std", 2.0), 2),
                    "z_score": 0.0,
                    "anomaly_score": 0.0,
                    "severity": 0.0,
                })
        return results

    def get_zone_ids(self) -> list[str]:
        return list(self._cache.keys())

    @property
    def is_loaded(self) -> bool:
        return self._loaded
