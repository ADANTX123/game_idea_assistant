from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .evaluator import ProjectEvaluator
from .generator import GeneratorRouter
from .knowledge import load_knowledge_base
from .retriever import HybridRetriever
from .settings import SettingsStore


class GameIdeaAssistant:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        knowledge_path = root_dir / "data" / "knowledge_base" / "game_cases.json"
        self.log_dir = root_dir / "data" / "run_logs"
        self.settings_store = SettingsStore(root_dir / "data" / "runtime_settings.json")
        self.cases = load_knowledge_base(knowledge_path)
        self.retriever = HybridRetriever(self.cases)
        self.generator = GeneratorRouter()
        self.evaluator = ProjectEvaluator()

    def run(self, idea: str) -> dict[str, object]:
        cleaned_idea = idea.strip()
        if not cleaned_idea:
            raise ValueError("idea is empty")

        settings = self.settings_store.load()
        generated_at = datetime.now().isoformat(timespec="seconds")
        hits = self.retriever.search(cleaned_idea, top_k=3)
        plan, generator_meta = self.generator.generate(cleaned_idea, hits, settings)
        evaluation = self.evaluator.evaluate(cleaned_idea, plan, hits)
        response: dict[str, object] = {
            "idea": cleaned_idea,
            "generated_at": generated_at,
            "retrieval": [hit.to_dict() for hit in hits],
            "plan": plan,
            "evaluation": evaluation,
            "meta": {
                "knowledge_case_count": len(self.cases),
                "retriever": "hybrid_lexical_bm25",
                "settings": settings.sanitized(),
                **generator_meta,
            },
        }
        log_path = self._write_log(response)
        response["meta"]["log_file"] = str(log_path)
        return response

    def get_settings_summary(self) -> dict[str, object]:
        return self.settings_store.load().sanitized()

    def update_settings(self, updates: dict[str, object]) -> dict[str, object]:
        return self.settings_store.save(updates).sanitized()

    def health(self) -> dict[str, object]:
        return {
            "status": "ok",
            "service": "game-idea-assistant",
            "settings": self.get_settings_summary(),
        }

    def recent_runs(self, limit: int = 5) -> list[dict[str, object]]:
        if not self.log_dir.exists():
            return []

        items: list[dict[str, object]] = []
        for path in sorted(self.log_dir.glob("*.json"), reverse=True)[:limit]:
            payload = json.loads(path.read_text(encoding="utf-8"))
            items.append(
                {
                    "generated_at": payload.get("generated_at"),
                    "idea": payload.get("idea"),
                    "overall_score": payload.get("evaluation", {}).get("overall_score"),
                    "generator_mode": payload.get("meta", {}).get("generator_mode"),
                    "model": payload.get("meta", {}).get("settings", {}).get("model"),
                    "latency_ms": payload.get("meta", {}).get("latency_ms"),
                    "log_file": str(path),
                }
            )
        return items

    def _write_log(self, payload: dict[str, object]) -> Path:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}.json"
        path = self.log_dir / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
