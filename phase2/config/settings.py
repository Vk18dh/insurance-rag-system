"""
phase2.config.settings
========================

Central configuration module for Phase 2 – Agentic RAG System.

Loading priority (highest → lowest):
    1. Environment variables  (PHASE2__SECTION__KEY)
    2. phase2_config.yaml     (project root)
    3. Pydantic field defaults (fallback only)

Secrets (API keys, JWT secrets) MUST be in environment variables only.
They must NEVER appear in YAML config files.

Startup validation:
    Call validate_settings(settings) at application startup.
    The application must fail-fast if required configuration is missing or invalid.

Usage:
    from phase2.config.settings import get_settings, Phase2Settings

    settings = get_settings()           # Cached singleton
    model    = settings.llm.model_name  # Typed access
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from phase2.exceptions.query_exception import QueryConfigurationException

logger = logging.getLogger(__name__)

# Project root = parent of this file's package (phase2/config/settings.py → majorcode/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_FILE = _PROJECT_ROOT / "phase2_config.yaml"


# ===========================================================================
# Sub-setting models (nested Pydantic models for each config section)
# ===========================================================================

class LLMSettings(BaseModel):
    """LLM provider and model configuration."""

    provider: str = Field(default="gemini", description="LLM provider: gemini | offline")
    model_name: str = Field(default="gemma-3-27b-it", description="LLM model identifier")
    api_key: Optional[str] = Field(default=None, description="Loaded from GOOGLE_API_KEY env var")
    timeout_seconds: float = Field(default=30.0, gt=0, description="Per-request timeout")
    max_retries: int = Field(default=3, ge=1, le=10, description="Retry count for transient failures")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="LLM temperature")
    max_output_tokens: int = Field(default=1024, gt=0, description="Max response tokens")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed = {"gemini", "openai", "anthropic", "local", "offline"}
        if v.lower() not in allowed:
            raise ValueError(f"llm.provider must be one of {allowed}, got: {v!r}")
        return v.lower()


class QueryAgentSettings(BaseModel):
    """Query Understanding Agent configuration."""

    agent_name: str = Field(default="QueryUnderstandingAgent")
    max_query_length: int = Field(default=2000, gt=0)
    min_query_length: int = Field(default=3, ge=1)
    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    log_query_preview_length: int = Field(default=80, gt=0)
    prompt_template_path: str = Field(
        default="phase2/prompts/query_understanding_prompt.txt"
    )
    default_language: str = Field(
        default="en",
        description="BCP-47 fallback language code when LLM does not return a language.",
    )
    supported_intents: List[str] = Field(
        default_factory=lambda: [
            "policy_information", "benefits", "exclusions", "premium",
            "eligibility", "claim_process", "maturity", "surrender",
            "loan", "nomination", "rider", "tax_benefit", "waiting_period",
            "regulatory_information", "compliance", "general_inquiry", "unknown",
        ]
    )
    classification_types: List[str] = Field(
        default_factory=lambda: [
            "factual", "comparative", "regulatory", "risk",
            "policy_specific", "multi_document", "general", "unknown",
        ]
    )

    @model_validator(mode="after")
    def validate_length_order(self) -> "QueryAgentSettings":
        if self.min_query_length >= self.max_query_length:
            raise ValueError(
                f"min_query_length ({self.min_query_length}) must be less than "
                f"max_query_length ({self.max_query_length})"
            )
        return self


class SecuritySettings(BaseModel):
    """Security and input sanitisation configuration."""

    max_payload_length: int = Field(default=10000, gt=0)
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )
    rate_limit_requests_per_minute: int = Field(default=60, gt=0)
    request_timeout_seconds: float = Field(default=60.0, gt=0)


class LoggingSettings(BaseModel):
    """Structured logging configuration."""

    level: str = Field(default="INFO")
    format: str = Field(default="json")
    log_dir: str = Field(default="logs/phase2")
    log_filename: str = Field(default="phase2.log")
    max_bytes: int = Field(default=10_485_760)   # 10 MB
    backup_count: int = Field(default=5, ge=1)
    include_query_preview: bool = Field(default=True)

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        up = v.upper()
        if up not in allowed:
            raise ValueError(f"logging.level must be one of {allowed}")
        return up

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        allowed = {"json", "text"}
        if v.lower() not in allowed:
            raise ValueError(f"logging.format must be one of {allowed}")
        return v.lower()


class Phase1Settings(BaseModel):
    """Phase 1 integration parameters consumed by the Retrieval Agent (Part 2)."""

    chroma_collection_name: str = Field(default="insurance_docs")
    top_k: int = Field(default=8, gt=0)
    bm25_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    vector_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    similarity_threshold: float = Field(default=0.4, ge=0.0, le=1.0)


class APISettings(BaseModel):
    """FastAPI server settings."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, gt=0, lt=65536)
    prefix: str = Field(default="/api/v2")
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")


