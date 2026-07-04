function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, Math.round(value)));
}

function formatTimestamp(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  const second = String(date.getSeconds()).padStart(2, "0");
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

/**
 * MQTTX 自定义脚本。
 *
 * 输入示例：
 * {
 *   "messageType": "telemetry",
 *   "deviceId": "SL-001",
 *   "lampStatus": "off",
 *   "online": true,
 *   "baseLight": 120,
 *   "variance": 35,
 *   "voltageBase": 220.5,
 *   "brightness": 0
 * }
 *
 * messageType:
 * - telemetry: 生成 light_data 上报内容
 * - status: 生成设备心跳内容
 */
function handlePayload(value, msgType, index) {
  const deviceId = value.deviceId || "SL-001";
  const messageType = String(value.messageType || "telemetry").toLowerCase();
  const lampStatus = String(value.lampStatus || "off").toLowerCase();
  const online = value.online !== false;
  const baseLight = Number(value.baseLight ?? 120);
  const variance = Number(value.variance ?? 35);
  const voltageBase = Number(value.voltageBase ?? 220.5);
  const brightness = Number(value.brightness ?? 0);
  const now = formatTimestamp(new Date());

  if (messageType === "status") {
    return {
      deviceId,
      online,
      lampStatus,
      timestamp: now,
    };
  }

  const ambient = baseLight + (Math.random() * 2 - 1) * variance;
  const lampBoost = lampStatus === "on" ? Math.max(30, brightness * 1.6) : 0;
  const lightIntensity = clamp(ambient + lampBoost, 0, 1000);
  const voltage = Number((voltageBase + (Math.random() * 2 - 1) * 1.2).toFixed(1));

  return {
    deviceId,
    lightIntensity,
    lampStatus,
    voltage,
    timestamp: now,
  };
}

execute(handlePayload);
