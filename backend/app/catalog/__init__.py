"""Catalog package — pre-set enums and specs for the POC.

Every "state" or "parameter" the platform recognizes lives here so the API,
schemas, prompts, simulator, and rule engine share a single source of truth.
"""

from app.catalog.audiences import (
    AUDIENCE_DESCRIPTIONS,
    AUDIENCES,
    Audience,
    is_valid_audience,
)
from app.catalog.experiment_options import (
    CONFIDENCE_LEVELS,
    DEFAULT_SAMPLE_SIZES,
    DURATION_OPTIONS_DAYS,
    TRAFFIC_SPLIT_LABELS,
    TRAFFIC_SPLITS,
    TrafficSplitOption,
    get_split,
    is_valid_confidence,
    is_valid_duration,
    is_valid_split,
)
from app.catalog.features import (
    FEATURE_DESCRIPTIONS,
    FEATURES,
    Feature,
    is_valid_feature,
)
from app.catalog.metrics import (
    GUARDRAIL_METRICS,
    METRIC_IDS,
    METRICS,
    PRIMARY_METRICS,
    SECONDARY_METRICS,
    Direction,
    MetricKind,
    MetricRole,
    MetricSpec,
    get_metric,
    is_valid_guardrail,
    is_valid_metric,
    is_valid_primary,
    is_valid_secondary,
)
from app.catalog.status import STATUSES, ExperimentStatus

__all__ = [
    # audiences
    "AUDIENCES",
    "AUDIENCE_DESCRIPTIONS",
    "Audience",
    "is_valid_audience",
    # experiment options
    "CONFIDENCE_LEVELS",
    "DEFAULT_SAMPLE_SIZES",
    "DURATION_OPTIONS_DAYS",
    "TRAFFIC_SPLITS",
    "TRAFFIC_SPLIT_LABELS",
    "TrafficSplitOption",
    "get_split",
    "is_valid_confidence",
    "is_valid_duration",
    "is_valid_split",
    # features
    "FEATURES",
    "FEATURE_DESCRIPTIONS",
    "Feature",
    "is_valid_feature",
    # metrics
    "GUARDRAIL_METRICS",
    "METRIC_IDS",
    "METRICS",
    "PRIMARY_METRICS",
    "SECONDARY_METRICS",
    "Direction",
    "MetricKind",
    "MetricRole",
    "MetricSpec",
    "get_metric",
    "is_valid_guardrail",
    "is_valid_metric",
    "is_valid_primary",
    "is_valid_secondary",
    # status
    "STATUSES",
    "ExperimentStatus",
]


def catalog_summary() -> dict:
    """Compact summary of all catalogs, useful for LLM prompts and /catalog API."""
    return {
        "features": [
            {"id": f.value, "description": FEATURE_DESCRIPTIONS[f]} for f in FEATURES
        ],
        "audiences": [
            {"id": a.value, "description": AUDIENCE_DESCRIPTIONS[a]}
            for a in AUDIENCES
        ],
        "metrics": [
            {
                "id": m.id,
                "label": m.label,
                "kind": m.kind.value,
                "direction": m.direction.value,
                "eligible_roles": [r.value for r in m.eligible_roles],
                "baseline": m.baseline,
                "unit": m.unit,
                "description": m.description,
            }
            for m in METRICS.values()
        ],
        "traffic_splits": [
            {
                "option": o.value,
                "label": TRAFFIC_SPLIT_LABELS[o],
                "control": TRAFFIC_SPLITS[o][0],
                "variant": TRAFFIC_SPLITS[o][1],
            }
            for o in TrafficSplitOption
        ],
        "duration_options_days": list(DURATION_OPTIONS_DAYS),
        "confidence_levels": list(CONFIDENCE_LEVELS),
        "default_sample_sizes": list(DEFAULT_SAMPLE_SIZES),
        "statuses": [s.value for s in STATUSES],
    }