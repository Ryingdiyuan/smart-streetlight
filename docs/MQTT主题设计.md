# MQTT 主题设计

## 主题命名原则

MQTT 主题围绕单个设备展开，统一使用设备编码作为路径参数。主题保持简洁，便于 mock 设备和真实硬件复用。

```text
streetlight/{deviceId}/{messageType}
```

## Topic 列表

| Topic | 方向 | 说明 |
| --- | --- | --- |
| `streetlight/{deviceId}/telemetry` | 设备 -> 后端 | 上报光照、路灯状态、电压等遥测数据 |
| `streetlight/{deviceId}/status` | 设备 -> 后端 | 上报在线状态、心跳、最后执行状态 |
| `streetlight/{deviceId}/command` | 后端 -> 设备 | 下发开灯、关灯、亮度调节等控制指令 |
| `streetlight/{deviceId}/command/reply` | 设备 -> 后端 | 返回控制指令执行结果 |
| `streetlight/{deviceId}/alarm` | 设备 -> 后端 | 设备主动上报告警 |

## 遥测数据示例

Topic：

```text
streetlight/SL-001/telemetry
```

Payload：

```json
{
  "deviceId": "SL-001",
  "lightIntensity": 128,
  "lampStatus": "off",
  "voltage": 220.5,
  "timestamp": "2026-07-01 14:00:00"
}
```

## 状态心跳示例

Topic：

```text
streetlight/SL-001/status
```

Payload：

```json
{
  "deviceId": "SL-001",
  "online": true,
  "lampStatus": "off",
  "timestamp": "2026-07-01 14:00:10"
}
```

## 控制指令示例

Topic：

```text
streetlight/SL-001/command
```

Payload：

```json
{
  "commandId": "cmd-20260701140100-001",
  "deviceId": "SL-001",
  "command": "TURN_ON",
  "source": "manual",
  "timestamp": "2026-07-01 14:01:00"
}
```

## 指令回复示例

Topic：

```text
streetlight/SL-001/command/reply
```

Payload：

```json
{
  "commandId": "cmd-20260701140100-001",
  "deviceId": "SL-001",
  "result": "success",
  "message": "lamp turned on",
  "timestamp": "2026-07-01 14:01:02"
}
```

## 告警示例

Topic：

```text
streetlight/SL-001/alarm
```

Payload：

```json
{
  "deviceId": "SL-001",
  "alarmType": "light_abnormal",
  "alarmLevel": "warning",
  "content": "光照传感器读数异常",
  "timestamp": "2026-07-01 14:02:00"
}
```

## 后续约定

1. 后端订阅 `streetlight/+/telemetry`、`streetlight/+/status`、`streetlight/+/command/reply`、`streetlight/+/alarm`。
2. 后端下发指令只发布到 `streetlight/{deviceId}/command`。
3. 设备收到指令后必须通过 `command/reply` 返回结果，便于前端展示控制状态。
