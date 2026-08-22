from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from .hybrid_retriever import HybridSearchResult


@dataclass
class GuardrailResult:
    is_safe: bool = True
    is_on_topic: bool = True
    is_empty: bool = False
    prompt_injection_detected: bool = False
    confidence_score: float = 1.0
    passed: bool = True
    flag_reasons: list[str] = field(default_factory=list)


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"system\s+override",
    r"reveal\s+(your\s+)?(system\s+prompt|instructions)",
    r"bypass\s+all\s+(filters|rules|safeguards)",
    r"act\s+as\s+(dan|an\s+unrestricted\s+ai|an\s+evil\s+ai)",
    r"let(?:'s|s)\s+play\s+a\s+game",
    r"imagine\s+you\s+are\s+(not|no\s+longer)",
    r"pretend\s+(that\s+)?you\s+are",
    r"assume\s+(the\s+role\s+of|a\s+new\s+persona)",
    r"from\s+(now|here)\s+on\s+you\s+will",
]

UNSAFE_PATTERNS = [
    r"\b(how\s+to\s+make\s+(a\s+)?bomb|synthesize\s+illegal|create\s+malware|ransomware|ddos\s+attack)\b",
]


class SafetyGuard:
    """Multi-layer safety and input guardrails for Voice-Enabled RAG."""

    def __init__(self, min_confidence_threshold: float = 0.005) -> None:
        self.min_confidence_threshold = min_confidence_threshold

    def validate_query(self, query: str) -> GuardrailResult:
        flags: list[str] = []
        is_safe = True
        is_on_topic = True
        is_empty = False
        injection_detected = False

        query_clean = query.strip().lower()

        # Check for empty / silence
        if not query_clean or len(query_clean) < 2 or re.match(r"^[\W_]+$", query_clean):
            return GuardrailResult(
                is_safe=True,
                is_on_topic=False,
                is_empty=True,
                prompt_injection_detected=False,
                confidence_score=0.0,
                passed=False,
                flag_reasons=["No speech or clear text was detected."],
            )

        # 1. Prompt injection detection
        for pat in INJECTION_PATTERNS:
            if re.search(pat, query_clean, re.IGNORECASE):
                injection_detected = True
                is_safe = False
                flags.append(f"Prompt injection pattern detected: {pat}")
                break

        # 2. Unsafe / harmful content detection
        for pat in UNSAFE_PATTERNS:
            if re.search(pat, query_clean, re.IGNORECASE):
                is_safe = False
                flags.append("Unsafe query violating safety policies.")
                break

        passed = is_safe and is_on_topic and not injection_detected

        return GuardrailResult(
            is_safe=is_safe,
            is_on_topic=is_on_topic,
            is_empty=False,
            prompt_injection_detected=injection_detected,
            confidence_score=1.0 if passed else 0.0,
            passed=passed,
            flag_reasons=flags,
        )

    def validate_retrieval_confidence(
        self,
        query: str,
        retrieved_docs: list[HybridSearchResult],
    ) -> GuardrailResult:
        if not retrieved_docs:
            return GuardrailResult(
                is_safe=True,
                is_on_topic=False,
                confidence_score=0.0,
                passed=False,
                flag_reasons=["No relevant documents were retrieved from MSMARCO-XI dataset."],
            )

        top_score = retrieved_docs[0].fused_score
        confidence = min(1.0, top_score / 0.035)

        if top_score < self.min_confidence_threshold:
            return GuardrailResult(
                is_safe=True,
                is_on_topic=False,
                confidence_score=round(confidence, 3),
                passed=False,
                flag_reasons=[f"Retrieval confidence ({top_score:.4f}) is below minimum threshold ({self.min_confidence_threshold})."],
            )

        return GuardrailResult(
            is_safe=True,
            is_on_topic=True,
            confidence_score=round(confidence, 3),
            passed=True,
            flag_reasons=[],
        )
