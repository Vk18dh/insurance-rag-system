"""
phase2.validation.config.validation_settings
============================================

Configuration schema for the Validation Suite.

Contains threshold values for latency, allowed concurrent users,
and fallback logic for tests. The values map to a `validation:` block 
in phase2_config.yaml, adhering to the Zero Hardcoding Policy.
"""

import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field


class ValidationSettings(BaseModel):
    """
    Holds thresholds and behaviors specific to validation runs.
    Operates independently to prevent modifying core Phase2Settings.
    """
    
    # -------------------------------------------------------------------------
    # Performance & Load Test Thresholds
    # -------------------------------------------------------------------------
    standard_query_max_sec: float = Field(default=5.0, gt=0.0)
    heavy_query_max_sec: float = Field(default=10.0, gt=0.0)
    
    # Supported load simulation levels
    concurrent_users_low: int = Field(default=10, ge=1)
    concurrent_users_medium: int = Field(default=50, ge=1)
    concurrent_users_high: int = Field(default=100, ge=1)
    
    # -------------------------------------------------------------------------
    # Reporting Settings
    # -------------------------------------------------------------------------
    reports_output_dir: str = Field(default="phase2/validation/reports/output")
    generate_json: bool = Field(default=True)
    generate_markdown: bool = Field(default=True)
    
    # -------------------------------------------------------------------------
    # Security Test Tolerances
    # -------------------------------------------------------------------------
    fail_on_prompt_injection: bool = Field(default=True)
    
    @classmethod
    def load_from_yaml(cls, path: str = "phase2_config.yaml") -> "ValidationSettings":
        """
        Custom loader that reads the `validation` section from the main yaml,
        allowing the Validation Suite to act as an external client without
        modifying the production `Phase2Settings` object.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
                
            val_data = config_data.get("validation", {})
            return cls(**val_data)
        except Exception as e:
            # Fallback to pure defaults if the section is entirely missing
            return cls()
