"""
phase2.services.query_processing_service
=========================================

Core service that coordinates the full Query Understanding pipeline.

Architecture:
    QueryProcessingService receives ALL its dependencies through constructor
    injection. It never instantiates LLM clients, normalizers, or detectors
    internally. This design enables:
        - Unit testing with mock strategies           (Open/Closed Principle)
        - Runtime strategy swaps via configuration    (Strategy Pattern)
        - Parallel or alternative pipeline paths      (future Orchestrator feature)

Pipeline stages (in order):
    1. Input Validation
    2. Normalisation          (ITextNormalizer)
    3. LLM Analysis           (single-pass: intent + entity + classification + ambiguity)
    4. Result Parsing
    5. QueryContext Assembly
    6. Metadata Stamping

LLM strategy implementations provided in this module:
    - GeminiQueryAnalyzer   — Uses Google Generative AI (Gemini) for all NLP steps
                              in a single prompt call (efficient, low-latency).
                              Implements ILLMAnalyzer.
    - FallbackQueryAnalyzer — Rule-free offline stub that returns UNKNOWN results;
                              used in tests and when LLM is unavailable.
                              Implements ILLMAnalyzer.

Configuration consumed (all from settings, never hardcoded):
    - llm.model_name
    - llm.api_key (via env)
    - llm.timeout_seconds
    - llm.max_retries
    - llm.temperature
    - llm.max_output_tokens
    - query_agent.max_query_length
    - query_agent.confidence_threshold
    - query_agent.supported_intents
    - query_agent.prompt_template_path
    - query_agent.default_language
    - security.max_payload_length
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from phase2.exceptions.query_exception import (
    AmbiguityDetectionException,
    EntityExtractionException,
    IntentDetectionException,
    QueryClassificationException,
    QueryConfigurationException,
    QueryProcessingException,
    QuerySecurityException,
    QueryTimeoutException,
    QueryValidationException,
)
from phase2.interfaces.query_agent_interface import (
    IAmbiguityDetector,
    IEntityExtractor,
    IIntentDetector,
    ILLMAnalyzer,
    IQueryClassifier,
    IQueryProcessingService,
    ITextNormalizer,
)
from phase2.models.intent import IntentResult, IntentType
from phase2.models.query_context import ExtractedEntities, QueryContext
from phase2.models.query_metadata import AmbiguityInfo, QueryClassification, QueryMetadata

logger = logging.getLogger(__name__)


# ===========================================================================
# GeminiQueryAnalyzer — ILLMAnalyzer implementation for Google Gemini
# ===========================================================================
class GeminiQueryAnalyzer(ILLMAnalyzer):
    """
    Single-pass LLM analyzer that performs intent detection, entity extraction,
    classification, and ambiguity detection in ONE API call using Google Gemini.

    Implements ILLMAnalyzer — swap by providing a different ILLMAnalyzer
    implementation without changing any other code.

    Using a single call instead of four separate calls:
        - Reduces latency by ~3-4x
        - Reduces API cost
        - Gives the model full context for each sub-task

    Args:
        api_key             : Google AI Studio API key (from env — never hardcoded).
        model_name          : Gemini model identifier (from settings).
        prompt_template     : Loaded prompt string (from file — never hardcoded).
        supported_intents   : List of intent strings (from settings).
        timeout_seconds     : Per-request timeout (from settings).
        max_retries         : Retry count for transient failures (from settings).
        temperature         : LLM sampling temperature (from settings.llm.temperature).
        max_output_tokens   : Max response tokens (from settings.llm.max_output_tokens).
        base_delay_seconds  : Initial back-off delay (from settings).
        max_delay_seconds   : Maximum back-off cap (from settings).
    """

    def __init__(
        self,
        api_key: str,
        model_name: str,
        prompt_template: str,
        supported_intents: List[str],
        timeout_seconds: float,
        max_retries: int,
        temperature: float,
        max_output_tokens: int,
        base_delay_seconds: float,
        max_delay_seconds: float,
    ) -> None:
        if not api_key:
            raise QueryConfigurationException(
                "Google API key is required for GeminiQueryAnalyzer.",
                config_key="GOOGLE_API_KEY",
            )
        if not model_name:
            raise QueryConfigurationException(
                "LLM model name must be set in configuration.",
                config_key="llm.model_name",
            )
        if not prompt_template:
            raise QueryConfigurationException(
                "Prompt template must be loaded from file before instantiation.",
                config_key="query_agent.prompt_template_path",
            )

        self._model_name = model_name
        self._prompt_template = prompt_template
        self._supported_intents = supported_intents
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._base_delay_seconds = base_delay_seconds
        self._max_delay_seconds = max_delay_seconds

        # Lazy import — keeps startup fast when Gemini is optional
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(model_name)
            logger.info("GeminiQueryAnalyzer initialised with model=%s", model_name)
        except ImportError as exc:
            raise QueryConfigurationException(
                "google-generativeai package is not installed. "
                "Run: pip install google-generativeai",
                config_key="llm.provider",
            ) from exc

    def analyse(self, normalized_query: str) -> Dict[str, Any]:
        """
        Send a single LLM request and return parsed analysis results.

        Args:
            normalized_query: The cleaned query text.

        Returns:
            Dict with keys: intent, entities, classification, ambiguity, language.

        Raises:
            QueryTimeoutException   : On LLM response timeout.
            QueryProcessingException: On unexpected LLM or parsing failure.
        """
        prompt = self._prompt_template.format(
            query=normalized_query,
            supported_intents=", ".join(self._supported_intents),
        )

        last_exc: Optional[Exception] = None
        for attempt in range(1, self._max_retries + 1):
            try:
                logger.debug(
                    "LLM analysis attempt %d/%d for query length=%d",
                    attempt, self._max_retries, len(normalized_query),
                )
                response = self._model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": self._temperature,
                        "max_output_tokens": self._max_output_tokens,
                    },
                )
                raw_text = response.text.strip()
                return self._parse_llm_response(raw_text)

            except Exception as exc:  # noqa: BLE001 — broad catch intentional for retry
                last_exc = exc
                logger.warning(
                    "LLM attempt %d failed: %s", attempt, str(exc)
                )
                if attempt < self._max_retries:
                    delay = min(
                        self._base_delay_seconds * (2 ** (attempt - 1)),
                        self._max_delay_seconds,
                    )
                    time.sleep(delay)

        raise QueryProcessingException(
            f"LLM analysis failed after {self._max_retries} attempts.",
            step="llm_analysis",
            context={"last_error": str(last_exc)},
        )

    def _parse_llm_response(self, raw_text: str) -> Dict[str, Any]:
        """
        Parse the LLM JSON response defensively.

        Args:
            raw_text: Raw LLM output string.

        Returns:
            Dict with parsed analysis.

        Raises:
            QueryProcessingException: On JSON parse failure.
        """
        # Strip markdown fences if model added them despite instructions
        clean = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
        clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE).strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM JSON response: %s", raw_text[:200])
            raise QueryProcessingException(
                "LLM returned malformed JSON. Cannot parse analysis result.",
                step="llm_response_parsing",
                context={"parse_error": str(exc)},
            ) from exc


# ===========================================================================
# Offline / test fallback analyzer — ILLMAnalyzer implementation
# ===========================================================================
class FallbackQueryAnalyzer(ILLMAnalyzer):
    """
    Offline analyzer that returns safe UNKNOWN results without any LLM call.

    Implements ILLMAnalyzer — completely interchangeable with GeminiQueryAnalyzer
    through the same interface contract.

    Used when:
        - LLM is unavailable (offline mode, test isolation)
        - Configuration sets 'llm.provider = offline'
        - Unit tests that do not need real NLP
    """

    def analyse(self, normalized_query: str) -> Dict[str, Any]:  # noqa: ARG002 — intentionally unused; satisfies ILLMAnalyzer
        """Return a safe default analysis without calling any external service."""
        return {
            "intent": {
                "primary": "general_inquiry",
                "secondary": None,
                "confidence": 0.0,
                "explanation": "Offline fallback — no LLM analysis performed.",
            },
            "entities": {
                "policy_names": [],
                "insurance_concepts": [],
                "regulatory_terms": [],
                "numbers": [],
                "dates": [],
                "coverage_periods": [],
                "medical_terms": [],
                "risk_terms": [],
                "named_entities": [],
            },
            "classification": "general",
            "ambiguity": {
                "is_ambiguous": False,
                "ambiguity_type": None,
                "missing_entities": [],
                "clarification_hints": [],
                "confidence": 0.0,
            },
            "language": "en",
        }


# ---------------------------------------------------------------------------
# Adapter classes — bridge ILLMAnalyzer to the four strategy interfaces.
# All adapters accept ILLMAnalyzer, not any concrete class.
# A single shared_cache (dict, request-scoped) is passed to every adapter
# so the LLM is called at most once per query across all pipeline steps.
# ---------------------------------------------------------------------------

class _IntentDetectorAdapter(IIntentDetector):
    """Adapts ILLMAnalyzer to the IIntentDetector interface."""

    def __init__(
        self,
        analyzer: ILLMAnalyzer,
        confidence_threshold: float,
        shared_cache: Dict[str, Dict],
    ) -> None:
        self._analyzer = analyzer
        self._threshold = confidence_threshold
        self._cache = shared_cache

    def detect(self, normalized_query: str) -> IntentResult:
        try:
            analysis = self._get_or_analyse(normalized_query)
            intent_data = analysis.get("intent", {})
            raw_label = intent_data.get("primary", "unknown")
            try:
                intent_type = IntentType(raw_label.lower().replace(" ", "_"))
            except ValueError:
                logger.warning("Unknown intent label from LLM: %s — defaulting to UNKNOWN", raw_label)
                intent_type = IntentType.UNKNOWN

            secondary_raw = intent_data.get("secondary")
            secondary = None
            if secondary_raw:
                try:
                    secondary = IntentType(secondary_raw.lower().replace(" ", "_"))
                except ValueError:
                    secondary = None

            return IntentResult(
                intent=intent_type,
                confidence=float(intent_data.get("confidence", 0.0)),
                secondary=secondary,
                raw_label=raw_label,
                explanation=intent_data.get("explanation"),
            )
        except QueryProcessingException:
            raise
        except Exception as exc:
            raise IntentDetectionException(
                f"Intent detection failed: {exc}",
                context={"error": str(exc)},
            ) from exc

    def _get_or_analyse(self, query: str) -> Dict:
        if query not in self._cache:
            self._cache[query] = self._analyzer.analyse(query)
        return self._cache[query]


class _EntityExtractorAdapter(IEntityExtractor):
    """Adapts ILLMAnalyzer to the IEntityExtractor interface."""

    def __init__(self, analyzer: ILLMAnalyzer, cache: Dict[str, Dict]) -> None:
        self._analyzer = analyzer
        self._cache = cache

    def extract(self, normalized_query: str) -> ExtractedEntities:
        try:
            analysis = self._cache.get(normalized_query) or self._analyzer.analyse(normalized_query)
            self._cache[normalized_query] = analysis
            ent = analysis.get("entities", {})
            return ExtractedEntities(
                policy_names=ent.get("policy_names", []),
                insurance_concepts=ent.get("insurance_concepts", []),
                regulatory_terms=ent.get("regulatory_terms", []),
                numbers=ent.get("numbers", []),
                dates=ent.get("dates", []),
                coverage_periods=ent.get("coverage_periods", []),
                medical_terms=ent.get("medical_terms", []),
                risk_terms=ent.get("risk_terms", []),
                named_entities=ent.get("named_entities", []),
                raw_extraction=ent,
            )
        except QueryProcessingException:
            raise
        except Exception as exc:
            raise EntityExtractionException(
                f"Entity extraction failed: {exc}",
                context={"error": str(exc)},
            ) from exc


class _QueryClassifierAdapter(IQueryClassifier):
    """Adapts ILLMAnalyzer to the IQueryClassifier interface."""

    def __init__(self, analyzer: ILLMAnalyzer, cache: Dict[str, Dict]) -> None:
        self._analyzer = analyzer
        self._cache = cache

    def classify(self, normalized_query: str, intent: IntentResult) -> QueryClassification:
        try:
            analysis = self._cache.get(normalized_query) or self._analyzer.analyse(normalized_query)
            self._cache[normalized_query] = analysis
            raw = analysis.get("classification", "general")
            try:
                return QueryClassification(raw.lower().replace(" ", "_"))
            except ValueError:
                logger.warning("Unknown classification '%s' — defaulting to GENERAL", raw)
                return QueryClassification.GENERAL
        except QueryProcessingException:
            raise
        except Exception as exc:
            raise QueryClassificationException(
                f"Classification failed: {exc}",
                context={"error": str(exc)},
            ) from exc


class _AmbiguityDetectorAdapter(IAmbiguityDetector):
    """Adapts ILLMAnalyzer to the IAmbiguityDetector interface."""

    def __init__(self, analyzer: ILLMAnalyzer, cache: Dict[str, Dict]) -> None:
        self._analyzer = analyzer
        self._cache = cache

    def detect(
        self,
        normalized_query: str,
        intent: IntentResult,
        entities: ExtractedEntities,
    ) -> AmbiguityInfo:
        try:
            analysis = self._cache.get(normalized_query) or self._analyzer.analyse(normalized_query)
            self._cache[normalized_query] = analysis
            amb = analysis.get("ambiguity", {})
            return AmbiguityInfo(
                is_ambiguous=bool(amb.get("is_ambiguous", False)),
                ambiguity_type=amb.get("ambiguity_type") or None,
                missing_entities=amb.get("missing_entities", []),
                clarification_hints=amb.get("clarification_hints", []),
                confidence=float(amb.get("confidence", 0.0)),
            )
        except QueryProcessingException:
            raise
        except Exception as exc:
            raise AmbiguityDetectionException(
                f"Ambiguity detection failed: {exc}",
                context={"error": str(exc)},
            ) from exc


# ===========================================================================
# QueryProcessingService — main service (implements IQueryProcessingService)
# ===========================================================================
class QueryProcessingService(IQueryProcessingService):
    """
    Coordinates the full Query Understanding pipeline for a single query.

    Every dependency is injected. No dependency is created internally.
    This class has no knowledge of which LLM, normalizer, or detector
    implementation is in use — it only calls the interfaces.

    Args:
        normalizer          : ITextNormalizer implementation.
        intent_detector     : IIntentDetector implementation.
        entity_extractor    : IEntityExtractor implementation.
        classifier          : IQueryClassifier implementation.
        ambiguity_detector  : IAmbiguityDetector implementation.
        max_query_length    : Maximum character length (from settings).
        agent_version       : Version string loaded from settings.
        security_max_length : Hard security cap (guard against payload attacks).
        default_language    : Default BCP-47 language code (from settings).
    """

    def __init__(
        self,
        normalizer: ITextNormalizer,
        intent_detector: IIntentDetector,
        entity_extractor: IEntityExtractor,
        classifier: IQueryClassifier,
        ambiguity_detector: IAmbiguityDetector,
        max_query_length: int,
        agent_version: str,
        security_max_length: int,
        default_language: str = "en",
    ) -> None:
        self._normalizer = normalizer
        self._intent_detector = intent_detector
        self._entity_extractor = entity_extractor
        self._classifier = classifier
        self._ambiguity_detector = ambiguity_detector
        self._max_query_length = max_query_length
        self._agent_version = agent_version
        self._security_max_length = security_max_length
        self._default_language = default_language
        logger.info(
            "QueryProcessingService initialised (agent_version=%s, max_query_length=%d)",
            agent_version,
            max_query_length,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process(self, raw_query: str) -> QueryContext:
        """
        Run the full Query Understanding pipeline on a raw user query.

        Args:
            raw_query: Exact, unmodified user input string.

        Returns:
            QueryContext: Fully populated context ready for the Retrieval Agent.

        Raises:
            QueryValidationException : On invalid input.
            QuerySecurityException   : On detected security violation.
            QueryProcessingException : On NLP pipeline failure.
            QueryTimeoutException    : On processing timeout.
        """
        start_ms = time.monotonic() * 1000
        metadata = QueryMetadata(agent_version=self._agent_version)
        logger.info(
            "Processing query (query_id=%s, length=%d)",
            metadata.query_id,
            len(raw_query) if raw_query else 0,
        )

        try:
            # ── Stage 1: Security + Input Validation ────────────────────
            self._security_check(raw_query, metadata)
            self._validate_input(raw_query, metadata)

            # ── Stage 2: Normalisation ───────────────────────────────────
            normalized = self._normalize(raw_query, metadata)

            # ── Stage 3: Intent Detection ────────────────────────────────
            intent = self._detect_intent(normalized)
            logger.info(
                "Intent detected (query_id=%s): %s (conf=%.2f)",
                metadata.query_id, intent.intent.value, intent.confidence,
            )

            # ── Stage 4: Entity Extraction ───────────────────────────────
            entities = self._extract_entities(normalized)
            logger.info(
                "Entities extracted (query_id=%s): %d unique",
                metadata.query_id, len(entities.all_entities_flat()),
            )

            # ── Stage 5: Classification ──────────────────────────────────
            classification = self._classify(normalized, intent)
            logger.info(
                "Classification (query_id=%s): %s",
                metadata.query_id, classification.value,
            )

            # ── Stage 6: Ambiguity Detection ─────────────────────────────
            ambiguity = self._detect_ambiguity(normalized, intent, entities)
            if ambiguity.is_ambiguous:
                logger.warning(
                    "Ambiguous query detected (query_id=%s, type=%s)",
                    metadata.query_id, ambiguity.ambiguity_type,
                )

            # ── Stage 7: Metadata finalisation ───────────────────────────
            end_ms = time.monotonic() * 1000
            metadata.char_count = len(raw_query)
            metadata.word_count = len(raw_query.split())
            metadata.validation_passed = True
            metadata.normalization_applied = True
            # Language: read from cached LLM analysis if available, else config default
            metadata.language = self._resolve_language(normalized)
            metadata.mark_processed(start_ms, end_ms)
            logger.info(
                "Query processing complete (query_id=%s, %.1f ms)",
                metadata.query_id, metadata.processing_time_ms or 0,
            )

            return QueryContext(
                original_query=raw_query,
                normalized_query=normalized,
                intent=intent,
                entities=entities,
                classification=classification,
                ambiguity=ambiguity,
                metadata=metadata,
            )

        except (QueryValidationException, QuerySecurityException):
            raise  # already structured — re-raise as-is
        except QueryProcessingException:
            raise
        except Exception as exc:
            logger.exception("Unexpected error in QueryProcessingService.process")
            raise QueryProcessingException(
                f"Unexpected processing failure: {exc}",
                step="unknown",
                context={"error_type": type(exc).__name__},
            ) from exc

    def validate_only(self, raw_query: str) -> bool:
        """
        Validate input without running the full pipeline.

        Useful for API-layer early rejection before allocating LLM quota.

        Args:
            raw_query: Raw user input string.

        Returns:
            bool: True if valid.

        Raises:
            QueryValidationException: On invalid input.
            QuerySecurityException  : On security violation.
        """
        meta = QueryMetadata(agent_version=self._agent_version)
        self._security_check(raw_query, meta)
        self._validate_input(raw_query, meta)
        return True

    # ------------------------------------------------------------------
    # Private pipeline steps
    # ------------------------------------------------------------------
    def _security_check(self, raw_query: str, metadata: QueryMetadata) -> None:
        """Hard security gate — rejects obviously malicious input."""
        if raw_query is None:
            raise QuerySecurityException("Null input is not allowed.")
        if len(raw_query) > self._security_max_length:
            metadata.add_validation_error("Query exceeds hard security length cap.")
            raise QuerySecurityException(
                "Request rejected: payload size exceeds the security limit."
            )
        # Detect prompt injection attempt markers
        _INJECTION_PATTERNS = [
            r"ignore\s+previous\s+instructions",
            r"disregard\s+all\s+prior",
            r"you\s+are\s+now\s+a",
        ]
        lower_q = raw_query.lower()
        for pattern in _INJECTION_PATTERNS:
            if re.search(pattern, lower_q):
                raise QuerySecurityException(
                    "Request rejected for security reasons."
                )

    def _validate_input(self, raw_query: str, metadata: QueryMetadata) -> None:
        """Structural input validation before normalisation."""
        if not isinstance(raw_query, str):
            metadata.add_validation_error("Query must be a string.")
            raise QueryValidationException("Query must be a string.", field="query")
        if not raw_query or not raw_query.strip():
            metadata.add_validation_error("Query is empty or whitespace-only.")
            raise QueryValidationException(
                "Query is empty or whitespace-only.", field="query"
            )

    def _normalize(self, raw_query: str, metadata: QueryMetadata) -> str:
        """Apply text normalisation strategy."""
        try:
            normalized = self._normalizer.normalize(raw_query)
            logger.debug("Normalisation complete: %r → %r", raw_query[:50], normalized[:50])
            return normalized
        except QueryValidationException:
            raise
        except Exception as exc:
            raise QueryProcessingException(
                f"Normalisation failed: {exc}", step="normalisation"
            ) from exc

    def _detect_intent(self, normalized: str) -> IntentResult:
        """Delegate to the injected intent detector."""
        return self._intent_detector.detect(normalized)

    def _extract_entities(self, normalized: str) -> ExtractedEntities:
        """Delegate to the injected entity extractor."""
        return self._entity_extractor.extract(normalized)

    def _classify(self, normalized: str, intent: IntentResult) -> QueryClassification:
        """Delegate to the injected classifier."""
        return self._classifier.classify(normalized, intent)

    def _detect_ambiguity(
        self,
        normalized: str,
        intent: IntentResult,
        entities: ExtractedEntities,
    ) -> AmbiguityInfo:
        """Delegate to the injected ambiguity detector."""
        return self._ambiguity_detector.detect(normalized, intent, entities)

    def _resolve_language(self, normalized_query: str) -> str:
        """
        Resolve the detected language from the cached LLM analysis.

        Falls back to the configured default_language if not available.

        Args:
            normalized_query: The query whose cached analysis to inspect.

        Returns:
            str: BCP-47 language code.
        """
        # Try to read language from the analysis result already in the adapters' cache
        try:
            # The intent detector adapter holds the shared cache — access via its internal reference
            cached = getattr(self._intent_detector, "_cache", {})
            analysis = cached.get(normalized_query, {})
            lang = analysis.get("language")
            if lang and isinstance(lang, str):
                return lang
        except Exception:
            pass
        return self._default_language


# ===========================================================================
# Factory — creates a fully wired QueryProcessingService from settings
# ===========================================================================
class QueryProcessingServiceFactory:
    """
    Factory that assembles a production-ready QueryProcessingService from
    injected configuration settings.

    This is the ONLY place where concrete classes are instantiated.
    The rest of the system codes to interfaces.

    Configuration → ILLMAnalyzer selection:
        settings.llm.provider == "gemini"     → GeminiQueryAnalyzer
        settings.llm.provider == "offline"    → FallbackQueryAnalyzer
        settings.llm.provider == "openai"     → (future: OpenAIQueryAnalyzer)
        settings.llm.provider == "anthropic"  → (future: ClaudeQueryAnalyzer)
        settings.llm.provider == "local"      → (future: LocalQueryAnalyzer)
    """

    @staticmethod
    def create(settings: Any) -> QueryProcessingService:
        """
        Build and return a fully wired QueryProcessingService.

        Args:
            settings: Configuration settings object (from phase2.config.settings).

        Returns:
            QueryProcessingService: Ready to process queries.

        Raises:
            QueryConfigurationException: On invalid or missing settings.
        """
        from phase2.utils.text_normalizer import InsuranceTextNormalizer

        # ── Load prompt template from file (never inline) ────────────────
        prompt_path = Path(settings.query_agent.prompt_template_path)
        if not prompt_path.exists():
            raise QueryConfigurationException(
                f"Prompt template not found: {prompt_path}",
                config_key="query_agent.prompt_template_path",
            )
        prompt_template = prompt_path.read_text(encoding="utf-8")
        logger.info("Loaded prompt template from %s", prompt_path)

        # ── Choose ILLMAnalyzer implementation based on provider ──────────
        provider = settings.llm.provider.lower()

        # Request-scoped cache: created fresh per factory call, shared across all adapters.
        # Per-request scope is correct — one query → one LLM call → cached for all stages.
        shared_cache: Dict[str, Dict] = {}

        if provider == "gemini":
            analyzer: ILLMAnalyzer = GeminiQueryAnalyzer(
                api_key=settings.llm.api_key,
                model_name=settings.llm.model_name,
                prompt_template=prompt_template,
                supported_intents=settings.query_agent.supported_intents,
                timeout_seconds=settings.llm.timeout_seconds,
                max_retries=settings.llm.max_retries,
                temperature=settings.llm.temperature,
                max_output_tokens=settings.llm.max_output_tokens,
                base_delay_seconds=1.0,
                max_delay_seconds=settings.llm.timeout_seconds,
            )
        elif provider == "offline":
            logger.warning(
                "Using FallbackQueryAnalyzer (offline mode). LLM results will be UNKNOWN."
            )
            analyzer = FallbackQueryAnalyzer()
        elif provider in ("openai", "anthropic", "local"):
            raise QueryConfigurationException(
                f"LLM provider '{provider}' is planned but not yet implemented. "
                "Available now: gemini, offline.",
                config_key="llm.provider",
            )
        else:
            raise QueryConfigurationException(
                f"Unsupported LLM provider: '{provider}'. "
                "Supported: gemini, openai, anthropic, local, offline.",
                config_key="llm.provider",
            )

        # ── Wire strategy adapters (all accept ILLMAnalyzer) ─────────────
        # All adapters share the same request-scoped cache — prevents duplicate LLM calls.
        intent_detector = _IntentDetectorAdapter(
            analyzer, settings.query_agent.confidence_threshold, shared_cache
        )
        entity_extractor = _EntityExtractorAdapter(analyzer, shared_cache)
        classifier = _QueryClassifierAdapter(analyzer, shared_cache)
        ambiguity_detector = _AmbiguityDetectorAdapter(analyzer, shared_cache)
        normalizer = InsuranceTextNormalizer(
            max_length=settings.query_agent.max_query_length
        )

        return QueryProcessingService(
            normalizer=normalizer,
            intent_detector=intent_detector,
            entity_extractor=entity_extractor,
            classifier=classifier,
            ambiguity_detector=ambiguity_detector,
            max_query_length=settings.query_agent.max_query_length,
            agent_version=settings.agent_version,
            security_max_length=settings.security.max_payload_length,
            default_language=settings.query_agent.default_language,
        )
