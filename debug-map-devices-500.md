# [OPEN] map-devices-500

## 现象
- 软件前端大盘显示 0
- 地图页请求失败并显示 `{"detail":"Internal Server Error","status":500}`
- 后端日志显示 `/api/devices` 在序列化绑定传感器时抛出数据库字段不存在错误

## 假设
1. `sensors` 表缺少新模型所需字段，导致查询绑定传感器时报错
2. 只有绑定了 `sensor_id` 的路灯在序列化时会触发 500
3. 当前运行期 schema 兼容逻辑只补了 `devices`，没有补 `sensors`
4. 补齐 `sensors` 缺失字段后，`/api/devices` 会恢复，地图和大盘也会恢复

## 证据
- 后端运行日志：`Unknown column 'sensors.location' in 'field list'`
- `DESCRIBE sensors` 显示当前远端表仍是旧结构，仅含 `sensor_type` 等旧字段
- `backend/app/core/database.py` 当前只处理 `devices` 表的补字段

## 下一步
- 扩展 `ensure_schema_updates()`，为 `sensors` 表补齐兼容字段
- 执行一次 schema 更新并重启后端
- 重新验证 `/api/devices`、大盘和地图
