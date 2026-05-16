"""Centralized configuration manager for PMSS-Pro.

Consolidates all file-based configuration loading into a single,
lazy-loaded, type-safe access point. Eliminates module-level side effects
and scattered ``open("config/...")`` calls throughout the codebase.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIG_DIR = _PROJECT_ROOT / "config"


def _load_json(filename: str) -> Any:
    """Load and cache a JSON config file from the config directory."""
    path = _CONFIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {path}  "
            f"(resolved from project root: {_PROJECT_ROOT})"
        )
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_text(filename: str) -> str:
    """Load a plain-text config file."""
    path = _CONFIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {path}  "
            f"(resolved from project root: {_PROJECT_ROOT})"
        )
    return path.read_text(encoding="utf-8").strip()


# ---------------------------------------------------------------------------
# ConfigManager – single class, multiple config namespaces
# ---------------------------------------------------------------------------

class ConfigManager:
    """Lazy-loaded, thread-safe configuration manager.

    Each config file is read at most once (on first access) and then cached.
    The class is designed as a thread-safe singleton: use
    ``ConfigManager.get_instance()`` everywhere rather than constructing
    your own instance.
    """

    _instance: ConfigManager | None = None
    _lock = threading.Lock()

    # ---- public helpers ---------------------------------------------------

    @classmethod
    def get_instance(cls) -> ConfigManager:
        """Return the shared ConfigManager singleton (thread-safe)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ---- public config accessors (lazy) -----------------------------------

    @property
    def silicon_flow(self) -> dict[str, Any]:
        """SiliconFlow API configuration (key + model list).

        File: ``config/siliconFlowConfig.json``
        """
        return self._cached("silicon_flow", lambda: _load_json("siliconFlowConfig.json"))

    @property
    def api_key(self) -> str:
        """Shortcut to the SiliconFlow API key."""
        return str(self.silicon_flow["key"])

    @property
    def api_models(self) -> list[str]:
        """Shortcut to the SiliconFlow model list (deprecated alias: ``config["models"]``)."""
        return list(self.silicon_flow["models"])

    @property
    def model_list(self) -> list[str]:
        """Full model catalogue for the model-selection UI.

        File: ``config/modelList.json``
        """
        return list(self._cached("model_list", lambda: _load_json("modelList.json")))

    @property
    def translation(self) -> dict[str, str]:
        """UI string translation table.

        File: ``config/translation.json``
        """
        return dict(self._cached("translation", lambda: _load_json("translation.json")))

    @property
    def element_options(self) -> list[dict[str, Any]]:
        """Default creation options for every element type.

        File: ``config/elementOptions.json``
        """
        return list(self._cached("element_options", lambda: _load_json("elementOptions.json")))

    @property
    def environment_options(self) -> list[dict[str, Any]]:
        """Default environment parameters (gravity, air resistance, …).

        File: ``config/environmentOptions.json``
        """
        return list(self._cached("env_options", lambda: _load_json("environmentOptions.json")))

    @property
    def screen_size(self) -> tuple[int, int]:
        """Default window dimensions as ``(width, height)``.

        File: ``config/screenSize.txt``  (format: ``WIDTH x HEIGHT``)
        """
        raw: str = self._cached("screen_size", lambda: _load_text("screenSize.txt"))
        parts = raw.split("x")
        return (int(parts[0].strip()), int(parts[1].strip()))

    # ---- mutable access ---------------------------------------------------

    def set_silicon_flow_models(self, models: list[str]) -> None:
        """Replace the model list in the in-memory cache **and** persist to disk.

        This is used by the AI thread when the user switches models at
        runtime.
        """
        self.silicon_flow["models"] = list(models)
        path = _CONFIG_DIR / "siliconFlowConfig.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(self.silicon_flow, fh, indent=4)

    # ---- internal ---------------------------------------------------------

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    def _cached(self, key: str, loader: Callable[[], Any]) -> Any:
        """Return cached value, or load & cache it."""
        if key not in self._cache:
            self._cache[key] = loader()
        return self._cache[key]


# ---------------------------------------------------------------------------
# Convenience shortcut (preferred over manual singleton lookup)
# ---------------------------------------------------------------------------

config_manager = ConfigManager.get_instance()
