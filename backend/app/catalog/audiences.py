"""Audience catalog.

The pre-set list of user segments a PM can target. Every experiment
configuration must pick exactly one audience from this enum.
"""

from __future__ import annotations

from enum import StrEnum


class Audience(StrEnum):
    """User segments available for experiment targeting."""

    ALL_USERS = "all_users"
    NEW_USERS = "new_users"
    RETURNING_USERS = "returning_users"
    MOBILE_USERS = "mobile_users"
    DESKTOP_USERS = "desktop_users"
    ANDROID_USERS = "android_users"
    IOS_USERS = "ios_users"
    RETURNING_ANDROID_USERS = "returning_android_users"
    HIGH_VALUE_CUSTOMERS = "high_value_customers"
    US_USERS = "us_users"
    EU_USERS = "eu_users"


AUDIENCES: tuple[Audience, ...] = tuple(Audience)


AUDIENCE_DESCRIPTIONS: dict[Audience, str] = {
    Audience.ALL_USERS: "Every user, no filtering.",
    Audience.NEW_USERS: "Users on their first session.",
    Audience.RETURNING_USERS: "Users with at least one prior session.",
    Audience.MOBILE_USERS: "Any mobile device.",
    Audience.DESKTOP_USERS: "Desktop browsers only.",
    Audience.ANDROID_USERS: "Users on Android devices.",
    Audience.IOS_USERS: "Users on iOS devices.",
    Audience.RETURNING_ANDROID_USERS: "Returning users on Android devices.",
    Audience.HIGH_VALUE_CUSTOMERS: "Top-spending customer segment.",
    Audience.US_USERS: "Users located in the United States.",
    Audience.EU_USERS: "Users located in the European Union.",
}


def is_valid_audience(value: str) -> bool:
    """Return True if `value` is a known audience id."""
    return value in Audience._value2member_map_