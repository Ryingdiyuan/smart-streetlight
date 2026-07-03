# MQTT 主题设计

## 当前阶段

Day 5 已接入 MQTT telemetry 数据：

- 后端在 `MQTT_ENABLED=true` 时连接 MQTT Broker。
- 后端订阅 `streetlight/+/telemetry`。
- 收到合法设备遥测数据后写入 MySQL 的 `light_data` 表。
- `MQTT_ENABLED=false` 时不启动 MQTT，不影响 HTTP 接口测试。

Day 7 新增手动控制命令发布：

- `POST /api/devices/{device_id}/commands` 会记录 `control_logs`。
- `MQTT_ENABLED=true` 时，后端发布到 `streetlight/{deviceCode}/command`。
- `MQTT_ENABLED=false` 时，不发布 MQTT，控制日志结果为 `skipped`。
- Day 7 不处理设备 `command/reply`。

## 配置项

MQTT 配置通过 `backend/.env` 读取，不写死在业务代码中。

```env
MQTT_ENABLED=false
MQTT_HOST=127.0.0.1
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=smart-streetlight-backend
```

本地联调 MQTT 时，将 `MQTT_ENABLED` 改为 `true`，并确保本地 MQTT Broker 已启动。

## 主题命名

```text
streetlight/{deviceId}/{messageType}
```

`deviceId` 使用设备编码，对应 `devices.device_code`，例如 `SL-001`。

## Topic 列表

| Topic | 方向 | 当前状态 | 说明 |
| --- | --- | --- | --- |
| `streetlight/{deviceId}/telemetry` | 设备 -> 后端 | Day 5 已实现订阅 | 上报光照、路灯状态、电压等遥测数据 |
| `streetlight/{deviceId}/status` | 设备 -> 后端 | 后续实现 | 上报在线状态、心跳、最后执行状态 |
| `streetlight/{deviceId}/command` | 后端 -> 设备 | Day 7 已实现发布 | 下发开灯、关灯、亮度调节等控制指令 |
| `streetlight/{deviceId}/command/reply` | 设备 -> 后端 | 后续实现 | 返回控制指令执行结果 |
| `streetlight/{deviceId}/alarm` | 设备 -> 后端 | 后续实现 | 设备主动上报告警 |

## Telemetry 上报

Topic：

```text
streetlight/SL-001/telemetry
```

Payload：

```json
{
  "deviceId": "SL-001",
  "lightIntensity": 120,
  "lampStatus": "off",
  "voltage": 220.5,
  "timestamp": "2026-07-03 10:00:00"
}
```

## Command 下发

Topic：

```text
streetlight/SL-001/command
```

开灯 Payload：

```json
{
  "command": "TURN_ON",
  "source": "manual",
  "timestamp": "2026-07-03 10:00:00"
}
```

关灯 Payload：

```json
{
  "command": "TURN_OFF",
  "source": "manual",
  "timestamp": "2026-07-03 10:00:00"
}
```

设置亮度 Payload：

```json
{
  "command": "SET_BRIGHTNESS",
  "brightness": 80,
  "source": "manual",
  "timestamp": "2026-07-03 10:00:00"
}
```

## 异常处理约定

1. telemetry payload 不是合法 JSON 时，只记录日志，不写入数据库。
2. telemetry payload 缺少 `deviceId` 或 `lightIntensity` 时，只记录日志，不写入数据库。
3. `deviceId` 找不到对应设备时，只记录日志，不写入数据库。
4. MQTT command 发布异常时，HTTP 接口不崩溃，控制日志结果记为 `failed`。
5. `MQTT_ENABLED=false` 时不发布 command，控制日志结果记为 `skipped`。

## 测试建议

使用 MQTTX 订阅：

```text
streetlight/SL-001/command
```

然后在 `/docs` 调用：

```text
POST /api/devices/1/commands
```

如果 MQTT 正常启用，MQTTX 应能收到后端发布的控制命令。
