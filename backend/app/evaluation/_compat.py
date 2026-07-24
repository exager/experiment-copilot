"""Import-time compatibility shim for the evaluation harness.

``app.schemas.experiment`` imports ``ExperimentStatus`` from
``app.models.experiment``, a module that doesn't exist yet (only an empty
``app/models/__init__.py`` is present). Any transitive import of that module
would raise ``ImportError``. The test suite works around this in
``backend/tests/conftest.py`` by faking the module into ``sys.modules`` before
importing ``app.schemas``.

The evaluation package can be imported/run outside of pytest (e.g. via
``python -m app.evaluation.run_eval``), so we replicate the exact same guard
here. Import this module *first* — before importing anything from
``app.schemas`` or ``app.agents`` — to guarantee the shim is installed.

This is a no-op once the real ``app.models.experiment`` model lands.
"""

from __future__ import annotations

import enum
import sys
import types

if "app.models.experiment" not in sys.modules:
    _fake_experiment_model = types.ModuleType("app.models.experiment")

    class ExperimentStatus(str, enum.Enum):
        DRAFT = "draft"
        VALIDATED = "validated"
        RUNNING = "running"
        COMPLETED = "completed"
        STOPPED = "stopped"

    _fake_experiment_model.ExperimentStatus = ExperimentStatus
    sys.modules["app.models.experiment"] = _fake_experiment_model
