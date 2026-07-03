# MQTT 主题设计

## 当前阶段

Day 5 已接入 MQTT telemetry 数据：

- 后端在 `MQTT_ENABLED=true` 时连接 MQTT Broker。
- 后端订阅 `streetlight/+/telemetry`。
- 收到合法设备遥测数据后写入 MySQL 的 `light_data` 表。
- `MQTT_ENABLED=false` 时不启动 MQTT，不影响 HTTP 接口测试。

Day 6 已在 MQTT telemetry 写入 `light_data` 后接入自动判断逻辑：

- 光照低于低阈值：记录 `TURN_ON`
- 光照高于高阈值：记录 `TURN_OFF`
- 光照位于阈值之间：记录 `KEEP`
- 阈值配置未启用：记录 `DISABLED`

Day 6 只记录建议动作，不向 `streetlight/{deviceId}/command` 发布真实控制指令。

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
| `streetlight/{deviceId}/command` | 后端 -> 设备 | Day 7 再实现 | 下发开灯、关灯、亮度调节等控制指令 |
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

字段映射：

| MQTT 字段 | 数据库字段 | 说明 |
| --- | --- | --- |
| deviceId | devices.device_code | 用于查找设备 |
| lightIntensity | light_data.light_intensity | 光照强度 |
| lampStatus | light_data.lamp_status | 路灯状态；缺失时默认 `off` |
| voltage | light_data.voltage | 电压，可为空 |
| timestamp | light_data.reported_at | 上报时间；缺失或格式错误时使用当前时间 |

## 异常处理约定

1. payload 不是合法 JSON 时，只记录日志，不写入数据库。
2. payload 缺少 `deviceId` 时，只记录日志，不写入数据库。
3. `deviceId` 找不到对应设备时，只记录日志，不写入数据库。
4. payload 缺少 `lightIntensity` 时，只记录日志，不写入数据库。
5. payload 缺少 `lampStatus` 时，默认写入 `off`。
6. MQTT 消息处理异常会 rollback 并关闭数据库 Session，不影响 HTTP 接口。

## 测试示例

使用 `mosquitto_pub`：

```powershell
mosquitto_pub -h 127.0.0.1 -p 1883 -t streetlight/SL-001/telemetry -m "{\"deviceId\":\"SL-001\",\"lightIntensity\":120,\"lampStatus\":\"off\",\"voltage\":220.5,\"timestamp\":\"2026-07-03 10:00:00\"}"
```

如果没有 `mosquitto_pub`，可以使用 MQTTX 图形化客户端连接 `127.0.0.1:1883`，向 `streetlight/SL-001/telemetry` 发布同样的 JSON。
