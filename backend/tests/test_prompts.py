"""Prompt-template tests (Developer 4, Phase 4).

Each of the six prompt files in ``app/prompts/`` is rendered by its paired
agent with ``str.format(**kwargs)``. These tests guard against the most common
prompt-engineering breakage without needing any API key:

* every prompt ``str.format``s cleanly with *exactly* the keys its agent
  supplies (no ``KeyError`` from an unknown placeholder, no
  ``ValueError``/``IndexError`` from a stray/positional brace), and
* the set of placeholders in the file matches the agent's key set exactly, so
  the prompt and the agent can never silently drift apart.

The expected key sets below are the authoritative ``_PROMPT.format(...)`` call
sites in each ``app/agents/*.py`` node. Keep them in sync with the agents.

``conftest.py`` installs the ``app.models.experiment`` shim into ``sys.modules``
before this module imports anything from ``app``, so importing ``app`` here is
safe.
"""

from __future__ import annotations

import string
from pathlib import Path

import pytest

import app

PROMPTS_DIR = Path(app.__file__).resolve().parent / "prompts"

# prompt filename -> exact set of placeholder keys the paired agent passes to
# ``_PROMPT.format(...)``. Derived from the format() call sites in:
#   context_understanding.md  <- app/agents/context_agent.py
#   hypothesis.md             <- app/agents/hypothesis_agent.py
#   experiment_design.md      <- app/agents/experiment_design_agent.py
#   validation.md             <- app/agents/validation_agent.py
#   explanation.md            <- app/agents/explanation_agent.py
#   report.md                 <- app/agents/report_agent.py
EXPECTED_KEYS: dict[str, set[str]] = {
    "context_understanding.md": {
        "business_goal",
        "website",
        "current_flow",
        "feature",
        "pain_point",
    },
    "hypothesis.md": {
        "business_goal",
        "website",
        "current_flow",
        "feature",
        "pain_point",
        "catalog",
    },
    "experiment_design.md": {
        "experiment_name",
        "hypothesis",
        "primary_metric",
        "secondary_metrics",
        "guardrail_metrics",
        "catalog",
    },
    "validation.md": {
        "configuration",
        "decision",
        "rules_matched",
        "rules_rejected",
    },
    "explanation.md": {
        "hypothesis",
        "control_conversion_rate",
        "variant_conversion_rate",
        "conversion_lift",
        "confidence",
        "winner",
        "recommendation",
    },
    "report.md": {
        "business_goal",
        "hypothesis",
        "configuration",
        "statistics",
        "recommendation",
        "business_impact",
    },
}


def _extract_placeholders(text: str) -> set[str]:
    """Return the base field names of every ``{placeholder}`` in ``text``.

    Uses :class:`string.Formatter` (the same parser ``str.format`` uses), so a
    stray/unbalanced brace raises ``ValueError`` here just as it would at render
    time. Positional/empty fields (``{}`` / ``{0}``) are surfaced as-is so the
    caller can reject them.
    """
    names: set[str] = set()
    for _literal, field_name, _spec, _conv in string.Formatter().parse(text):
        if field_name is None:
            continue
        # ``{foo.bar}`` / ``{foo[0]}`` -> base name ``foo``; ``{}`` -> ``""``.
        base = field_name.split(".")[0].split("[")[0]
        names.add(base)
    return names


def _read_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    assert path.is_file(), f"prompt file not found: {path}"
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("filename", sorted(EXPECTED_KEYS))
def test_prompt_placeholders_match_agent_keys(filename: str) -> None:
    """The braces in the prompt are exactly the keys the agent supplies."""
    text = _read_prompt(filename)
    expected = EXPECTED_KEYS[filename]

    found = _extract_placeholders(text)

    # No positional or empty placeholders ({}, {0}) — every brace must be a
    # named field the agent knows about.
    positional = {name for name in found if name == "" or name.isdigit()}
    assert not positional, f"{filename} has positional/empty placeholders: {positional}"

    assert found == expected, (
        f"{filename} placeholders {sorted(found)} != agent keys {sorted(expected)}"
    )


@pytest.mark.parametrize("filename", sorted(EXPECTED_KEYS))
def test_prompt_formats_cleanly_with_agent_keys(filename: str) -> None:
    """``str.format`` with exactly the agent's keys renders without error."""
    text = _read_prompt(filename)
    dummy_kwargs = {key: f"<{key}>" for key in EXPECTED_KEYS[filename]}

    # Must not raise KeyError (unknown placeholder), IndexError (positional),
    # or ValueError (stray single brace / malformed field).
    rendered = text.format(**dummy_kwargs)

    # Every placeholder was substituted, and no stray single braces remain.
    for key in dummy_kwargs:
        assert f"{{{key}}}" not in rendered
    assert "{" not in rendered and "}" not in rendered, (
        f"{filename} still contains a brace after formatting — likely a stray "
        f"'{{' or '}}' in the prose"
    )
