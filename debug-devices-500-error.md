# [OPEN] devices-500-error

## 症状
- 前端登录后访问 `/devices`
- 浏览器请求 `GET /api/devices`
- 后端返回 `500 Internal Server Error`

## 当前假设
1. `devices` 表缺少 `last_heartbeat_at`
2. 设备相关表结构未完全同步，缺的不止一个字段
3. 设备接口序列化或鉴权链路存在独立异常
4. 数据库现有数据触发了解析异常

## 当前证据
- `/api/auth/login` 正常
- `/api/alarms` 带 token 返回 `200 []`
- `/api/devices` 带 token 返回 `500`
- ORM 模型 `Device` 包含 `last_heartbeat_at`
- 本地 `devices` 表缺少 `last_heartbeat_at`
- 补列后 `/api/devices` 返回 `200`，并返回 3 条设备记录

## 下一步
- 请用户在浏览器中验证设备列表页是否正常
- 如确认修复，再决定是否清理本次调试记录
