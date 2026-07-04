import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是智慧路灯节能系统的运维问答助手。
只能根据后端提供的上下文回答。
如果上下文不足，要明确说明“当前数据不足，无法确定”。
不要编造不存在的设备、告警、光照数据。
不要声称已经执行了开灯、关灯、修改阈值等操作。
只能给排查建议，不能代替用户执行控制命令。
回答要简洁，适合项目演示和运维人员阅读。
优先用中文回答。"""


def build_mock_answer(question: str, context: dict[str, Any]) -> str:
    if context["scope"] == "device":
        device = context["device"]
        parts = [
            f"{device['device_code']} 当前状态为 {device['status']}。",
        ]
        if device.get("last_heartbeat_at"):
            parts.append(f"最近一次心跳时间为 {device['last_heartbeat_at']}。")
        if context.get("latest_light"):
            latest = context["latest_light"]
            parts.append(
                f"最新光照强度为 {latest['light_intensity']}，路灯状态为 {latest['lamp_status']}。"
            )
        else:
            parts.append("当前没有查到最新光照数据。")

        if context["unhandled_alarm_count"] > 0:
            parts.append(
                f"该设备有 {context['unhandled_alarm_count']} 条未处理告警，建议优先查看告警详情。"
            )
        if device["status"] == "offline":
            parts.append("建议检查设备供电、网络连接和 MQTT status 心跳上报程序。")
        else:
            parts.append("建议结合历史光照、阈值配置和控制日志继续排查。")
        return "".join(parts)

    stats = context["device_stats"]
    unhandled = context["unhandled_alarm_count"]
    if stats["device_count"] == 0:
        return "当前系统还没有设备数据，无法判断运行情况。建议先创建设备并上报光照或心跳数据。"

    return (
        f"当前系统共有 {stats['device_count']} 台设备，在线 {stats['online_count']} 台，"
        f"离线 {stats['offline_count']} 台，未处理告警 {unhandled} 条。"
        "建议优先关注离线设备和未处理告警，再检查最近控制日志与光照上报是否正常。"
    )


def build_fallback_answer(question: str, context: dict[str, Any], reason: str) -> str:
    return f"大模型暂不可用，已返回规则版分析。原因：{reason}。{build_mock_answer(question, context)}"


def build_user_prompt(question: str, context: dict[str, Any]) -> str:
    return (
        "用户问题：\n"
        f"{question}\n\n"
        "后端上下文 JSON：\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)}"
    )


def call_openai_compatible_chat(question: str, context: dict[str, Any]) -> str:
    if not settings.llm_base_url:
        raise RuntimeError("LLM_BASE_URL 未配置")
    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY 未配置")
    if not settings.llm_model:
        raise RuntimeError("LLM_MODEL 未配置")

    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(question, context)},
        ],
        "temperature": 0.2,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.llm_api_key}",
        },
    )

    try:
        with urlopen(request, timeout=settings.llm_timeout_seconds) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        logger.warning("LLM HTTP error: status=%s", error.code)
        raise RuntimeError(f"LLM HTTP {error.code}") from error
    except URLError as error:
        logger.warning("LLM request failed: %s", error.reason)
        raise RuntimeError("LLM 请求失败") from error
    except TimeoutError as error:
        logger.warning("LLM request timeout")
        raise RuntimeError("LLM 请求超时") from error

    result = json.loads(response_body)
    try:
        answer = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("LLM 响应格式不符合预期") from error

    if not str(answer).strip():
        raise RuntimeError("LLM 返回空回答")
    return str(answer).strip()


def generate_agent_answer(question: str, context: dict[str, Any]) -> tuple[str, str]:
    if not settings.llm_enabled:
        return build_mock_answer(question, context), "mock"

    if settings.llm_provider != "openai-compatible":
        return (
            build_fallback_answer(question, context, "暂不支持的 LLM_PROVIDER"),
            "fallback",
        )

    try:
        return call_openai_compatible_chat(question, context), "llm"
    except Exception as error:
        return build_fallback_answer(question, context, str(error)), "fallback"
