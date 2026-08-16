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
from typing import Any, Dict, List, Optional

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

    provider: str = Field(default="failover", description="LLM provider strategy")
    model_name: str = Field(default="", description="Legacy model name")
    primary_provider: str = Field(default="openrouter", description="Primary LLM provider")
    secondary_provider: str = Field(default="groq", description="Secondary LLM provider")
    openrouter_model: str = Field(default="google/gemma-3-27b-it:free", description="OpenRouter model")
    groq_model: str = Field(default="llama-3.3-70b-versatile", description="Groq model")
    api_key: Optional[str] = Field(default=None, description="Legacy fallback key")
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API Key")
    groq_api_key: Optional[str] = Field(default=None, description="Groq API Key")
    failover_enabled: bool = Field(default=True, description="Enable automatic failover")
    retry_backoff_seconds: float = Field(default=1.0, gt=0, description="Backoff between retries")
    timeout_seconds: float = Field(default=30.0, gt=0, description="Per-request timeout")
    max_retries: int = Field(default=3, ge=1, le=10, description="Retry count for transient failures")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="LLM temperature")
    max_output_tokens: int = Field(default=1024, gt=0, description="Max response tokens")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed = {"gemini", "openai", "anthropic", "local", "offline", "openrouter", "failover"}
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

    bm25_index_path: str = Field(default="data/bm25_index.pkl")
    chroma_dir: str = Field(default="data/chroma_db")
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


# ---------------------------------------------------------------------------
# Part 2 — Retrieval Agent settings
# ---------------------------------------------------------------------------

class RetrievalSettings(BaseModel):
    """
    Retrieval Agent configuration.

    strategy_weights maps QueryClassification values to {bm25, vector, top_k}.
    Each key must match a QueryClassification enum value or 'default'.
    The 'default' key is mandatory — used when no specific strategy matches.

    Example (from phase2_config.yaml):
        strategy_weights:
          policy_specific: { bm25: 0.7, vector: 0.3, top_k: 8 }
          regulatory:      { bm25: 0.4, vector: 0.6, top_k: 8 }
          default:         { bm25: 0.5, vector: 0.5, top_k: 8 }
    """

    top_k: int = Field(
        default=8, gt=0,
        description="Default number of evidence chunks to retrieve.",
    )
    timeout_seconds: float = Field(
        default=10.0, gt=0,
        description="Max seconds for Phase 1 retrieval before TimeoutException.",
    )
    max_retries: int = Field(
        default=2, ge=0, le=5,
        description="Max retry attempts for transient retrieval failures.",
    )
    similarity_threshold: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="Minimum combined_score for a chunk to pass validation.",
    )
    strategy_weights: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "policy_specific": {"bm25": 0.7, "vector": 0.3, "top_k": 8},
            "factual":         {"bm25": 0.5, "vector": 0.5, "top_k": 8},
            "regulatory":      {"bm25": 0.4, "vector": 0.6, "top_k": 8},
            "comparative":     {"bm25": 0.3, "vector": 0.7, "top_k": 8},
            "risk":            {"bm25": 0.5, "vector": 0.5, "top_k": 8},
            "multi_document":  {"bm25": 0.4, "vector": 0.6, "top_k": 12},
            "general":         {"bm25": 0.5, "vector": 0.5, "top_k": 8},
            "unknown":         {"bm25": 0.5, "vector": 0.5, "top_k": 8},
            "default":         {"bm25": 0.5, "vector": 0.5, "top_k": 8},
        },
        description="Per-classification retrieval weight map. 'default' is required.",
    )

    @field_validator("strategy_weights")
    @classmethod
    def validate_strategy_weights(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if "default" not in v:
            raise ValueError("retrieval.strategy_weights must contain a 'default' entry.")
        for key, cfg in v.items():
            if not isinstance(cfg, dict):
                raise ValueError(f"retrieval.strategy_weights.{key} must be a dict.")
            bm25 = float(cfg.get("bm25", 0.5))
            vector = float(cfg.get("vector", 0.5))
            if not (0.0 <= bm25 <= 1.0 and 0.0 <= vector <= 1.0):
                raise ValueError(
                    f"retrieval.strategy_weights.{key}: bm25 and vector must be in [0, 1]."
                )
        return v


class RankingSettings(BaseModel):
    """
    Evidence re-ranking configuration.

    The three signal weights control how the WeightedRankingService computes
    its composite ranking_score:

        ranking_score = (
            retrieval_score_weight * normalised_combined_score
          + keyword_overlap_weight * keyword_overlap_ratio
          + metadata_completeness_weight * metadata_completeness
        )

    Weights do not need to sum to 1.0 — they are applied independently.
    """

    retrieval_score_weight: float = Field(
        default=0.6, ge=0.0, le=1.0,
        description="Weight for the Phase 1 combined retrieval score signal.",
    )
    keyword_overlap_weight: float = Field(
        default=0.2, ge=0.0, le=1.0,
        description="Weight for query-to-chunk keyword token overlap.",
    )
    metadata_completeness_weight: float = Field(
        default=0.2, ge=0.0, le=1.0,
        description="Weight for chunk metadata completeness (source + page).",
    )
    min_ranking_score: float = Field(
        default=0.0, ge=0.0,
        description="Chunks with ranking_score below this are excluded from results.",
    )

    @model_validator(mode="after")
    def validate_weights_non_zero(self) -> "RankingSettings":
        total = self.retrieval_score_weight + self.keyword_overlap_weight + self.metadata_completeness_weight
        if total == 0.0:
            raise ValueError("Sum of ranking weights must be > 0.")
        return self


class ValidationSettings(BaseModel):
    """
    Retrieval quality validation thresholds.

    All thresholds are configurable — no hardcoded values in the validation service.
    """

    min_chunks_required: int = Field(
        default=1, ge=0,
        description="Minimum number of chunks for retrieval to be considered non-empty.",
    )
    min_similarity_score: float = Field(
        default=0.1, ge=0.0, le=1.0,
        description="Minimum top-chunk combined_score to avoid LOW_SIMILARITY warning.",
    )
    max_incomplete_metadata_ratio: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Maximum fraction of chunks allowed to have incomplete metadata.",
    )
    require_page_numbers: bool = Field(
        default=False,
        description="If True, warn when all chunks have page_number='N/A'.",
    )


