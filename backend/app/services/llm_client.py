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

OFFLINE_KEYWORDS = ("离线", "在线", "心跳", "status", "断连", "掉线")
THRESHOLD_KEYWORDS = ("阈值", "开灯", "关灯", "光照", "亮度", "lux", "telemetry")
CONTROL_KEYWORDS = ("控制", "命令", "响应", "执行", "turn_on", "turn_off", "brightness")
ALARM_KEYWORDS = ("告警", "报警", "异常", "offline alarm")
GREETING_WORDS = (
    "你好",
    "您好",
    "hello",
    "hi",
    "嗨",
    "在吗",
    "你是谁",
    "你能做什么",
    "你可以做什么",
)


def contains_any_keyword(question: str, keywords: tuple[str, ...]) -> bool:
    normalized_question = question.lower()
    return any(keyword.lower() in normalized_question for keyword in keywords)


def is_small_talk_question(question: str) -> bool:
    normalized_question = question.strip().lower()
    if not normalized_question:
        return False

    direct_matches = {
        "你好",
        "您好",
        "hello",
        "hi",
        "嗨",
        "在吗",
        "你是谁",
        "你能做什么",
        "你可以做什么",
    }
    if normalized_question in direct_matches:
        return True

    return (
        len(normalized_question) <= 12
        and contains_any_keyword(normalized_question, GREETING_WORDS)
    )


def build_small_talk_answer() -> str:
    return (
        "你好，我是智慧路灯系统的运维问答助手。"
        "我可以帮你分析设备离线、告警、光照阈值、控制记录和指定设备状态。"
        "例如你可以问：SL-001 为什么离线？或 当前系统有哪些告警需要处理？"
    )


def describe_light_with_threshold(context: dict[str, Any]) -> str:
    latest = context.get("latest_light")
    config = context.get("threshold_config")
    if not latest:
        return "当前没有查到最新光照数据，建议检查设备 telemetry 上报程序和 MQTT 连接。"
    if not config:
        return (
            f"最新光照强度为 {latest['light_intensity']}，路灯状态为 {latest['lamp_status']}。"
            "当前没有查到阈值配置，建议先确认阈值配置是否已创建。"
        )
    if not config["enabled"]:
        return (
            f"最新光照强度为 {latest['light_intensity']}，但该设备阈值判断已关闭，"
            "系统暂不生成开关灯建议。"
        )

    light_intensity = latest["light_intensity"]
    if light_intensity < config["low_threshold"]:
        suggestion = "低于低阈值，系统建议开灯"
    elif light_intensity > config["high_threshold"]:
        suggestion = "高于高阈值，系统建议关灯"
    else:
        suggestion = "处于阈值区间内，建议保持当前状态"

    return (
        f"最新光照强度为 {light_intensity}，低阈值为 {config['low_threshold']}，"
        f"高阈值为 {config['high_threshold']}，{suggestion}。"
    )


def describe_device_alarms(context: dict[str, Any]) -> str:
    unhandled_count = context["unhandled_alarm_count"]
    alarms = context.get("alarm_logs", [])
    if unhandled_count == 0:
        return "当前没有未处理告警。"

    offline_alarm = next(
        (alarm for alarm in alarms if alarm["alarm_type"] == "offline" and not alarm["handled"]),
        None,
    )
    if offline_alarm:
        return (
            f"该设备有 {unhandled_count} 条未处理告警，其中包含离线告警。"
            "建议先检查供电、网络、设备网关和 MQTT status 心跳上报程序。"
        )
    return f"该设备有 {unhandled_count} 条未处理告警，建议先查看告警列表并确认告警原因。"


def describe_control_logs(context: dict[str, Any]) -> str:
    control_logs = context.get("control_logs", [])
    if not control_logs:
        return "最近没有查到人工控制记录。"

    latest_log = control_logs[0]
    return (
        f"最近一次人工控制命令为 {latest_log['command']}，执行结果记录为 {latest_log['result']}，"
        f"时间为 {latest_log['created_at']}。"
    )


def build_device_specific_answer(question: str, context: dict[str, Any]) -> str:
    device = context["device"]
    parts = [f"{device['device_code']} 当前状态为 {device['status']}。"]
    if device.get("last_heartbeat_at"):
        parts.append(f"最近一次心跳时间为 {device['last_heartbeat_at']}。")

    if contains_any_keyword(question, OFFLINE_KEYWORDS):
        parts.append(describe_device_alarms(context))
        if device["status"] == "offline":
            parts.append("该问题重点在离线排查，建议优先检查供电、网络、设备网关和 MQTT status 心跳上报程序。")
        else:
            parts.append("设备当前在线，若仍怀疑离线异常，建议重点检查心跳是否间歇性丢失。")
        return "".join(parts)

    if contains_any_keyword(question, THRESHOLD_KEYWORDS):
        parts.append(describe_light_with_threshold(context))
        parts.append("如果要继续验证阈值是否合理，建议结合历史光照曲线和现场环境时段做调整。")
        return "".join(parts)

    if contains_any_keyword(question, CONTROL_KEYWORDS):
        parts.append(describe_control_logs(context))
        parts.append("如果命令记录显示 success 但现场设备未响应，建议检查 MQTT command 订阅、设备端执行逻辑和 reply 回传。")
        return "".join(parts)

    if contains_any_keyword(question, ALARM_KEYWORDS):
        parts.append(describe_device_alarms(context))
        parts.append("建议先确认最新一条告警的类型、是否已处理，以及它与最近心跳和控制记录是否有关联。")
        return "".join(parts)

    parts.append(describe_light_with_threshold(context))
    parts.append(describe_device_alarms(context))
    parts.append(describe_control_logs(context))
    if device["status"] == "offline":
        parts.append("设备当前离线，建议优先排查供电、网络、设备网关和心跳程序。")
    else:
        parts.append("设备当前在线，建议结合光照趋势、阈值配置和最近控制记录继续判断。")
    return "".join(parts)


