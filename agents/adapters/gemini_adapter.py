"""Google Gemini provider, shaped so the rest of the codebase never knows it's
not Anthropic.

`call_model()` in model_adapter.py returns a native `anthropic.types.Message`,
and every LangGraph node reads that exact shape — `.content` blocks with
`.type`/`.text`/`.name`/`.input`/`.id`, `.stop_reason`, and (stored back into
`messages` as an assistant turn) round-tripped through the next call. So rather
than invent a normalization layer, this adapter converts a Gemini response into
a real `anthropic.types.Message`: the blocks are genuine `TextBlock`/
`ToolUseBlock` objects, indistinguishable from a Claude turn to every caller and
to loop_runner.py's tool loop.

The reverse direction (Anthropic-style `messages`/`tools`/`system` -> Gemini
`contents`/`Tool`/system_instruction) has to accept the same three content
shapes call_model() callers produce: a bare string, a list of block *dicts*
(tool_result turns built by loop_runner), and a list of block *objects* (an
assistant turn stored as `response.content`). All three are handled here.
"""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any

from anthropic.types import Message, TextBlock, ToolUseBlock, Usage
from google import genai
from google.genai import types

from agents.config import settings

REQUEST_TIMEOUT_MS = 120_000  # mirror model_adapter.REQUEST_TIMEOUT_SECONDS

# JSON-schema keys Gemini's FunctionDeclaration parameters actually accept.
# Anthropic tool input_schema is full JSON schema; keys like additionalProperties
# or $schema make the genai SDK's Schema validation reject the whole tool, so we
# strip down to this subset recursively rather than pass the schema through raw.
_SCHEMA_KEYS = {"type", "description", "enum", "items", "properties", "required", "nullable"}


@lru_cache
def _client() -> genai.Client:
    return genai.Client(
        api_key=settings.google_api_key,
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
    )


def _get(block: Any, key: str, default: Any = None) -> Any:
    """Read `key` off a content block that may be a dict (tool_result / raw
    block built by a node) or an anthropic block object (a stored assistant
    turn). Both shapes flow through the same messages list."""
    if isinstance(block, dict):
        return block.get(key, default)
    return getattr(block, key, default)


def _sanitize_schema(schema: Any) -> Any:
    if not isinstance(schema, dict):
        return schema
    cleaned: dict[str, Any] = {}
    for key, value in schema.items():
        if key not in _SCHEMA_KEYS:
            continue
        if key == "properties" and isinstance(value, dict):
            cleaned[key] = {k: _sanitize_schema(v) for k, v in value.items()}
        elif key == "items":
            cleaned[key] = _sanitize_schema(value)
        else:
            cleaned[key] = value
    return cleaned


def _to_gemini_tools(tools: list[dict] | None) -> list[types.Tool] | None:
    if not tools:
        return None
    declarations = [
        types.FunctionDeclaration(
            name=tool["name"],
            description=tool.get("description", ""),
            parameters=_sanitize_schema(tool.get("input_schema")) or None,
        )
        for tool in tools
    ]
    return [types.Tool(function_declarations=declarations)]


def _tool_use_name_index(messages: list[dict]) -> dict[str, str]:
    """tool_use_id -> tool name, gathered across every assistant turn. Gemini's
    function_response is keyed by function *name*, but an anthropic tool_result
    only carries the tool_use_id — so we resolve the name from the tool_use
    block that opened it earlier in the conversation."""
    index: dict[str, str] = {}
    for message in messages:
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if _get(block, "type") == "tool_use":
                index[_get(block, "id")] = _get(block, "name")
    return index


def _to_gemini_contents(messages: list[dict]) -> list[types.Content]:
    name_index = _tool_use_name_index(messages)
    contents: list[types.Content] = []

    for message in messages:
        role = "model" if message.get("role") == "assistant" else "user"
        content = message.get("content")
        parts: list[types.Part] = []

        if isinstance(content, str):
            if content:
                parts.append(types.Part(text=content))
        else:
            for block in content or []:
                btype = _get(block, "type")
                if btype == "text":
                    text = _get(block, "text") or ""
                    if text:
                        parts.append(types.Part(text=text))
                elif btype == "tool_use":
                    parts.append(
                        types.Part.from_function_call(
                            name=_get(block, "name"),
                            args=dict(_get(block, "input") or {}),
                        )
                    )
                elif btype == "tool_result":
                    tool_use_id = _get(block, "tool_use_id")
                    result = _get(block, "content")
                    parts.append(
                        types.Part.from_function_response(
                            name=name_index.get(tool_use_id, tool_use_id or "tool"),
                            response={"result": result if isinstance(result, str) else str(result)},
                        )
                    )

        if parts:
            contents.append(types.Content(role=role, parts=parts))

    return contents


_FINISH_REASON_MAP = {
    "STOP": "end_turn",
    "MAX_TOKENS": "max_tokens",
    "SAFETY": "end_turn",
    "RECITATION": "end_turn",
}


def _to_anthropic_message(response: types.GenerateContentResponse, model_id: str) -> Message:
    blocks: list[TextBlock | ToolUseBlock] = []
    candidates = response.candidates or []
    parts = candidates[0].content.parts if candidates and candidates[0].content else []

    for part in parts or []:
        if getattr(part, "text", None):
            blocks.append(TextBlock(type="text", text=part.text, citations=None))
        elif getattr(part, "function_call", None):
            fc = part.function_call
            blocks.append(
                ToolUseBlock(
                    type="tool_use",
                    id=f"toolu_{uuid.uuid4().hex[:24]}",
                    name=fc.name,
                    input=dict(fc.args or {}),
                )
            )

    has_tool_use = any(b.type == "tool_use" for b in blocks)
    if has_tool_use:
        stop_reason = "tool_use"
    else:
        raw = candidates[0].finish_reason if candidates else None
        raw_name = getattr(raw, "name", str(raw)) if raw is not None else "STOP"
        stop_reason = _FINISH_REASON_MAP.get(raw_name, "end_turn")

    usage_meta = response.usage_metadata
    usage = Usage(
        input_tokens=getattr(usage_meta, "prompt_token_count", 0) or 0,
        output_tokens=getattr(usage_meta, "candidates_token_count", 0) or 0,
    )

    return Message(
        id=f"msg_{uuid.uuid4().hex[:24]}",
        type="message",
        role="assistant",
        model=model_id,
        content=blocks,
        stop_reason=stop_reason,
        stop_sequence=None,
        usage=usage,
    )


def call_gemini(
    model_id: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    system: str | None = None,
    max_tokens: int = 4096,
) -> Message:
    """Dispatch one chat completion to Gemini and return it as an
    anthropic.types.Message — the same object shape call_model()'s Anthropic
    branch returns, so callers and loop_runner are provider-agnostic."""
    if not settings.google_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set — an agent is configured for a gemini-* "
            "model but no Google credentials are available."
        )

    config = types.GenerateContentConfig(
        system_instruction=system or None,
        tools=_to_gemini_tools(tools),
        max_output_tokens=max_tokens,
    )
    response = _client().models.generate_content(
        model=model_id,
        contents=_to_gemini_contents(messages),
        config=config,
    )
    return _to_anthropic_message(response, model_id)
