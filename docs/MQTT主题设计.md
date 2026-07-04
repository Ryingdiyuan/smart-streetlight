# MQTT 主题设计

## 当前阶段

当前后端已经支持：

1. 订阅 telemetry 主题，将光照数据写入 `light_data`。
2. 发布 command 主题，用于手动控制设备。
3. 订阅 status 主题，用于设备心跳和在线状态更新。

`MQTT_ENABLED=false` 时，后端不会连接 MQTT Broker，不影响 HTTP 接口测试。

## 配置项

MQTT 配置通过 `backend/.env` 读取：

```env
MQTT_ENABLED=false
MQTT_HOST=127.0.0.1
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=smart-streetlight-backend
```

设备离线检测配置：

```env
SCHEDULER_ENABLED=true
DEVICE_OFFLINE_SECONDS=180
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
| `streetlight/{deviceId}/telemetry` | 设备 -> 后端 | 已实现订阅 | 上报光照、路灯状态、电压等遥测数据 |
| `streetlight/{deviceId}/status` | 设备 -> 后端 | 已实现订阅 | 上报在线状态和心跳 |
| `streetlight/{deviceId}/command` | 后端 -> 设备 | 已实现发布 | 下发开灯、关灯、亮度调节等控制命令 |
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

处理规则：

1. `deviceId` 对应 `devices.device_code`。
2. 找不到设备时只记录日志，不写入数据库。
3. 写入 `light_data` 后执行自动判断逻辑。

## Status 心跳

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
  "timestamp": "2026-07-03 10:00:00"
}
```

处理规则：

1. `deviceId` 对应 `devices.device_code`。
2. `online=true` 时，后端将 `devices.status` 更新为 `online`。
3. `online=false` 时，后端将 `devices.status` 更新为 `offline`。
4. `timestamp` 写入 `devices.last_heartbeat_at`。
5. 如果缺少 `timestamp`，后端使用当前时间。

## 离线检测

后端使用 APScheduler 定时执行离线检测：

1. 只检查 `status=online` 且有 `last_heartbeat_at` 的设备。
2. 如果当前时间与最后心跳时间的间隔超过 `DEVICE_OFFLINE_SECONDS`，则设备改为 `offline`。
3. 同时写入 `alarm_logs` 离线告警。
4. 如果该设备已经存在未处理的 `offline` 告警，不重复创建。

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

1. MQTT payload 不是合法 JSON 时，只记录日志，不写入数据库。
2. payload 缺少 `deviceId` 时，只记录日志，不写入数据库。
3. `deviceId` 找不到对应设备时，只记录日志，不写入数据库。
4. MQTT command 发布异常时，HTTP 接口不崩溃，控制日志结果记为 `failed`。
5. `MQTT_ENABLED=false` 时不发布 command，控制日志结果记为 `skipped`。
