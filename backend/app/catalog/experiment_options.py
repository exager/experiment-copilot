"""Fixed configuration options an experiment can use.

Traffic splits, durations, confidence levels, and sample sizes are drawn
from these enums/tuples so the Design Agent's output is bounded and the
frontend can render dropdowns.
"""

from __future__ import annotations

from enum import StrEnum


class TrafficSplitOption(StrEnum):
    """Allowed traffic-split presets (control / variant)."""

    SPLIT_50_50 = "50_50"
    SPLIT_60_40 = "60_40"
    SPLIT_70_30 = "70_30"
    SPLIT_90_10 = "90_10"   # canary
    SPLIT_95_5 = "95_5"     # small canary


TRAFFIC_SPLITS: dict[TrafficSplitOption, tuple[float, float]] = {
    TrafficSplitOption.SPLIT_50_50: (0.50, 0.50),
    TrafficSplitOption.SPLIT_60_40: (0.60, 0.40),
    TrafficSplitOption.SPLIT_70_30: (0.70, 0.30),
    TrafficSplitOption.SPLIT_90_10: (0.90, 0.10),
    TrafficSplitOption.SPLIT_95_5: (0.95, 0.05),
}


TRAFFIC_SPLIT_LABELS: dict[TrafficSplitOption, str] = {
    TrafficSplitOption.SPLIT_50_50: "50 / 50 (standard)",
    TrafficSplitOption.SPLIT_60_40: "60 / 40",
    TrafficSplitOption.SPLIT_70_30: "70 / 30",
    TrafficSplitOption.SPLIT_90_10: "90 / 10 (canary)",
    TrafficSplitOption.SPLIT_95_5: "95 / 5 (small canary)",
}


DURATION_OPTIONS_DAYS: tuple[int, ...] = (7, 14, 21, 28)

CONFIDENCE_LEVELS: tuple[float, ...] = (0.90, 0.95, 0.99)

DEFAULT_SAMPLE_SIZES: tuple[int, ...] = (2_000, 5_000, 10_000, 25_000)


def get_split(option: TrafficSplitOption) -> tuple[float, float]:
    """Return the (control, variant) fractions for a split option."""
    return TRAFFIC_SPLITS[option]


def is_valid_split(option: str) -> bool:
    return option in TrafficSplitOption._value2member_map_


def is_valid_duration(days: int) -> bool:
    return days in DURATION_OPTIONS_DAYS


def is_valid_confidence(level: float) -> bool:
    return level in CONFIDENCE_LEVELS