class VerificationSettings(BaseModel):
    """
    Verification Agent (Part 3) configurations handling boundaries for
    evidence validation thresholds. Zero hardcoding policy enforced here.
    """
    min_relevance_score: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="Minimum score mapping valid intent to chunks."
    )
    min_evidence_count: int = Field(
        default=1, ge=1,
        description="Minimum fully cited chunks required to avoid incomplete status."
    )
    timeout_seconds: float = Field(
        default=5.0, gt=0.0,
        description="Seconds limit before verification exception fires."
    )
    max_retries: int = Field(
        default=2, ge=0,
        description="Max retries for transient verification faults."
    )
    require_citations: bool = Field(
        default=True,
        description="Strips chunks entirely if source documentation is missing."
    )
    rules: Dict[str, Any] = Field(
        default_factory=lambda: {"strict_metadata": True},
        description="Map governing structural completeness checks."
    )


class ReasoningSettings(BaseModel):
    """
    Configuration parameters regulating Part 4 logic flows and topological limits.
    """
    model_config = SettingsConfigDict(extra="forbid")

    prompt_template_path: str = Field(default="phase2/prompts/reasoning_prompt.txt", description="Path to the system logic abstraction template")
    max_steps: int = Field(default=5, ge=1, le=15, description="Maximum permitted step deductions before halting")
    explanation_format: str = Field(default="structured", description="Target representation format strings")
    max_chunk_length: int = Field(default=1000, ge=100, le=9000, description="Payload string truncation protections")
    supported_clause_relationships: List[str] = Field(
        default_factory=lambda: ["supports", "restricts", "qualifies", "overrides", "references", "complements"], 
        description="Permitted relational topology bounds"
    )
    timeout_seconds: int = Field(default=45, ge=5, le=120, description="Deduction latency tripwire")
    max_retries: int = Field(default=3, ge=0, le=5, description="Fallback attempts upon parsing failures")

