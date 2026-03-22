from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import log

from .knowledge import KnowledgeCase
from .text_utils import expand_query_tokens, tokenize


@dataclass
class RetrievalHit:
    case: KnowledgeCase
    score: float
    matched_tokens: list[str]
    snippet: str

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.case.case_id,
            "title": self.case.title,
            "genre": self.case.genre,
            "audience": self.case.audience,
            "summary": self.case.summary,
            "score": round(self.score, 3),
            "matched_tokens": self.matched_tokens,
            "snippet": self.snippet,
            "mechanics": self.case.mechanics,
            "strengths": self.case.strengths,
            "risks": self.case.risks,
        }


class HybridRetriever:
    def __init__(self, cases: list[KnowledgeCase]) -> None:
        self.cases = cases
        self.doc_term_counts = [Counter(tokenize(case.search_text)) for case in cases]
        self.doc_lengths = [sum(counter.values()) for counter in self.doc_term_counts]
        self.avg_doc_length = max(sum(self.doc_lengths) / max(len(self.doc_lengths), 1), 1.0)
        self.doc_freq: Counter[str] = Counter()
        for counter in self.doc_term_counts:
            self.doc_freq.update(counter.keys())

    def search(self, query: str, top_k: int = 3) -> list[RetrievalHit]:
        base_tokens = tokenize(query)
        query_tokens = expand_query_tokens(base_tokens)
        query_counts = Counter(query_tokens)
        query_lower = query.lower()
        results: list[RetrievalHit] = []

        for case, term_counts, doc_length in zip(self.cases, self.doc_term_counts, self.doc_lengths):
            lexical_score = self._bm25_score(query_counts, term_counts, doc_length)
            bonus = self._bonus_score(query_lower, case)
            score = lexical_score + bonus
            matched_tokens = sorted(
                [token for token in set(query_tokens) if token in term_counts],
                key=lambda token: term_counts[token],
                reverse=True,
            )[:5]
            results.append(
                RetrievalHit(
                    case=case,
                    score=score,
                    matched_tokens=matched_tokens,
                    snippet=self._build_snippet(case),
                )
            )

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]

    def _bm25_score(self, query_counts: Counter[str], term_counts: Counter[str], doc_length: int) -> float:
        k1 = 1.5
        b = 0.75
        score = 0.0

        for token, query_frequency in query_counts.items():
            term_frequency = term_counts.get(token, 0)
            if not term_frequency:
                continue

            doc_frequency = self.doc_freq.get(token, 0)
            idf = log(1 + (len(self.cases) - doc_frequency + 0.5) / (doc_frequency + 0.5))
            numerator = term_frequency * (k1 + 1)
            denominator = term_frequency + k1 * (1 - b + b * doc_length / self.avg_doc_length)
            score += idf * (numerator / denominator) * min(query_frequency, 2)

        return score

    def _bonus_score(self, query_lower: str, case: KnowledgeCase) -> float:
        bonus = 0.0
        searchable_fields = [case.title, case.genre, case.audience, " ".join(case.tags)]
        for field in searchable_fields:
            field_lower = field.lower()
            if field_lower and field_lower in query_lower:
                bonus += 0.75

        if any(tag.lower() in query_lower for tag in case.tags):
            bonus += 0.5

        return bonus

    def _build_snippet(self, case: KnowledgeCase) -> str:
        top_mechanics = "、".join(case.mechanics[:2])
        return f"{case.summary} 关键玩法：{top_mechanics}。"