def build_system_specific_answer(question: str, context: dict[str, Any]) -> str:
    stats = context["device_stats"]
    unhandled = context["unhandled_alarm_count"]
    if stats["device_count"] == 0:
        return "当前系统还没有设备数据，无法判断运行情况。建议先创建设备并上报光照或心跳数据。"

    parts = [
        f"当前系统共有 {stats['device_count']} 台设备，在线 {stats['online_count']} 台，离线 {stats['offline_count']} 台，未处理告警 {unhandled} 条。"
    ]

    if contains_any_keyword(question, OFFLINE_KEYWORDS):
        if stats["offline_count"] > 0:
            parts.append("当前系统存在离线设备，建议先按设备列表筛出离线设备，再检查供电、网络、网关和 MQTT status 心跳上报。")
        else:
            parts.append("当前系统没有离线设备；如果要排查单台设备，建议在提问时指定设备编码。")
        return "".join(parts)

    if contains_any_keyword(question, ALARM_KEYWORDS):
        if unhandled > 0:
            parts.append("当前存在未处理告警，建议进入告警列表优先查看最近告警并按设备逐一确认原因。")
        else:
            parts.append("当前没有未处理告警；如果要分析单台设备的异常，建议指定设备编码继续提问。")
        return "".join(parts)

    if contains_any_keyword(question, CONTROL_KEYWORDS):
        if context.get("recent_control_logs"):
            latest_log = context["recent_control_logs"][0]
            parts.append(
                f"最近一条控制记录为 {latest_log['command']}，结果为 {latest_log['result']}。如需定位具体设备，请在问题中带上设备编码。"
            )
        else:
            parts.append("当前没有查到最近控制记录。")
        return "".join(parts)

    if contains_any_keyword(question, THRESHOLD_KEYWORDS):
        parts.append("阈值和光照建议更依赖单台设备的最新光照、阈值配置和历史趋势。建议指定设备编码后再提问。")
        return "".join(parts)

    if stats["offline_count"] > 0:
        parts.append("建议优先关注离线设备，检查供电、网络、网关和 MQTT 心跳上报。")
    if unhandled > 0:
        parts.append("建议进入告警列表查看未处理告警，并按设备逐一确认原因。")
    if context.get("recent_control_logs"):
        latest_log = context["recent_control_logs"][0]
        parts.append(
            f"最近一条控制记录为 {latest_log['command']}，结果为 {latest_log['result']}。"
        )
    else:
        parts.append("当前没有查到最近控制记录。")
    if stats["offline_count"] == 0 and unhandled == 0:
        parts.append("系统整体状态较稳定，建议继续观察 telemetry 和 status 上报是否持续正常。")
    return "".join(parts)


def build_mock_answer(question: str, context: dict[str, Any]) -> str:
    if context["scope"] == "device":
        return build_device_specific_answer(question, context)

    return build_system_specific_answer(question, context)


def build_fallback_answer(question: str, context: dict[str, Any], reason: str) -> str:
    return f"大模型暂不可用，已返回规则版分析。原因：{reason}。{build_mock_answer(question, context)}"


def build_user_prompt(question: str, context: dict[str, Any]) -> str:
    return (
        "用户问题：\n"
        f"{question}\n\n"
        "后端上下文 JSON：\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)}"
    )


def normalize_response_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        parts = [normalize_response_text(item) for item in value]
        return "\n".join(part for part in parts if part).strip()

    if isinstance(value, dict):
        for key in ("content", "text", "output_text", "value"):
            if key in value:
                normalized = normalize_response_text(value[key])
                if normalized:
                    return normalized

    return ""


def extract_answer_from_result(result: dict[str, Any]) -> str:
    error_info = result.get("error")
    if isinstance(error_info, dict):
        error_message = normalize_response_text(error_info.get("message"))
        error_code = normalize_response_text(error_info.get("code"))
        if error_code and error_message:
            raise RuntimeError(f"{error_code}: {error_message}")
        if error_message:
            raise RuntimeError(error_message)
        raise RuntimeError("LLM 返回错误响应")

    choices = result.get("choices")
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            if isinstance(message, dict):
                answer = normalize_response_text(message.get("content"))
                if answer:
                    return answer

            for key in ("content", "text", "output_text"):
                answer = normalize_response_text(first_choice.get(key))
                if answer:
                    return answer

    for key in ("output", "output_text", "content", "text"):
        answer = normalize_response_text(result.get(key))
        if answer:
            return answer

    raise RuntimeError("LLM 响应格式不符合预期")


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
    answer = extract_answer_from_result(result)
    if not str(answer).strip():
        raise RuntimeError("LLM 返回空回答")
    return str(answer).strip()


def generate_agent_answer(question: str, context: dict[str, Any]) -> tuple[str, str]:
    if is_small_talk_question(question):
        return build_small_talk_answer(), "mock"

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
