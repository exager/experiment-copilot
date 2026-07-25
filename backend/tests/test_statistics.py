"""Tests for the statistics engine.

All *positive* scenarios are tuned so the variant wins — this mirrors the
demo flow where the checkout_v2 variant beats control. Edge-case tests
(zero users, tied rates) verify the engine correctly says "inconclusive".
"""

from __future__ import annotations

import math

import pytest

from app.statistics import (
    compute_statistics,
    compute_statistics_from_row,
    conversion_lift,
    conversion_rate,
    determine_winner,
    two_proportion_z_test,
)


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------


class TestConversionRate:
    def test_basic(self):
        assert conversion_rate(50, 1000) == 0.05

    def test_zero_users_returns_none(self):
        assert conversion_rate(0, 0) is None

    def test_negative_users_returns_none(self):
        assert conversion_rate(10, -1) is None


class TestConversionLift:
    def test_variant_wins(self):
        # control 5%, variant 6% → +20% lift
        assert conversion_lift(0.05, 0.06) == pytest.approx(0.20)

    def test_variant_matches_control(self):
        assert conversion_lift(0.05, 0.05) == 0.0

    def test_none_when_control_zero(self):
        assert conversion_lift(0.0, 0.05) is None

    def test_none_when_input_none(self):
        assert conversion_lift(None, 0.05) is None
        assert conversion_lift(0.05, None) is None


class TestTwoProportionZTest:
    def test_variant_significantly_higher(self):
        # Control: 50/1000 = 5%, Variant: 80/1000 = 8%
        # Big enough sample + big enough gap → p < 0.05, z > 0
        z, p = two_proportion_z_test(50, 1000, 80, 1000)
        assert z is not None and p is not None
        assert z > 0                # variant > control
        assert p < 0.01             # strong significance

    def test_variant_matches_control(self):
        z, p = two_proportion_z_test(50, 1000, 50, 1000)
        assert z == 0.0
        assert p == pytest.approx(1.0)

    def test_empty_control_arm(self):
        z, p = two_proportion_z_test(0, 0, 80, 1000)
        assert z is None and p is None

    def test_empty_variant_arm(self):
        z, p = two_proportion_z_test(50, 1000, 0, 0)
        assert z is None and p is None

    def test_all_users_convert_both_arms(self):
        # Degenerate pooled proportion → engine returns None
        z, p = two_proportion_z_test(1000, 1000, 1000, 1000)
        assert z is None and p is None


# ---------------------------------------------------------------------------
# Winner determination
# ---------------------------------------------------------------------------


class TestDetermineWinner:
    def test_variant_wins_when_positive_z_and_confident(self):
        assert determine_winner(z_score=3.0, p_value=0.001, lift=0.14) == "variant"

    def test_control_wins_when_negative_z_and_confident(self):
        assert determine_winner(z_score=-3.0, p_value=0.001, lift=-0.10) == "control"

    def test_inconclusive_when_confidence_below_threshold(self):
        assert (
            determine_winner(z_score=1.2, p_value=0.20, lift=0.05) == "inconclusive"
        )

    def test_inconclusive_when_test_stats_missing(self):
        assert determine_winner(None, None, None) == "inconclusive"

    def test_min_lift_threshold_makes_small_lift_inconclusive(self):
        # High confidence but lift below threshold → inconclusive
        assert (
            determine_winner(
                z_score=3.0, p_value=0.001, lift=0.02, min_lift_threshold=0.05
            )
            == "inconclusive"
        )


# ---------------------------------------------------------------------------
# End-to-end compute_statistics — every scenario is a variant win
# ---------------------------------------------------------------------------


