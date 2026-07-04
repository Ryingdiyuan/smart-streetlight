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
- 智慧路灯运维问答 Agent
- 登录认证、JWT Token 和用户角色基础
- Swagger 接口文档和联调文档

智能体问答当前为 MVP：可以根据后端已有设备、光照、阈值、控制日志和告警数据生成运维建议；不会直接控制路灯、修改阈值或处理告警。

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

LLM_ENABLED=false
LLM_PROVIDER=openai-compatible
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=
LLM_TIMEOUT_SECONDS=30

JWT_SECRET_KEY=please-change-this-in-local-env
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120
```

真实大模型配置说明：

- `LLM_BASE_URL` 应填写到 OpenAI-compatible 服务的 `/v1` 层级，例如 `https://api.openai.com/v1`。
- 不要写成 `https://api.openai.com/v1/chat/completions`，因为代码会自动追加 `/chat/completions`。
- `LLM_API_KEY` 只能写在本地 `.env`，不要提交到 GitHub。
- `JWT_SECRET_KEY` 在本地 `.env` 中必须替换为自己的随机字符串，不要提交到 GitHub。

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

### 登录认证

- `POST /api/auth/init-admin`
- `POST /api/auth/login`
- `GET /api/auth/me`

说明：

- Day 13 新增认证基础能力。
- 当前未给旧业务接口强制加鉴权，避免破坏已有演示链路。
- 后续需要鉴权的请求使用 `Authorization: Bearer <access_token>`。

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

### 智能体问答

- `POST /api/agent/chat`

示例请求：

```json
{
  "question": "SL-001 最近为什么离线？",
  "device_code": "SL-001"
}
```

说明：

- `LLM_ENABLED=false` 时返回规则版回答，适合本地演示。
- `LLM_ENABLED=true` 时按 OpenAI-compatible chat completions 风格调用大模型。
- API Key 只能写在本地 `.env`，不要提交到 GitHub。
- 智能体只提供排查建议，不会直接执行开灯、关灯、修改阈值或处理告警。

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

### 智能体问答

本地 mock 模式：

```env
LLM_ENABLED=false
```

调用：

```text
POST /api/agent/chat
```

请求示例：

```json
{
  "question": "当前系统有哪些设备需要关注？"
}
```

更多测试问题见 [docs/智能体测试问题清单.md](docs/智能体测试问题清单.md)。

## 最终演示流程

推荐按 [docs/项目演示脚本.md](docs/项目演示脚本.md) 演示：

1. 启动 MySQL、Mosquitto 和 FastAPI。
2. 打开 Swagger `/docs` 和 MQTTX。
3. 创建设备并上报光照数据。
4. 通过 MQTTX 发布 telemetry 和 status。
5. 配置阈值并观察 `suggested_action`。
6. 调用手动控制接口，并在 MQTTX 查看 command。
7. 等待离线检测生成告警，查询并处理告警。
8. 调用 `POST /api/agent/chat` 展示智能体运维建议。

答辩讲解可参考 [docs/答辩说明.md](docs/答辩说明.md)。

## 文档目录

- [docs/后端技术选型.md](docs/后端技术选型.md)：后端技术栈选择说明。
- [docs/数据库设计.md](docs/数据库设计.md)：数据库表结构和字段说明。
- [docs/接口设计.md](docs/接口设计.md)：完整 HTTP 接口设计。
- [docs/权限设计.md](docs/权限设计.md)：登录认证、JWT 和角色权限设计。
- [docs/MQTT主题设计.md](docs/MQTT主题设计.md)：MQTT topic 和 payload 约定。
- [docs/前端联调接口清单.md](docs/前端联调接口清单.md)：给前端联调使用的接口清单。
- [docs/后端联调测试流程.md](docs/后端联调测试流程.md)：本地联调测试步骤。
- [docs/接口测试清单.md](docs/接口测试清单.md)：接口测试项清单。
- [docs/项目总结.md](docs/项目总结.md)：阶段性项目总结。
- [docs/简历项目描述.md](docs/简历项目描述.md)：简历和面试表达材料。
- [docs/智能体问答设计.md](docs/智能体问答设计.md)：智能体问答 MVP 设计说明。
- [docs/智能体测试问题清单.md](docs/智能体测试问题清单.md)：智能体典型问题和异常测试用例。
- [docs/项目演示脚本.md](docs/项目演示脚本.md)：最终项目演示流程。
- [docs/答辩说明.md](docs/答辩说明.md)：答辩讲解提纲。
## Day 14 权限接入说明

业务 HTTP 接口已经接入 JWT 权限控制。除公共接口和登录接口外，后续请求需要携带：

```text
Authorization: Bearer <access_token>
```

公共接口：

- `GET /`
- `GET /api/health`
- `POST /api/auth/init-admin`
- `POST /api/auth/login`

角色说明：

- `admin`：可以访问全部受保护业务接口。
- `operator`：可以查看数据、上报光照、修改阈值、下发控制、处理告警；不能管理设备基础信息。
- `viewer`：只能查看数据和使用智能体问答，不能执行写操作。

Swagger 测试时，先调用 `POST /api/auth/login` 获取 `access_token`，再点击右上角 `Authorize` 填入 token。`scripts/smoke_test_api.py` 现在会先登录，再携带 Token 测试受保护接口。

不要提交 `.env`、真实数据库密码、JWT Secret、API Key 或真实 Token。