class RiskSettings(BaseModel):
    """
    Configuration mapping zero hardcodes specifically constraining Part 5 Risk bounds natively.
    """
    prompt_template_path: str = Field(
        default="phase2/prompts/risk_assessment_prompt.txt",
        description="Absolute template bound securing JSON parsing routes explicitly."
    )
    timeout_seconds: float = Field(
        default=45.0, 
        ge=0.1, 
        le=120.0,
        description="Strict latency telemetry mapping preventing excessive execution limits natively."
    )
    supported_risk_categories: List[str] = Field(
        default_factory=lambda: ["Ambiguity", "Legal Sensitivity", "Regulatory", "Insurance Exclusion"],
        description="Explicit string literals safely enforcing classification checks seamlessly."
    )
    escalation_rules: List[str] = Field(
        default_factory=list,
        description="Arbitrary action definitions mapping HIGH/CRITICAL flows downstream natively."
    )

class ContradictionSettings(BaseModel):
    """Configuration mapping mapping bounds across LLM schema traces securely natively."""
    prompt_template_path: str = Field("phase2/prompts/contradiction_detection_prompt.txt", description="System constraint.")
    timeout_seconds: float = Field(45.0, ge=0.1, le=120.0, description="Latency boundary.")
    conflict_thresholds: List[str] = Field(default_factory=list, description="Map mapping CRITICAL conflicts.")
    supported_contradiction_categories: List[str] = Field(default_factory=list, description="Exclusion tracking maps.")
    comparison_rules: List[str] = Field(default_factory=list, description="Policy context boundaries.")

class OrchestratorSettings(BaseModel):
    """Configuration driving the Phase 2 Execution DAG mapping zero-hardcoded limits efficiently natively."""
    execution_sequence: List[str] = Field(
        default_factory=lambda: [
            "QueryUnderstandingAgent",
            "RetrievalAgent",
            "VerificationAgent",
            "ReasoningAgent",
            "RiskAssessmentAgent",
            "ContradictionAgent",
            "ResponseBuilder"
        ]
    )
    max_retries: int = Field(default=1, ge=0)
    retry_delay_ms: float = Field(default=200.0, ge=10.0)
    agent_timeout_ms: float = Field(default=30000.0, gt=0.0)
    max_workflow_timeout_ms: float = Field(default=120000.0, gt=0.0)

class ResponseBuilderSettings(BaseModel):
    """Configuration driving the Response Builder formatting structures mapping fallbacks explicitly."""
    fallback_explanation: str = Field(default="Unable to construct a logically verified explanation.")
    fallback_answer: str = Field(default="Insufficient policy evidence available to answer.")
    timeout_seconds: float = Field(default=45.0, ge=0.5, le=120.0, description="Latency limit.")
    retry_policy: int = Field(default=1, ge=0)
    language_options: List[str] = Field(default_factory=lambda: ["en"])