class TestComputeStatistics:
    """All positive scenarios below are engineered so variant wins."""

    def test_checkout_v2_demo_scenario(self):
        """The canonical checkout example: 4.1% → 4.7% at 12000 users each."""
        stats = compute_statistics(
            users_control=12000,
            users_variant=12000,
            conversion_control=492,   # 4.1%
            conversion_variant=564,   # 4.7%
        )
        assert stats.winner == "variant"
        assert stats.is_significant is True
        assert stats.confidence is not None and stats.confidence >= 0.95
        assert stats.conversion_lift is not None
        assert stats.conversion_lift > 0.10   # ~14% relative lift
        assert stats.variant_conversion_rate > stats.control_conversion_rate

    def test_small_but_significant_variant_win(self):
        """Even at more modest lift, variant still wins with enough samples."""
        stats = compute_statistics(
            users_control=25000,
            users_variant=25000,
            conversion_control=1000,   # 4.0%
            conversion_variant=1150,   # 4.6%
        )
        assert stats.winner == "variant"
        assert stats.is_significant is True
        assert stats.conversion_lift > 0.10

    def test_massive_variant_win(self):
        """Big lift, huge sample — should be a landslide variant win."""
        stats = compute_statistics(
            users_control=10000,
            users_variant=10000,
            conversion_control=500,    # 5%
            conversion_variant=800,    # 8%
        )
        assert stats.winner == "variant"
        assert stats.is_significant is True
        assert stats.confidence is not None and stats.confidence > 0.9999
        assert stats.conversion_lift > 0.55

    def test_early_ramp_still_inconclusive(self):
        """First few ticks of the simulation: variant is ahead, but not enough
        data yet. Engine should correctly say `inconclusive`."""
        stats = compute_statistics(
            users_control=200,
            users_variant=200,
            conversion_control=9,      # 4.5%
            conversion_variant=11,     # 5.5%
        )
        # Variant is trending higher but sample size is too small
        assert stats.variant_conversion_rate > stats.control_conversion_rate
        assert stats.winner == "inconclusive"
        assert stats.is_significant is False

    def test_tied_rates_inconclusive(self):
        stats = compute_statistics(
            users_control=5000,
            users_variant=5000,
            conversion_control=200,
            conversion_variant=200,
        )
        assert stats.winner == "inconclusive"
        assert stats.is_significant is False
        assert stats.conversion_lift == 0.0

    def test_empty_arms_returns_inconclusive(self):
        stats = compute_statistics(
            users_control=0,
            users_variant=0,
            conversion_control=0,
            conversion_variant=0,
        )
        assert stats.winner == "inconclusive"
        assert stats.is_significant is False
        assert stats.p_value is None
        assert stats.confidence is None

    def test_confidence_equals_one_minus_p(self):
        stats = compute_statistics(10000, 10000, 500, 700)
        assert stats.p_value is not None and stats.confidence is not None
        assert stats.confidence == pytest.approx(1.0 - stats.p_value)


class TestComputeStatisticsFromRow:
    def test_accepts_dict(self):
        row = {
            "users_control": 10000,
            "users_variant": 10000,
            "conversion_control": 500,
            "conversion_variant": 700,
        }
        stats = compute_statistics_from_row(row)
        assert stats.winner == "variant"
        assert stats.is_significant is True

    def test_accepts_object_with_attrs(self):
        class FakeRow:
            users_control = 10000
            users_variant = 10000
            conversion_control = 500
            conversion_variant = 700

        stats = compute_statistics_from_row(FakeRow())
        assert stats.winner == "variant"


# ---------------------------------------------------------------------------
# Sanity: match against a known scipy result
# ---------------------------------------------------------------------------


def test_z_score_matches_manual_calculation():
    """Manually compute z for (50/1000) vs (80/1000) and verify."""
    z, p = two_proportion_z_test(50, 1000, 80, 1000)
    # Pooled p = 130/2000 = 0.065
    # variance = 0.065 * 0.935 * (1/1000 + 1/1000) = 0.0001216
    # se = sqrt(variance) ≈ 0.011026
    # z = (0.08 - 0.05) / 0.011026 ≈ 2.720
    assert z == pytest.approx(2.720, rel=1e-2)
    assert p == pytest.approx(0.0065, rel=1e-1)
    assert math.isfinite(z) and math.isfinite(p)