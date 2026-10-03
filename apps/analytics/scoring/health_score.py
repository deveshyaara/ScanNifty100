"""Transparent historical screening score, not a predictive investment model."""
import json
from pathlib import Path
from apps.analytics.features.common import number


def load_config():
    import os
    path = Path(os.environ.get("SCORING_CONFIG", Path(__file__).with_name("config.json")))
    config = json.loads(path.read_text(encoding="utf-8"))
    if set(config["weights"]) != set(config["metrics"]):
        raise ValueError("Scoring weights must match components")
    if any(v <= 0 for v in config["weights"].values()):
        raise ValueError("Scoring weights must be positive")
    return config


def explain_score(metrics, sector=None, identity_status=None, config=None):
    config = config or load_config()
    excluded = set(config.get("sector_exclusions", {}).get(sector, []))
    components, contributions = {}, {}
    eligible_weight = available_weight = weighted_score = 0.0
    for component, rules in config["metrics"].items():
        active = {k: v for k, v in rules.items() if k not in excluded}
        if not active:
            components[component] = None
            continue
        weight = config["weights"][component]
        eligible_weight += weight
        scores = []
        for metric, (low, high) in active.items():
            if high == low:
                raise ValueError(f"Equal scoring endpoints: {metric}")
            value = number(metrics.get(metric))
            score = None if value is None else max(0, min(100, (value - low) / (high - low) * 100))
            contributions[metric] = {"value": value, "score": score, "component": component, "weight": weight / len(active), "status": "available" if value is not None else "unavailable_or_insufficient_history"}
            if score is not None:
                scores.append(score)
                available_weight += weight / len(active)
                weighted_score += score * weight / len(active)
        components[component] = sum(scores) / len(scores) if scores else None
    coverage = available_weight / eligible_weight if eligible_weight else 0
    blocked = identity_status == "conflicting_profile"
    overall = weighted_score / available_weight if available_weight and coverage >= config["minimum_coverage"] and not blocked else None
    return {"overall_score": round(overall, 2) if overall is not None else None, "coverage_pct": round(coverage * 100, 2), "components": components, "contributions": contributions, "excluded_metrics": sorted(excluded), "status": "identity_conflict" if blocked else "scored" if overall is not None else "insufficient_coverage", "model_version": config["version"], "health_label": map_score_to_label(overall)}


def calculate_health_score(metrics):
    """
    Calculate overall company health score (0-100)
    
    Args:
        metrics: Dictionary of financial metrics
    
    Returns:
        Health score (0-100)
    """
    return explain_score(metrics)["overall_score"]


def map_score_to_label(score):
    """Map numerical score to health label"""
    if score is None:
        return None
    for threshold, label in [(80, "EXCELLENT"), (60, "GOOD"), (40, "AVERAGE"), (20, "WEAK"), (0, "POOR")]:
        if score >= threshold:
            return label
    raise ValueError("Score must be nonnegative")
