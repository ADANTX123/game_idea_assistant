from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class KnowledgeCase:
    case_id: str
    title: str
    genre: str
    audience: str
    summary: str
    mechanics: list[str]
    strengths: list[str]
    risks: list[str]
    session_length: str
    tags: list[str]

    @property
    def search_text(self) -> str:
        parts: list[str] = [
            self.case_id,
            self.title,
            self.genre,
            self.audience,
            self.summary,
            self.session_length,
            " ".join(self.tags),
            " ".join(self.mechanics),
            " ".join(self.strengths),
            " ".join(self.risks),
        ]
        return " ".join(part for part in parts if part)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.case_id,
            "title": self.title,
            "genre": self.genre,
            "audience": self.audience,
            "summary": self.summary,
            "mechanics": self.mechanics,
            "strengths": self.strengths,
            "risks": self.risks,
            "session_length": self.session_length,
            "tags": self.tags,
        }


def load_knowledge_base(path: Path) -> list[KnowledgeCase]:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    cases: list[KnowledgeCase] = []
    for item in raw:
        cases.append(
            KnowledgeCase(
                case_id=item["id"],
                title=item["title"],
                genre=item["genre"],
                audience=item["audience"],
                summary=item["summary"],
                mechanics=item["mechanics"],
                strengths=item["strengths"],
                risks=item["risks"],
                session_length=item["session_length"],
                tags=item["tags"],
            )
        )
    return cases

