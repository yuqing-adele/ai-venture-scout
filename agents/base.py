from __future__ import annotations
import json
import logging
import time
from anthropic import Anthropic

logger = logging.getLogger(__name__)

_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def call_claude_structured(
    system_prompt: str,
    user_message: str,
    output_schema: dict,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 4096,
) -> dict:
    """使用 tool_use 强制 Claude 输出合法 JSON，避免一切解析问题"""
    client = get_client()
    tools = [{
        "name": "output_result",
        "description": "输出结构化分析结果",
        "input_schema": output_schema,
    }]
    for attempt in range(3):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            tools=tools,
            tool_choice={"type": "tool", "name": "output_result"},
        )
        for block in response.content:
            if hasattr(block, "type") and block.type == "tool_use":
                return clean_data(block.input)
        logger.warning(f"tool_use 未返回结果，重试 {attempt+1}/3")
        time.sleep(1)
    raise ValueError("Claude tool_use 未产生输出")


def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 2048,
) -> dict:
    """保留旧接口兼容性，内部仍用文本 JSON 解析"""
    client = get_client()
    for attempt in range(3):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = response.content[0].text.strip()
        try:
            return parse_json(raw)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"JSON 解析失败（第{attempt+1}次）: {e}")
            time.sleep(1)
    raise ValueError("JSON 解析失败，已重试3次")


def parse_json(raw: str) -> dict:
    import re
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    raw = re.sub(r"\bNone\b", "null", raw)
    raw = re.sub(r"\bTrue\b", "true", raw)
    raw = re.sub(r"\bFalse\b", "false", raw)
    raw = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw)
    raw = _escape_newlines_in_strings(raw)
    raw = re.sub(r'(["}\]\d]|true|false|null)\n(\s{1,}")', r'\1,\n\2', raw)
    try:
        return clean_data(json.loads(raw))
    except json.JSONDecodeError:
        last = raw.rfind("}")
        if last > 0:
            trimmed = re.sub(r",\s*([}\]])", r"\1", raw[:last + 1])
            try:
                return clean_data(json.loads(trimmed))
            except json.JSONDecodeError:
                pass
        start, end = raw.find("{"), raw.rfind("}") + 1
        if start >= 0 and end > start:
            return clean_data(json.loads(raw[start:end]))
        raise


def _escape_newlines_in_strings(s: str) -> str:
    result, in_string, i = [], False, 0
    while i < len(s):
        c = s[i]
        if c == '\\' and in_string:
            result.append(c)
            i += 1
            if i < len(s):
                result.append(s[i])
            i += 1
            continue
        if c == '"':
            in_string = not in_string
            result.append(c)
        elif in_string and c == '\n':
            result.append('\\n')
        elif in_string and c == '\r':
            result.append('\\r')
        else:
            result.append(c)
        i += 1
    return ''.join(result)


_ARRAY_FIELDS = {
    "key_papers", "key_breakthroughs", "citations", "growth_drivers", "target_segments",
    "major_patent_holders", "chinese_patent_holders", "key_patent_areas", "notable_deals",
    "top_vc_investors", "national_policies", "shenzhen_city_policies", "district_policies",
    "big_tech_players", "startup_competitors", "chinese_competitors", "differentiation_gaps",
    "candidates", "key_customer_profiles", "core_technologies", "key_technical_risks",
    "key_components", "certifications_needed", "best_applicable_policies", "evaluations",
    "top5_ids", "honorable_mention_ids", "dimension_scores", "top_strengths", "top_risks",
    "investors", "search_keywords", "excluded_areas", "directions",
    "direct_competitors", "alternative_sources",
}


def clean_data(obj):
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k == "citations":
                result[k] = [item for item in (v or []) if isinstance(item, dict)]
            elif k in _ARRAY_FIELDS and not isinstance(v, list):
                result[k] = []
            else:
                result[k] = clean_data(v)
        return result
    if isinstance(obj, list):
        return [clean_data(item) for item in obj]
    return obj
