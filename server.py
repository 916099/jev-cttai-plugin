"""Minimal stdio MCP bridge to Jev through CTTAI; uses only Python's stdlib."""

from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SERVER_NAME = "jev-cttai"
SERVER_VERSION = "0.1.3"
DEFAULT_BASE_URL = "https://llmapi.cttai.art"
DEFAULT_MODEL = "jev-latest"
DEFAULT_SYSTEMONE_PATH = "/typesafe/v1/systemone"
DEFAULT_MODELS_PATH = "/v1/models"
TIMEOUT_SECONDS = 45


def _write(message: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _rpc_error(request_id: Any, code: int, message: str) -> None:
    _write({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})


def _tool_result(text: str, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": text}],
        "isError": is_error,
    }


def _api_request(path: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    api_key = os.environ.get("CTTAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "未设置 CTTAI_API_KEY。请在 Windows 用户环境变量中设置后，完全退出并重启 Codex。"
        )

    base_url = os.environ.get("CTTAI_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    if not base_url.startswith("https://"):
        raise RuntimeError("CTTAI_BASE_URL 必须使用 HTTPS。")
    if not path.startswith("/") or "://" in path:
        raise RuntimeError("API 路径必须是以 / 开头的相对路径。")

    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(f"{base_url}{path}", data=body, headers=headers, method=method)

    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
    except HTTPError as exc:
        # Do not return upstream response bodies: they may contain sensitive request details.
        raise RuntimeError(f"CTTAI API 返回 HTTP {exc.code}。请检查 Key、模型权限和请求参数。") from None
    except URLError as exc:
        raise RuntimeError(f"无法连接 CTTAI API：{exc.reason}") from None
    except TimeoutError:
        raise RuntimeError(f"CTTAI API 请求超过 {TIMEOUT_SECONDS} 秒。") from None

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("CTTAI API 返回了无法解析的 JSON。") from None
    if not isinstance(data, dict):
        raise RuntimeError("CTTAI API 返回格式不是 JSON 对象。")
    return data


def _validate_questions(questions: Any) -> None:
    if not isinstance(questions, dict) or not questions:
        raise ValueError("questions 必须是包含至少一个问题的对象。")
    allowed = {"choice", "score", "noul"}
    for key, question in questions.items():
        if not isinstance(key, str) or not key.strip() or not isinstance(question, dict):
            raise ValueError("questions 中每项都必须是带名称的问题对象。")
        if question.get("type") not in allowed:
            raise ValueError(f"问题 {key!r} 的 type 必须是 choice、score 或 noul。")


def _call_tool(name: str, arguments: Any) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        return _tool_result("工具参数必须是 JSON 对象。", True)

    try:
        if name == "jev_decide":
            if "state" not in arguments:
                raise ValueError("缺少 state。")
            questions = arguments.get("questions")
            _validate_questions(questions)
            model = str(arguments.get("model") or os.environ.get("CTTAI_MODEL", DEFAULT_MODEL))
            data = _api_request(
                os.environ.get("CTTAI_SYSTEMONE_PATH", DEFAULT_SYSTEMONE_PATH).strip(),
                "POST",
                {"model": model, "state": arguments["state"], "questions": questions},
            )
            return _tool_result(json.dumps(data, ensure_ascii=False, indent=2))

        if name == "jev_list_models":
            path = os.environ.get("CTTAI_MODELS_PATH", DEFAULT_MODELS_PATH).strip()
            data = _api_request(path, "GET")
            return _tool_result(json.dumps(data, ensure_ascii=False, indent=2))

        return _tool_result(f"未知工具：{name}", True)
    except (ValueError, RuntimeError) as exc:
        return _tool_result(str(exc), True)


TOOLS = [
    {
        "name": "jev_decide",
        "description": (
            "通过 CTTAI 调用 Jev，回答边界明确的选项判断、等级评分或是非（noul）问题。"
            "按 TypeSafe System One 格式提供 state 和命名问题。Jev 返回结构化判断与概率，"
            "不会撰写解释或自由文本；不要将其用于开放式写作或长链路推理。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "state": {
                    "description": "供问题判断的文本或结构化 JSON 状态。",
                    "anyOf": [
                        {"type": "string"},
                        {"type": "object"},
                        {"type": "array"},
                    ],
                },
                "questions": {
                    "type": "object",
                    "description": "TypeSafe 格式的命名问题对象；类型为 choice、score 或 noul。",
                    "additionalProperties": {"type": "object"},
                },
                "model": {
                    "type": "string",
                    "description": "可选的 CTTAI Jev 模型 ID；默认读取 CTTAI_MODEL，否则使用 jev-latest。",
                },
            },
            "required": ["state", "questions"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True},
    },
    {
        "name": "jev_list_models",
        "description": "列出当前 CTTAI API Key 可访问的 Jev 模型 ID。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True},
    },
]


def _handle(message: dict[str, Any]) -> None:
    method = message.get("method")
    request_id = message.get("id")
    if method == "notifications/initialized" or (method and method.startswith("notifications/")):
        return
    if method == "initialize":
        params = message.get("params") or {}
        version = params.get("protocolVersion", "2025-03-26")
        _write(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": version,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            }
        )
        return
    if method == "ping":
        _write({"jsonrpc": "2.0", "id": request_id, "result": {}})
        return
    if method == "tools/list":
        _write({"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}})
        return
    if method == "tools/call":
        params = message.get("params") or {}
        result = _call_tool(str(params.get("name", "")), params.get("arguments", {}))
        _write({"jsonrpc": "2.0", "id": request_id, "result": result})
        return
    if request_id is not None:
        _rpc_error(request_id, -32601, f"Method not found: {method}")


def main() -> None:
    # MCP stdio is newline-delimited UTF-8 JSON-RPC. Never write diagnostics to stdout.
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            if isinstance(message, dict):
                _handle(message)
        except json.JSONDecodeError:
            _rpc_error(None, -32700, "Parse error")
        except Exception:
            _rpc_error(None, -32603, "Internal server error")


if __name__ == "__main__":
    main()
