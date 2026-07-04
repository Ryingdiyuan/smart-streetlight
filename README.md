# 智慧路灯节能系统

本仓库用于重庆交通大学-中软国际企业实训项目，选题为“智慧路灯节能系统”。

项目目标是完成一个端-智-云一体化应用：校内阶段先通过模拟设备和 MQTT 打通数据链路，后端负责设备管理、数据采集、阈值判断、控制命令、心跳离线检测和告警管理；基地阶段再接入鸿蒙开发板、光照传感器和路灯控制外设。

## 项目简介

当前后端是基于 FastAPI + MySQL + MQTT 的智慧路灯服务，已支持：

- 设备管理
- 光照数据 HTTP 上报和查询
- MQTT telemetry 遥测数据入库
- 阈值配置和自动判断建议
- 手动控制命令发布
- 设备心跳和离线告警
- Swagger 接口文档和联调文档

智能体问答计划在后续阶段接入，当前版本未实现。

## 技术栈

- Python 3.10+
- FastAPI
- MySQL
- SQLAlchemy
- Paho-MQTT
- APScheduler
- pydantic-settings / python-dotenv
- Mosquitto / MQTTX

## 后端目录

```text
backend/
  app/
    core/       # 配置、数据库连接
    models/     # SQLAlchemy ORM 模型
    schemas/    # Pydantic 请求和响应模型
    routers/    # FastAPI 路由
    services/   # 业务服务
    mqtt/       # MQTT 客户端和消息处理
    tasks/      # APScheduler 定时任务
  scripts/      # 本地测试脚本
```

## 本地启动

### 1. 创建虚拟环境

```powershell
cd D:\code\smart-streetlight\backend
python -m venv .venv
```

如果 PowerShell 禁止激活脚本，可以直接使用 `.venv\Scripts\python.exe` 和 `.venv\Scripts\uvicorn.exe`，不强制激活虚拟环境。

### 2. 安装依赖

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. 配置 .env

在 `backend/` 下创建 `.env`，不要把真实密码提交到仓库。

```env
APP_NAME=智慧路灯节能系统后端
APP_VERSION=0.1.0
DEBUG=true
API_PREFIX=/api

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASSWORD=你的数据库密码
MYSQL_DATABASE=smart_streetlight

MQTT_ENABLED=false
MQTT_HOST=127.0.0.1
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=smart-streetlight-backend

SCHEDULER_ENABLED=true
DEVICE_OFFLINE_SECONDS=180
```

### 4. 创建数据库

```sql
CREATE DATABASE IF NOT EXISTS smart_streetlight
DEFAULT CHARSET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

当前开发阶段使用 `Base.metadata.create_all(bind=engine)` 创建不存在的表。注意：`create_all` 不会自动修改已有表字段。

如果本地已经存在旧版 `devices` 表，需要手动补充 Day 8 新增字段：

```sql
ALTER TABLE devices ADD COLUMN last_heartbeat_at DATETIME NULL;
```

### 5. 启动 Mosquitto

如果只测试 HTTP 接口，可以保持：

```env
MQTT_ENABLED=false
```

如果要测试 MQTT，请先启动本地 Mosquitto Broker：

```text
Host: 127.0.0.1
Port: 1883
```

### 6. 启动 FastAPI

```powershell
cd D:\code\smart-streetlight\backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

访问：

```text
http://127.0.0.1:8000/docs
```

## 常用接口

详细请求体、响应体和错误码见 [docs/接口设计.md](docs/接口设计.md)。

### 通用接口

- `GET /`
- `GET /api/health`

### 设备管理

- `GET /api/devices`
- `GET /api/devices/{id}`
- `POST /api/devices`
- `PUT /api/devices/{id}`
- `DELETE /api/devices/{id}`

### 光照数据

- `POST /api/devices/{device_id}/light-data`
- `GET /api/devices/{device_id}/latest-light`
- `GET /api/devices/{device_id}/light-history`

### 阈值配置

- `GET /api/devices/{device_id}/threshold`
- `PUT /api/devices/{device_id}/threshold`

### 控制命令

- `POST /api/devices/{device_id}/commands`
- `GET /api/devices/{device_id}/commands`

### 告警管理

- `GET /api/alarms`
- `GET /api/alarms/{alarm_id}`
- `PUT /api/alarms/{alarm_id}/handle`

## 测试方式

### Swagger

```text
http://127.0.0.1:8000/docs
```

### 冒烟测试脚本

启动后端后执行：

```powershell
cd D:\code\smart-streetlight\backend
.\.venv\Scripts\python.exe scripts\smoke_test_api.py
```

如果后端地址不是默认值，可以设置：

```powershell
$env:BACKEND_BASE_URL="http://127.0.0.1:8000"
.\.venv\Scripts\python.exe scripts\smoke_test_api.py
```

### MQTTX

可用 MQTTX 测试：

- `streetlight/SL-001/telemetry`
- `streetlight/SL-001/status`
- `streetlight/SL-001/command`

## 文档目录

- [docs/后端技术选型.md](docs/后端技术选型.md)：后端技术栈选择说明。
- [docs/数据库设计.md](docs/数据库设计.md)：数据库表结构和字段说明。
- [docs/接口设计.md](docs/接口设计.md)：完整 HTTP 接口设计。
- [docs/MQTT主题设计.md](docs/MQTT主题设计.md)：MQTT topic 和 payload 约定。
- [docs/前端联调接口清单.md](docs/前端联调接口清单.md)：给前端联调使用的接口清单。
- [docs/后端联调测试流程.md](docs/后端联调测试流程.md)：本地联调测试步骤。
- [docs/接口测试清单.md](docs/接口测试清单.md)：接口测试项清单。
- [docs/项目总结.md](docs/项目总结.md)：阶段性项目总结。
- [docs/简历项目描述.md](docs/简历项目描述.md)：简历和面试表达材料。