class ObservabilitySettings(BaseModel):
    """Configuration for the non-invasive Observability Layer (Part 9)."""

    enabled: bool = Field(default=True, description="Master switch — set False to use NullFacade.")
    log_level: str = Field(default="INFO", description="Logging level: DEBUG | INFO | WARNING | ERROR | CRITICAL.")
    log_dir: str = Field(default="logs", description="Directory for observability log files.")
    log_to_file: bool = Field(default=True)
    log_to_console: bool = Field(default=True)
    log_format: str = Field(default="json", description="Log format: json | text.")
    audit_enabled: bool = Field(default=True)
    audit_storage_backend: str = Field(default="json", description="Storage backend: json | sqlite.")
    audit_dir: str = Field(default="audit_logs", description="Directory for audit JSONL / SQLite files.")
    metrics_enabled: bool = Field(default=True)
    tracing_enabled: bool = Field(default=True)
    health_monitor_enabled: bool = Field(default=True)
    health_window_size: int = Field(
        default=100, ge=10, le=10000,
        description="Rolling window size for health metric computation."
    )
    alert_failure_rate_threshold: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="Failure rate fraction that triggers a HIGH alert."
    )
    alert_avg_latency_ms_threshold: float = Field(
        default=5000.0, gt=0.0,
        description="Average latency (ms) that triggers a MEDIUM alert."
    )
    query_hash_salt_env_var: str = Field(
        default="OBSERVABILITY_SALT",
        description="Name of the env var holding the HMAC salt for query hashing."
    )
    max_audit_retention_days: int = Field(
        default=30, ge=1,
        description="Number of days to retain audit files (enforced by external job)."
    )
    # Agent role classification — used to segment per-type latency (no agent logic here)
    retrieval_agent_names: List[str] = Field(
        default_factory=lambda: ["RetrievalAgent"],
        description="Agent names classified as retrieval workers for metrics segmentation."
    )
    reasoning_agent_names: List[str] = Field(
        default_factory=lambda: ["ReasoningAgent"],
        description="Agent names classified as reasoning workers for metrics segmentation."
    )
    response_agent_names: List[str] = Field(
        default_factory=lambda: ["ResponseBuilder"],
        description="Agent names classified as response workers for metrics segmentation."
    )

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid:
            raise ValueError(f"log_level must be one of {valid}, got '{v}'")
        return v.upper()

    @field_validator("audit_storage_backend")
    @classmethod
    def _validate_storage_backend(cls, v: str) -> str:
        valid = {"json", "sqlite"}
        if v.lower() not in valid:
            raise ValueError(f"audit_storage_backend must be one of {valid}, got '{v}'")
        return v.lower()

    @field_validator("log_format")
    @classmethod
    def _validate_log_format(cls, v: str) -> str:
        valid = {"json", "text"}
        if v.lower() not in valid:
            raise ValueError(f"log_format must be one of {valid}, got '{v}'")
        return v.lower()

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
    # Part 2 — Retrieval Agent
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    ranking: RankingSettings = Field(default_factory=RankingSettings)
    validation: ValidationSettings = Field(default_factory=ValidationSettings)
    # Part 3 — Verification Agent
    verification: VerificationSettings = Field(default_factory=VerificationSettings)
    # Part 4 — Reasoning Agent
    reasoning: ReasoningSettings = Field(default_factory=ReasoningSettings)
    # Part 5 — Risk Agent
    risk: RiskSettings = Field(
        default_factory=RiskSettings,
        description="Configuration for global Risk limits."
    )
    contradiction: ContradictionSettings = Field(
        default_factory=ContradictionSettings,
        description="Configuration for zero-hardcoded contradiction thresholds natively."
    )
    orchestrator: OrchestratorSettings = Field(
        default_factory=OrchestratorSettings,
        description="Configuration spanning central orchestrator loops efficiently safely."
    )
    response_builder: ResponseBuilderSettings = Field(
        default_factory=ResponseBuilderSettings,
        description="Response Builder mapping limits safely natively."
    )
    # Part 9 — Observability Layer
    observability: ObservabilitySettings = Field(
        default_factory=ObservabilitySettings,
        description="Centralized observability configuration for logging, metrics, audit, and tracing."
    )

    @model_validator(mode="after")
    def _inject_secrets(self) -> "Phase2Settings":
        """Inject secrets from environment variables — never from YAML."""
        self.llm.openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        self.llm.groq_api_key = os.environ.get("GROQ_API_KEY")
        
        if self.llm.provider.lower() == "openrouter" or self.llm.primary_provider.lower() == "openrouter":
            api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("PHASE2__LLM__API_KEY")
        else:
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
    if resolved_provider not in ["offline", "failover"] and not settings.llm.api_key:
        errors.append(
            "GOOGLE_API_KEY is required when llm.provider is not 'offline'. "
            "Set it in your .env file or set PHASE2__LLM__PROVIDER=offline for offline mode."
        )
    elif resolved_provider == "failover":
        if not settings.llm.openrouter_api_key and not settings.llm.groq_api_key:
            errors.append("Failover provider requires at least one API key (OPENROUTER_API_KEY or GROQ_API_KEY)")

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
    if resolved_provider not in ["failover", "openrouter", "offline"] and (not settings.llm.model_name or not settings.llm.model_name.strip()):
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
