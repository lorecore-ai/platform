"""PII / sensitive data detection with regex patterns and severity classification."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

# --- Pattern definitions ---------------------------------------------------

_PATTERNS: list[tuple[str, re.Pattern[str], Literal["low", "critical"], str]] = [
    # Low severity — maskable
    (
        "email",
        re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
        "low",
        "[EMAIL]",
    ),
    (
        "phone",
        re.compile(
            r"(?<!\d)"
            r"(?:\+?\d{1,3}[\s\-]?)?"
            r"(?:\(?\d{2,4}\)?[\s\-]?)?"
            r"\d{3,4}[\s\-]?\d{2,4}[\s\-]?\d{2,4}"
            r"(?!\d)"
        ),
        "low",
        "[PHONE]",
    ),
    (
        "credit_card",
        re.compile(
            r"(?<!\d)"
            r"(?:\d{4}[\s\-]?){3}\d{4}"
            r"(?!\d)"
        ),
        "low",
        "[CARD]",
    ),
    (
        "ip_address",
        re.compile(
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        ),
        "low",
        "[IP]",
    ),
    # Critical severity — reject the message
    (
        "passport_ru",
        re.compile(
            r"\b\d{2}\s?\d{2}\s?\d{6}\b"
        ),
        "critical",
        "[PASSPORT]",
    ),
    (
        "ssn",
        re.compile(
            r"\b\d{3}-\d{2}-\d{4}\b"
        ),
        "critical",
        "[SSN]",
    ),
    (
        "api_key",
        re.compile(
            r"(?i)"
            r"(?:sk-[a-zA-Z0-9]{20,})"
            r"|(?:ghp_[a-zA-Z0-9]{36,})"
            r"|(?:AKIA[0-9A-Z]{16})"
            r"|(?:-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----)"
        ),
        "critical",
        "[SECRET_KEY]",
    ),
    (
        "jwt_token",
        re.compile(
            r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"
        ),
        "critical",
        "[JWT]",
    ),
]


@dataclass
class PIIMatch:
    category: str
    severity: Literal["low", "critical"]
    span: tuple[int, int]
    replacement: str


@dataclass
class DetectionResult:
    has_critical: bool
    has_low: bool
    matches: list[PIIMatch]
    masked_text: str
    rejection_reason: str | None


def detect_pii(text: str) -> DetectionResult:
    """Scan text for PII patterns, return detection result with masked text."""
    matches: list[PIIMatch] = []

    for category, pattern, severity, replacement in _PATTERNS:
        for m in pattern.finditer(text):
            matches.append(PIIMatch(
                category=category,
                severity=severity,
                span=(m.start(), m.end()),
                replacement=replacement,
            ))

    if not matches:
        return DetectionResult(
            has_critical=False,
            has_low=False,
            matches=[],
            masked_text=text,
            rejection_reason=None,
        )

    has_critical = any(m.severity == "critical" for m in matches)
    has_low = any(m.severity == "low" for m in matches)

    critical_categories = sorted(
        {m.category for m in matches if m.severity == "critical"}
    )
    rejection_reason = (
        f"Detected critical sensitive data: {', '.join(critical_categories)}"
        if has_critical
        else None
    )

    # Build masked text (replace matches from end to start to preserve offsets)
    masked = text
    for m in sorted(matches, key=lambda x: x.span[0], reverse=True):
        start, end = m.span
        masked = masked[:start] + m.replacement + masked[end:]

    return DetectionResult(
        has_critical=has_critical,
        has_low=has_low,
        matches=matches,
        masked_text=masked,
        rejection_reason=rejection_reason,
    )
