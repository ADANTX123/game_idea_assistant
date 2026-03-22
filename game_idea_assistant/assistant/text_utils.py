from __future__ import annotations

import re


SYNONYM_GROUPS = [
    {"塔防", "守塔", "防守"},
    {"二次元", "动漫", "日系"},
    {"肉鸽", "roguelike", "rougelike"},
    {"轻度", "休闲", "碎片化"},
    {"养成", "收集", "成长"},
    {"剧情", "叙事", "故事"},
    {"社交", "合作", "组队"},
    {"竞技", "pvp", "对抗"},
    {"卡牌", "deck", "牌组"},
]


def tokenize(text: str) -> list[str]:
    normalized = text.lower()
    tokens: list[str] = []

    for word in re.findall(r"[a-z0-9]+", normalized):
        tokens.append(word)

    for segment in re.findall(r"[\u4e00-\u9fff]+", normalized):
        if not segment:
            continue
        tokens.append(segment)
        if len(segment) == 1:
            continue
        tokens.extend(segment[index : index + 2] for index in range(len(segment) - 1))

    return [token for token in tokens if token.strip()]


def expand_query_tokens(tokens: list[str]) -> list[str]:
    expanded = list(tokens)
    seen = set(tokens)
    for token in tokens:
        for group in SYNONYM_GROUPS:
            if token in group:
                for item in group:
                    if item not in seen:
                        expanded.append(item)
                        seen.add(item)
    return expanded


def flatten_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(flatten_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {flatten_text(item)}" for key, item in value.items())
    return str(value)


def contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)
