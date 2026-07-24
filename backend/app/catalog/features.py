"""Feature / page catalog.

The pre-set list of website features/pages a PM can test against. Any
component that needs to enumerate valid features (Home form, Hypothesis
prompt, simulator behavior mapping) uses these enums.
"""

from __future__ import annotations

from enum import StrEnum


class Feature(StrEnum):
    """Website features / pages available for experimentation."""

    CHECKOUT = "checkout"
    CART = "cart"
    PRODUCT_PAGE = "product_page"
    SIGNUP = "signup"
    SEARCH = "search"
    HOMEPAGE = "homepage"
    ONBOARDING = "onboarding"


FEATURES: tuple[Feature, ...] = tuple(Feature)


FEATURE_DESCRIPTIONS: dict[Feature, str] = {
    Feature.CHECKOUT: "The checkout / payment flow.",
    Feature.CART: "The shopping cart page.",
    Feature.PRODUCT_PAGE: "Individual product detail pages.",
    Feature.SIGNUP: "Account signup / registration flow.",
    Feature.SEARCH: "Site search experience.",
    Feature.HOMEPAGE: "The homepage / landing page.",
    Feature.ONBOARDING: "First-run / new-user onboarding.",
}


def is_valid_feature(value: str) -> bool:
    """Return True if `value` is a known feature id."""
    return value in Feature._value2member_map_