from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from .retriever import RetrievalHit
from .settings import RuntimeSettings
from .text_utils import contains_any


STRING_FIELDS = [
    "project_title",
    "one_sentence_pitch",
    "target_players",
    "art_and_audio_direction",
    "session_design",
    "monetization_or_live_ops",
]

LIST_FIELDS = [
    "player_motivation",
    "core_gameplay_loop",
    "progression_system",
    "content_pillars",
    "mvp_scope",
    "risks",
    "self_revision",
]


class MockGenerator:
    def generate(self, idea: str, hits: list[RetrievalHit]) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self._infer_profile(idea, hits)
        references = self._build_references(hits)
        plan = {
            "project_title": self._build_title(profile),
            "one_sentence_pitch": self._build_pitch(profile),
            "target_players": profile["target_players"],
            "player_motivation": profile["player_motivation"],
            "core_gameplay_loop": self._build_gameplay_loop(profile),
            "progression_system": self._build_progression(profile),
            "content_pillars": self._build_content_pillars(profile),
            "art_and_audio_direction": self._build_art_direction(profile),
            "session_design": profile["session_design"],
            "monetization_or_live_ops": self._build_live_ops(profile),
            "mvp_scope": self._build_mvp_scope(),
            "risks": self._build_risks(hits),
            "self_revision": self._build_self_revision(profile),
            "references": references,
        }
        return plan, {
            "generator_mode": "mock",
            "generator_detail": "rule-based fallback",
            "provider": "local_rule_engine",
            "fallback_used": False,
        }

    def _infer_profile(self, idea: str, hits: list[RetrievalHit]) -> dict[str, Any]:
        genre = "策略养成手游"
        if contains_any(idea, ["塔防", "守塔", "防守"]):
            genre = "塔防策略手游"
        elif contains_any(idea, ["肉鸽", "roguelike"]):
            genre = "Roguelike 动作手游"
        elif contains_any(idea, ["剧情", "叙事", "故事"]):
            genre = "剧情驱动冒险手游"
        elif contains_any(idea, ["派对", "音乐", "社交"]):
            genre = "社交轻竞技手游"

        target_players = "泛二次元轻中度玩家"
        if contains_any(idea, ["轻度", "休闲", "碎片"]):
            target_players = "偏轻度的二次元手游玩家"
        if contains_any(idea, ["硬核", "高难", "竞技"]):
            target_players = "追求挑战和构筑深度的中重度玩家"

        style = "清爽明亮的日系幻想"
        if contains_any(idea, ["废土", "科幻"]):
            style = "偏科幻的高对比未来感"
        if contains_any(idea, ["治愈", "温馨", "农场"]):
            style = "柔和治愈的手绘动画感"

        session_design = "单局 6 到 8 分钟，首周目标是让玩家在 30 秒内理解局内目标。"
        if contains_any(idea, ["硬核", "竞技"]):
            session_design = "单局 12 到 15 分钟，强调中期抉择和后期翻盘空间。"

        player_motivation = [
            "获得明确且持续的成长反馈",
            "在短局内体验高强度爽感或策略决策",
            "通过角色、关卡或事件组合形成可讨论的内容",
        ]
        if contains_any(idea, ["剧情", "叙事", "故事"]):
            player_motivation[1] = "在推进剧情时保持角色关系和情绪投入"

        return {
            "idea": idea,
            "genre": genre,
            "style": style,
            "target_players": target_players,
            "session_design": session_design,
            "player_motivation": player_motivation,
            "reference_titles": [hit.case.title for hit in hits],
        }

    def _build_title(self, profile: dict[str, Any]) -> str:
        idea = profile["idea"]
        if contains_any(idea, ["塔防"]) and contains_any(idea, ["二次元", "动漫"]):
            return "星潮塔防计划"
        if contains_any(idea, ["剧情", "侦探"]):
            return "叙事谜局计划"
        if contains_any(idea, ["派对", "音乐"]):
            return "节拍派对实验"
        return "游戏创意助手输出方案"

    def _build_pitch(self, profile: dict[str, Any]) -> str:
        return (
            f"一个面向{profile['target_players']}的{profile['genre']}，"
            f"主打{profile['style']}包装下的可重复成长循环。"
        )

    def _build_gameplay_loop(self, profile: dict[str, Any]) -> list[str]:
        idea = profile["idea"]
        if contains_any(idea, ["塔防"]):
            return [
                "进入关卡前完成角色编队和站位预配置。",
                "战斗中用低频高价值技能决策强化爽感，而不是要求高压微操。",
                "结算后把掉落资源投入角色养成与关卡天赋，形成下一局提升。",
            ]
        if contains_any(idea, ["剧情", "叙事"]):
            return [
                "通过对话、调查和节点选择获取线索。",
                "把线索组织成推理链，解锁新的剧情分支或角色关系。",
                "用章节奖励强化角色能力和下一章探索权限。",
            ]
        return [
            "用一句明确的局内目标驱动玩家进入短局。",
            "在每局中提供两到三次关键抉择，让体验有策略感。",
            "用局后成长和收集反馈把玩家拉回下一个循环。",
        ]

    def _build_progression(self, profile: dict[str, Any]) -> list[str]:
        return [
            "局外成长以角色等级、技能解锁和阵容协同为主，避免一开始堆太多系统。",
            "局内成长只保留少量高识别度的随机强化，方便后续做 Eval 和版本对比。",
            "章节或赛季目标作为中期追逐点，承担留存驱动而不是一次性塞满内容。",
        ]

    def _build_content_pillars(self, profile: dict[str, Any]) -> list[str]:
        return [
            "高识别度题材包装，让玩家一句话就能复述卖点。",
            "短局可重复核心玩法，方便持续做数值和关卡迭代。",
            "轻量社交或分享点，让玩家能展示阵容、Build 或剧情分支结果。",
        ]

    def _build_art_direction(self, profile: dict[str, Any]) -> str:
        return (
            f"视觉上采用{profile['style']}，UI 用高信息密度的分区卡片而不是堆满弹窗；"
            "音频上优先做战斗反馈音和章节主题旋律，保证 MVP 阶段就有统一体验。"
        )

    def _build_live_ops(self, profile: dict[str, Any]) -> str:
        return (
            "首版只保留周常挑战和限定角色试用两个运营抓手，"
            "避免一开始就把活动系统做得过重。"
        )

    def _build_mvp_scope(self) -> list[str]:
        return [
            "1 个主玩法模式，验证核心循环是否成立。",
            "6 个可上阵角色或功能单位，保证搭配空间但控制内容成本。",
            "10 个关卡或章节节点，用来观察难度曲线与留存表现。",
            "1 套结构化输出与 Eval 报告，用于记录每次方案迭代。",
        ]

    def _build_risks(self, hits: list[RetrievalHit]) -> list[str]:
        risks = [
            "如果同时追求太多系统深度，轻度玩家会在首日流失。",
            "题材包装和核心玩法如果脱节，会出现看起来很新但玩起来很旧的问题。",
            "如果没有结构化 Eval，后续很难定位是检索、生成还是方案设计出了问题。",
        ]
        for hit in hits[:2]:
            if hit.case.risks:
                risks.append(f"参考 {hit.case.title} 的风险提示：{hit.case.risks[0]}")
        return risks[:4]

    def _build_self_revision(self, profile: dict[str, Any]) -> list[str]:
        revisions = [
            "如果目标玩家偏轻度，我会先砍掉复杂 Build 组合，把深度放到局外养成。",
            "如果后续要接真 LLM，第一步先保留 JSON Schema 和离线 Eval，不直接追求自由生成。",
            "如果首轮测试发现引用案例和生成方案脱节，需要先回头优化检索和 Prompt，而不是继续加功能。",
        ]
        if contains_any(profile["idea"], ["剧情", "叙事"]):
            revisions[0] = "如果叙事占比过高，我会把首版文本长度砍到 3 分钟可读，先验证剧情驱动力。"
        return revisions

    def _build_references(self, hits: list[RetrievalHit]) -> list[dict[str, str]]:
        reasons = [
            "用于借鉴核心循环和关卡目标设计。",
            "用于约束成长系统和付费点不要过早膨胀。",
            "用于提醒题材包装与玩法一致性。",
        ]
        references: list[dict[str, str]] = []
        for index, hit in enumerate(hits):
            references.append(
                {
                    "case_id": hit.case.case_id,
                    "title": hit.case.title,
                    "used_for": reasons[min(index, len(reasons) - 1)],
                }
            )
        return references


