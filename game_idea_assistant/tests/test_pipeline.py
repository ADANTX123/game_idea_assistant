from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from assistant import GameIdeaAssistant
from assistant.generator import GeneratorRouter
from assistant.knowledge import load_knowledge_base
from assistant.retriever import HybridRetriever
from assistant.settings import RuntimeSettings, SettingsStore


class PipelineTestCase(unittest.TestCase):
    def test_pipeline_returns_structured_output(self) -> None:
        assistant = GameIdeaAssistant(PROJECT_ROOT)
        result = assistant.run("做一个二次元塔防游戏，面向轻度玩家，强调爽感和养成。")

        self.assertIn("plan", result)
        self.assertIn("evaluation", result)
        self.assertIn("retrieval", result)
        self.assertGreaterEqual(len(result["retrieval"]), 1)
        self.assertIn("project_title", result["plan"])
        self.assertIn("overall_score", result["evaluation"])

    def test_references_come_from_retrieval(self) -> None:
        assistant = GameIdeaAssistant(PROJECT_ROOT)
        result = assistant.run("做一个剧情向侦探手游，强调角色关系和章节悬念。")

        retrieved_ids = {item["id"] for item in result["retrieval"]}
        referenced_ids = {item["case_id"] for item in result["plan"]["references"]}
        self.assertTrue(referenced_ids.issubset(retrieved_ids))

    def test_openai_mode_without_key_falls_back_to_mock(self) -> None:
        cases = load_knowledge_base(PROJECT_ROOT / "data" / "knowledge_base" / "game_cases.json")
        hits = HybridRetriever(cases).search("做一个二次元塔防游戏", top_k=3)
        plan, meta = GeneratorRouter().generate(
            "做一个二次元塔防游戏",
            hits,
            RuntimeSettings(mode="openai", api_key="", model="gpt-4.1-mini"),
        )

        self.assertIn("project_title", plan)
        self.assertEqual(meta["generator_mode"], "mock")
        self.assertEqual(meta["requested_mode"], "openai")
        self.assertEqual(meta["fallback_reason"], "missing_api_key")

    def test_settings_store_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SettingsStore(Path(temp_dir) / "runtime_settings.json")
            saved = store.save(
                {
                    "mode": "openai",
                    "model": "gpt-4.1-mini",
                    "base_url": "https://example.com/v1",
                    "temperature": 0.6,
                    "timeout_seconds": 30,
                    "max_output_tokens": 1500,
                    "api_key": "sk-test",
                }
            )

            loaded = store.load()
            self.assertEqual(saved.mode, "openai")
            self.assertEqual(loaded.model, "gpt-4.1-mini")
            self.assertEqual(loaded.base_url, "https://example.com/v1")
            self.assertEqual(loaded.api_key, "sk-test")

    def test_service_reads_saved_runtime_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "assistant").mkdir(parents=True, exist_ok=True)
            (root / "data" / "run_logs").mkdir(parents=True, exist_ok=True)
            (root / "data" / "knowledge_base").mkdir(parents=True, exist_ok=True)
            shutil.copy2(
                PROJECT_ROOT / "data" / "knowledge_base" / "game_cases.json",
                root / "data" / "knowledge_base" / "game_cases.json",
            )

            assistant = GameIdeaAssistant(root)
            assistant.update_settings({"mode": "openai", "model": "demo-model", "api_key": "sk-demo"})
            result = assistant.run("做一个二次元塔防游戏，面向轻度玩家，强调爽感和养成。")
            self.assertEqual(result["meta"]["settings"]["mode"], "openai")
            self.assertEqual(result["meta"]["settings"]["model"], "demo-model")


if __name__ == "__main__":
    unittest.main()
