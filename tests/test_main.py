from __future__ import annotations

import importlib
import sys
from unittest.mock import Mock

from src.app.core import dependencies


def test_importing_main_does_not_initialize_dependencies(monkeypatch) -> None:
    initialize_dependencies = Mock()
    monkeypatch.setattr(
        dependencies,
        "initialize_dependencies",
        initialize_dependencies,
    )
    sys.modules.pop("src.app.main", None)

    module = importlib.import_module("src.app.main")

    assert callable(module.app)
    initialize_dependencies.assert_not_called()