class OpenAICompatibleGenerator:
    def __init__(self, fallback: MockGenerator) -> None:
        self.fallback = fallback

    def generate(
        self,
        idea: str,
        hits: list[RetrievalHit],
        settings: RuntimeSettings,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if not settings.api_key:
            plan, metadata = self.fallback.generate(idea, hits)
            metadata.update(
                {
                    "requested_mode": "openai",
                    "requested_model": settings.model,
                    "request_base_url": settings.base_url,
                    "fallback_used": True,
                    "fallback_reason": "missing_api_key",
                }
            )
            return plan, metadata

        start_time = time.perf_counter()
        prompt = self._build_prompt(idea, hits)
        payload = {
            "model": settings.model,
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": prompt},
            ],
            "temperature": settings.temperature,
            "max_tokens": settings.max_output_tokens,
            "response_format": {"type": "json_object"},
        }

        url = settings.base_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url = f"{url}/chat/completions"

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=settings.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
            raw_message = raw["choices"][0]["message"]["content"]
            parsed_message = self._parse_json_object(raw_message)
            base_plan, _ = self.fallback.generate(idea, hits)
            normalized_plan = self._normalize_plan(parsed_message, base_plan, hits)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 1)
            return normalized_plan, {
                "generator_mode": "openai",
                "generator_detail": settings.model,
                "provider": "chat_completions",
                "requested_mode": "openai",
                "requested_model": settings.model,
                "request_base_url": settings.base_url,
                "fallback_used": False,
                "latency_ms": latency_ms,
            }
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, json.JSONDecodeError) as error:
            plan, metadata = self.fallback.generate(idea, hits)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 1)
            metadata.update(
                {
                    "requested_mode": "openai",
                    "requested_model": settings.model,
                    "request_base_url": settings.base_url,
                    "fallback_used": True,
                    "fallback_reason": str(error)[:240],
                    "latency_ms": latency_ms,
                }
            )
            return plan, metadata

    def _system_prompt(self) -> str:
        return (
            "你是游戏创意分析助手。你必须返回合法 JSON，不要输出 Markdown，不要输出解释文字。"
            "内容要体现工程化思维：目标用户、玩法循环、MVP 范围、风险和自我修正都要具体。"
        )

    def _build_prompt(self, idea: str, hits: list[RetrievalHit]) -> str:
        cases_text = "\n".join(
            (
                f"案例ID: {hit.case.case_id}\n"
                f"标题: {hit.case.title}\n"
                f"类型: {hit.case.genre}\n"
                f"用户: {hit.case.audience}\n"
                f"摘要: {hit.case.summary}\n"
                f"玩法: {' / '.join(hit.case.mechanics)}\n"
                f"优点: {' / '.join(hit.case.strengths)}\n"
                f"风险: {' / '.join(hit.case.risks)}"
            )
            for hit in hits
        )
        return (
            "请根据用户创意和检索案例输出一份结构化游戏设计方案。\n"
            "要求：\n"
            "1. 只能引用给定案例中的 case_id。\n"
            "2. 输出字段必须包含：project_title, one_sentence_pitch, target_players, player_motivation, core_gameplay_loop, progression_system, content_pillars, art_and_audio_direction, session_design, monetization_or_live_ops, mvp_scope, risks, self_revision, references。\n"
            "3. 其中 player_motivation, core_gameplay_loop, progression_system, content_pillars, mvp_scope, risks, self_revision 都必须是字符串数组。\n"
            "4. references 是对象数组，每项包含 case_id, title, used_for。\n"
            "5. 内容要偏产品化和工程落地，不要空泛。\n\n"
            f"用户创意：{idea}\n\n"
            f"检索案例：\n{cases_text}"
        )

    def _parse_json_object(self, text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start_index = cleaned.find("{")
            end_index = cleaned.rfind("}")
            if start_index == -1 or end_index == -1 or end_index <= start_index:
                raise
            return json.loads(cleaned[start_index : end_index + 1])

    def _normalize_plan(
        self,
        candidate: dict[str, Any],
        fallback_plan: dict[str, Any],
        hits: list[RetrievalHit],
    ) -> dict[str, Any]:
        normalized = dict(fallback_plan)
        for field in STRING_FIELDS:
            value = candidate.get(field)
            if isinstance(value, str) and value.strip():
                normalized[field] = value.strip()

        for field in LIST_FIELDS:
            value = candidate.get(field)
            if isinstance(value, list):
                cleaned = [str(item).strip() for item in value if str(item).strip()]
                if cleaned:
                    normalized[field] = cleaned[:8]

        references = candidate.get("references")
        retrieved_map = {hit.case.case_id: hit.case.title for hit in hits}
        if isinstance(references, list):
            cleaned_references: list[dict[str, str]] = []
            for item in references:
                if not isinstance(item, dict):
                    continue
                case_id = str(item.get("case_id", "")).strip()
                title = str(item.get("title", "")).strip()
                used_for = str(item.get("used_for", "")).strip()
                if case_id and used_for and case_id in retrieved_map:
                    cleaned_references.append(
                        {
                            "case_id": case_id,
                            "title": title or retrieved_map[case_id],
                            "used_for": used_for,
                        }
                    )
            if cleaned_references:
                normalized["references"] = cleaned_references[: len(hits)]

        return normalized


class GeneratorRouter:
    def __init__(self) -> None:
        self.mock = MockGenerator()
        self.openai = OpenAICompatibleGenerator(self.mock)

    def generate(
        self,
        idea: str,
        hits: list[RetrievalHit],
        settings: RuntimeSettings,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if settings.mode == "openai":
            return self.openai.generate(idea, hits, settings)
        return self.mock.generate(idea, hits)
