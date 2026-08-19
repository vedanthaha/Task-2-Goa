from __future__ import annotations

import re
from dataclasses import dataclass, field
from .hybrid_retriever import HybridSearchResult


@dataclass
class GroundingResult:
    is_grounded: bool
    grounding_score: float
    supported_statements: list[str] = field(default_factory=list)
    unsupported_statements: list[str] = field(default_factory=list)
    reason: str = "ok"


class GroundingChecker:
    """Verifies that generated answers are strictly grounded in retrieved passages."""

    def __init__(self, min_grounding_threshold: float = 0.50) -> None:
        self.min_grounding_threshold = min_grounding_threshold

    def verify(
        self,
        answer: str,
        retrieved_docs: list[HybridSearchResult],
    ) -> GroundingResult:
        if not answer or not retrieved_docs:
            return GroundingResult(
                is_grounded=False,
                grounding_score=0.0,
                reason="missing_answer_or_context",
            )

        # Concatenate context terms
        combined_context = " ".join(doc.text.lower() for doc in retrieved_docs)
        context_words = set(re.findall(r"\w+", combined_context))

        # Split answer into individual sentences
        raw_sentences = re.split(r"(?<=[.!?])\s+", answer)
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 10]

        if not sentences:
            return GroundingResult(
                is_grounded=True,
                grounding_score=1.0,
                supported_statements=[answer],
            )

        supported: list[str] = []
        unsupported: list[str] = []

        for sentence in sentences:
            sentence_words = [w.lower() for w in re.findall(r"\w+", sentence) if len(w) > 3]
            if not sentence_words:
                supported.append(sentence)
                continue

            matched = sum(1 for w in sentence_words if w in context_words)
            overlap_ratio = matched / len(sentence_words)

            if overlap_ratio >= 0.40:
                supported.append(sentence)
            else:
                unsupported.append(sentence)

        total_sentences = len(sentences)
        grounding_score = len(supported) / total_sentences if total_sentences > 0 else 1.0
        is_grounded = grounding_score >= self.min_grounding_threshold

        return GroundingResult(
            is_grounded=is_grounded,
            grounding_score=round(grounding_score, 3),
            supported_statements=supported,
            unsupported_statements=unsupported,
            reason="verified" if is_grounded else "insufficient_grounding_support",
        )
