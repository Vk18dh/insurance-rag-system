"""
phase2.config — Public API exports.

    from phase2.config import get_settings, build_settings, validate_settings, Phase2Settings
"""

from phase2.config.settings import (
    Phase2Settings,
    build_settings,
    get_settings,
    validate_settings,
)

__all__ = [
    "Phase2Settings",
    "build_settings",
    "get_settings",
    "validate_settings",
]
