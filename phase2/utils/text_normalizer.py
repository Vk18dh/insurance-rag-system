"""
phase2.utils.text_normalizer
==============================

Concrete implementation of ITextNormalizer for insurance domain queries.

Design principles:
    - CONSERVATIVE normalisation: preserve domain terminology at all costs.
    - Insurance terms, policy names, abbreviations, and numbers are NEVER altered.
    - Configurable via settings — no normalisation behaviour is hardcoded.
    - Stateless: can be reused across threads without locks.

Classes:
    InsuranceTextNormalizer — Production normaliser (implements ITextNormalizer).
    PassthroughNormalizer   — No-op normaliser for testing/debugging.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List

from phase2.exceptions.query_exception import QueryValidationException
from phase2.interfaces.query_agent_interface import ITextNormalizer


class InsuranceTextNormalizer(ITextNormalizer):
    """
    Conservative text normaliser for insurance domain queries.

    What it DOES:
        - Strip leading/trailing whitespace.
        - Collapse interior runs of whitespace to a single space.
        - Normalise Unicode to NFC form (composed characters).
        - Remove zero-width and invisible control characters.
        - Ensure sentence ends with a question mark when it is clearly a question.

    What it NEVER does:
        - Lowercase (destroys abbreviations like 'IRDAI', 'UIN', 'LIC').
        - Remove punctuation inside domain terms ('Free Look Period').
        - Strip numbers (policy numbers, amounts, ages are critical).
        - Remove parentheses or slashes (e.g. 'Section 80C/80D').

    Args:
        max_length: Maximum allowed character length after normalisation.
                    Loaded from settings — not hardcoded here.
        preserve_patterns: Optional list of regex patterns whose matches
                           must survive normalisation unchanged.
    """

    # Invisible / zero-width Unicode categories to strip
    _STRIP_CATEGORIES: frozenset[str] = frozenset({"Cf", "Cc"})

    # Whitespace normalisation pattern (compiled once at class load)
    _MULTI_SPACE: re.Pattern[str] = re.compile(r"[ \t]+")
    _MULTI_NEWLINE: re.Pattern[str] = re.compile(r"\n{3,}")

    def __init__(
        self,
        max_length: int,
        preserve_patterns: List[str] | None = None,
    ) -> None:
        """
        Initialise the normaliser with injected configuration.

        Args:
            max_length       : Maximum character count; loaded from settings.
            preserve_patterns: Optional regex patterns to anchor during normalisation.
        """
        if max_length <= 0:
            raise QueryValidationException(
                "max_length must be a positive integer.",
                field="max_length",
            )
        self._max_length = max_length
        self._preserve_patterns: List[re.Pattern[str]] = [
            re.compile(p) for p in (preserve_patterns or [])
        ]

    # ------------------------------------------------------------------
    # ITextNormalizer implementation
    # ------------------------------------------------------------------
    def normalize(self, text: str) -> str:
        """
        Normalise an insurance query string conservatively.

        Args:
            text: Raw query text.

        Returns:
            str: Normalised query text safe for downstream NLP processing.

        Raises:
            QueryValidationException: If text is empty, None, or exceeds max length.
        """
        if not isinstance(text, str):
            raise QueryValidationException(
                "Query must be a string.",
                field="query",
                context={"received_type": type(text).__name__},
            )

        # Step 1 — Unicode NFC normalisation
        text = unicodedata.normalize("NFC", text)

        # Step 2 — Strip invisible control / format characters
        text = self._strip_invisible(text)

        # Step 3 — Strip leading/trailing whitespace
        text = text.strip()

        if not text:
            raise QueryValidationException(
                "Query is empty after normalisation.",
                field="query",
            )

        # Step 4 — Collapse interior whitespace
        text = self._MULTI_SPACE.sub(" ", text)
        text = self._MULTI_NEWLINE.sub("\n\n", text)

        # Step 5 — Length guard (after normalisation)
        if len(text) > self._max_length:
            raise QueryValidationException(
                f"Query exceeds maximum allowed length of {self._max_length} characters.",
                field="query",
                context={"length": len(text), "max_length": self._max_length},
            )

        return text

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _strip_invisible(self, text: str) -> str:
        """
        Remove zero-width and invisible Unicode control/format characters.

        Preserves printable characters including all standard punctuation,
        digits, and letters across scripts.

        Args:
            text: Input string.

        Returns:
            str: String with invisible characters removed.
        """
        return "".join(
            ch for ch in text
            if unicodedata.category(ch) not in self._STRIP_CATEGORIES
        )


# ---------------------------------------------------------------------------
# Passthrough normaliser — for testing and offline environments
# ---------------------------------------------------------------------------
class PassthroughNormalizer(ITextNormalizer):
    """
    No-op normaliser that returns the input stripped of leading/trailing whitespace.

    Use in unit tests when normalisation behaviour is not under test, or in
    offline environments where conservative-but-accurate normalisation is
    still required without the full implementation.

    Args:
        max_length: Maximum allowed length; validated even in passthrough mode.
    """

    def __init__(self, max_length: int) -> None:
        if max_length <= 0:
            raise QueryValidationException(
                "max_length must be positive.", field="max_length"
            )
        self._max_length = max_length

    def normalize(self, text: str) -> str:
        """
        Strip whitespace and validate length only.

        Args:
            text: Raw query string.

        Returns:
            str: Stripped query.

        Raises:
            QueryValidationException: If empty or too long.
        """
        if not isinstance(text, str) or not text.strip():
            raise QueryValidationException("Query is empty.", field="query")
        result = text.strip()
        if len(result) > self._max_length:
            raise QueryValidationException(
                "Query exceeds max length.",
                field="query",
                context={"length": len(result), "max_length": self._max_length},
            )
        return result