# ===========================================================================
# Root settings object
# ===========================================================================

class Phase2Settings(BaseSettings):
    """
    Root configuration object for all Phase 2 settings.

    Loaded from:
        1. Environment variables (PHASE2__ prefix)
        2. phase2_config.yaml
        3. Field defaults

    Secrets:
        llm.api_key is loaded from GOOGLE_API_KEY env var in post-init.
        It is never read from YAML.
    """

    model_config = SettingsConfigDict(
        env_prefix="PHASE2__",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    agent_version: str = Field(default="2.0.0")
    environment: str = Field(default="development")

    llm: LLMSettings = Field(default_factory=LLMSettings)
    query_agent: QueryAgentSettings = Field(default_factory=QueryAgentSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    phase1: Phase1Settings = Field(default_factory=Phase1Settings)
    api: APISettings = Field(default_factory=APISettings)

    @model_validator(mode="after")
    def _inject_secrets(self) -> "Phase2Settings":
        """Inject secrets from environment variables — never from YAML."""
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("PHASE2__LLM__API_KEY")
        if api_key:
            self.llm.api_key = api_key
        return self

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "testing", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v.lower()


# ===========================================================================
# YAML loader
# ===========================================================================

def _load_yaml_config(path: Path) -> dict:
    """
    Load configuration from a YAML file.

    Args:
        path: Absolute path to the YAML config file.

    Returns:
        dict: Parsed YAML content (empty dict if file missing).

    Raises:
        QueryConfigurationException: If file exists but cannot be parsed.
    """
    if not path.exists():
        logger.warning("Phase 2 config file not found at %s — using defaults.", path)
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        logger.debug("Loaded phase2 config from %s", path)
        return data
    except yaml.YAMLError as exc:
        raise QueryConfigurationException(
            f"Failed to parse phase2_config.yaml: {exc}",
            config_key="phase2_config.yaml",
        ) from exc


# ===========================================================================
# Settings factory + cached singleton
# ===========================================================================

def _deep_merge(base: dict, override: dict) -> dict:
    """
    Deep-merge two dicts. Values in `override` always win.
    Nested dicts are merged recursively; other types are replaced entirely.
    """
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def build_settings(config_path: Optional[Path] = None) -> Phase2Settings:
    """
    Build Phase2Settings from YAML, then apply environment variable overrides.

    Priority (highest → lowest):
        1. PHASE2__* environment variables
        2. phase2_config.yaml
        3. Pydantic field defaults

    Args:
        config_path: Optional custom path to YAML file (defaults to project root).

    Returns:
        Phase2Settings: Fully validated settings instance.

    Raises:
        QueryConfigurationException: On YAML parse error or validation failure.
    """
    yaml_data = _load_yaml_config(config_path or _CONFIG_FILE)

    # --- Build env-override dict from PHASE2__ prefixed variables ---
    # pydantic-settings handles top-level env vars automatically.
    # For nested keys (PHASE2__LLM__PROVIDER) we also build a nested dict
    # so they override YAML values passed as constructor kwargs.
    env_overrides: dict = {}
    prefix = "PHASE2__"
    for key, val in os.environ.items():
        if key.upper().startswith(prefix):
            parts = key[len(prefix):].lower().split("__")
            node = env_overrides
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = val

    merged = _deep_merge(yaml_data, env_overrides)

    try:
        settings = Phase2Settings(**merged)
        logger.info(
            "Phase2Settings loaded (env=%s, llm_provider=%s, model=%s)",
            settings.environment,
            settings.llm.provider,
            settings.llm.model_name,
        )
        return settings
    except Exception as exc:
        raise QueryConfigurationException(
            f"Invalid Phase 2 configuration: {exc}",
            config_key="phase2_config",
        ) from exc


@lru_cache(maxsize=1)
def get_settings() -> Phase2Settings:
    """
    Return the cached Phase2Settings singleton.

    The singleton is built once per process. In testing, call
    get_settings.cache_clear() to force a rebuild with different env vars.

    Returns:
        Phase2Settings: Application-wide configuration singleton.
    """
    return build_settings()


# ===========================================================================
# Startup validation — fail-fast
# ===========================================================================

def validate_settings(settings: Phase2Settings) -> None:
    """
    Validate all required configuration at application startup.

    Raises:
        QueryConfigurationException: On any missing or invalid required value.
                                     Application must NOT start with invalid config.

    Args:
        settings: The Phase2Settings instance to validate.
    """
    errors: list[str] = []

    # LLM API key is required unless running in offline mode
    resolved_provider = (settings.llm.provider or "").lower()
    if resolved_provider != "offline" and not settings.llm.api_key:
        errors.append(
            "GOOGLE_API_KEY is required when llm.provider is not 'offline'. "
            "Set it in your .env file or set PHASE2__LLM__PROVIDER=offline for offline mode."
        )

    # Prompt template must exist on disk
    prompt_path = _PROJECT_ROOT / settings.query_agent.prompt_template_path
    if not prompt_path.exists():
        errors.append(
            f"Prompt template not found: {prompt_path}. "
            "Ensure phase2/prompts/query_understanding_prompt.txt exists."
        )

    # Log directory must be creatable
    try:
        log_dir = Path(settings.logging.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        errors.append(f"Cannot create log directory '{settings.logging.log_dir}': {exc}")

    # Weight sanity check for retrieval
    total_weight = settings.phase1.bm25_weight + settings.phase1.vector_weight
    if abs(total_weight - 1.0) > 0.01:
        errors.append(
            f"phase1.bm25_weight + phase1.vector_weight must sum to 1.0, "
            f"got {total_weight:.3f}"
        )

    # LLM model name must not be empty
    if not settings.llm.model_name or not settings.llm.model_name.strip():
        errors.append(
            "llm.model_name must not be empty. Set it in phase2_config.yaml or via "
            "PHASE2__LLM__MODEL_NAME env var."
        )

    # Supported intents must be non-empty
    if not settings.query_agent.supported_intents:
        errors.append(
            "query_agent.supported_intents must not be empty. "
            "At minimum include 'general_inquiry' and 'unknown'."
        )

    # Chroma collection name must not be empty
    if not settings.phase1.chroma_collection_name or not settings.phase1.chroma_collection_name.strip():
        errors.append(
            "phase1.chroma_collection_name must not be empty. "
            "Set it in phase2_config.yaml."
        )

    if errors:
        error_msg = "\n".join(f"  • {e}" for e in errors)
        raise QueryConfigurationException(
            f"Phase 2 startup validation failed:\n{error_msg}",
            config_key="startup_validation",
        )

    logger.info(
        "Phase 2 configuration validated OK (env=%s, provider=%s)",
        settings.environment,
        settings.llm.provider,
    )
