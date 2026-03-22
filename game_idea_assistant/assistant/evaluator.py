from __future__ import annotations

from typing import Any

from .retriever import RetrievalHit
from .text_utils import contains_any, flatten_text


REQUIRED_STRING_FIELDS = [
    "project_title",
    "one_sentence_pitch",
    "target_players",
    "art_and_audio_direction",
    "session_design",
    "monetization_or_live_ops",
]

REQUIRED_LIST_FIELDS = [
    "player_motivation",
    "core_gameplay_loop",
    "progression_system",
    "content_pillars",
    "mvp_scope",
    "risks",
    "self_revision",
    "references",
]


class ProjectEvaluator:
    def evaluate(self, idea: str, plan: dict[str, Any], hits: list[RetrievalHit]) -> dict[str, Any]:
        completeness = self._check_completeness(plan)
        formatting = self._check_format(plan)
        citations = self._check_citations(plan, hits)
        consistency = self._check_consistency(idea, plan)

        overall_score = round(
            (
                completeness["score"]
                + formatting["score"]
                + citations["score"]
                + consistency["score"]
            )
            / 4,
            1,
        )

        issues = completeness["issues"] + formatting["issues"] + citations["issues"] + consistency["issues"]
        return {
            "passed": overall_score >= 75 and formatting["passed"],
            "overall_score": overall_score,
            "checks": [completeness, formatting, citations, consistency],
            "issues": issues,
        }

    def _check_completeness(self, plan: dict[str, Any]) -> dict[str, Any]:
        total = len(REQUIRED_STRING_FIELDS) + len(REQUIRED_LIST_FIELDS)
        completed = 0
        missing: list[str] = []

        for field in REQUIRED_STRING_FIELDS:
            value = plan.get(field, "")
            if isinstance(value, str) and value.strip():
                completed += 1
            else:
                missing.append(field)

        for field in REQUIRED_LIST_FIELDS:
            value = plan.get(field, [])
            if isinstance(value, list) and value:
                completed += 1
            else:
                missing.append(field)

        score = round(completed / total * 100, 1)
        issues = [f"完整性不足，缺少字段: {', '.join(missing)}"] if missing else []
        return {
            "name": "完整性",
            "passed": not missing,
            "score": score,
            "detail": "检查关键字段是否齐全且非空。",
            "issues": issues,
        }

    def _check_format(self, plan: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        for field in REQUIRED_STRING_FIELDS:
            if not isinstance(plan.get(field, ""), str):
                issues.append(f"{field} 不是字符串")

        for field in REQUIRED_LIST_FIELDS:
            if not isinstance(plan.get(field, []), list):
                issues.append(f"{field} 不是数组")

        references = plan.get("references", [])
        if isinstance(references, list):
            for item in references:
                if not isinstance(item, dict):
                    issues.append("references 中存在非对象项")
                    continue
                for key in ("case_id", "title", "used_for"):
                    if not isinstance(item.get(key, ""), str) or not item.get(key, "").strip():
                        issues.append(f"references 缺少 {key}")
        score = 100.0 if not issues else max(40.0, 100.0 - len(issues) * 10.0)
        return {
            "name": "格式正确性",
            "passed": not issues,
            "score": round(score, 1),
            "detail": "检查 JSON 结构和字段类型。",
            "issues": issues,
        }

    def _check_citations(self, plan: dict[str, Any], hits: list[RetrievalHit]) -> dict[str, Any]:
        retrieved_ids = {hit.case.case_id for hit in hits}
        references = plan.get("references", [])
        valid = 0
        issues: list[str] = []

        if not references:
            issues.append("没有引用检索到的案例。")
        else:
            for item in references:
                case_id = item.get("case_id", "")
                if case_id in retrieved_ids:
                    valid += 1
                else:
                    issues.append(f"引用 {case_id or 'unknown'} 不在当前检索结果内。")

        total = max(len(references), 1)
        score = round(valid / total * 100, 1)
        return {
            "name": "引用有效性",
            "passed": valid > 0 and not issues,
            "score": score,
            "detail": "检查输出是否引用了当前检索回来的案例。",
            "issues": issues,
        }

    def _check_consistency(self, idea: str, plan: dict[str, Any]) -> dict[str, Any]:
        combined_text = flatten_text(plan)
        issues: list[str] = []

        if contains_any(idea, ["轻度", "休闲"]) and contains_any(
            combined_text, ["硬核", "高惩罚", "复杂数值", "重度操作"]
        ):
            issues.append("原始创意偏轻度，但方案里出现了偏硬核或高负担描述。")

        if contains_any(idea, ["单机"]) and contains_any(combined_text, ["公会", "强社交", "大型组队"]):
            issues.append("原始创意偏单机，但方案里引入了较重的社交要求。")

        if contains_any(idea, ["剧情", "叙事"]) and not contains_any(combined_text, ["剧情", "叙事", "角色关系"]):
            issues.append("原始创意强调叙事，但输出方案没有体现叙事抓手。")

        if contains_any(idea, ["二次元", "动漫"]) and not contains_any(combined_text, ["二次元", "日系", "动画感"]):
            issues.append("原始创意强调二次元，但美术方向没有明显承接。")

        session_design = str(plan.get("session_design", ""))
        if contains_any(idea, ["轻度", "休闲"]) and contains_any(session_design, ["12", "15", "20"]):
            issues.append("轻度向创意的局长看起来偏长，可能会影响首日留存。")

        score = max(50.0, 100.0 - len(issues) * 15.0)
        return {
            "name": "明显自相矛盾",
            "passed": not issues,
            "score": round(score, 1),
            "detail": "用规则启发式检查输入创意和输出方案是否冲突。",
            "issues": issues,
        }
