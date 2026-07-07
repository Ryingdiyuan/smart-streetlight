# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**智慧路灯节能系统 (Smart Streetlight Energy-Saving System)** — A full-stack IoT application for managing smart streetlights. Backend handles device management, MQTT telemetry, threshold-based auto control, heartbeat/offline detection, alarms, and an AI Ops agent. Frontend is a Vue 3 admin console with role-based views and mock/API service switching.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.0 (declarative) |
| Database | MySQL via PyMySQL |
| MQTT | Paho-MQTT (Mosquitto / EMQX) |
| Scheduler | APScheduler |
| Auth | PyJWT + Passlib (bcrypt) |
| Frontend | Vue 3 (Composition API, `<script setup>`), Vue Router 4 |
| Build | Vite 8, TypeScript 6 |
| Charts | ECharts 6 + vue-echarts 8 |

## Common Commands

### Backend

```powershell
# Install dependencies
cd backend && python -m pip install -r requirements.txt

# Run dev server (hot reload)
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Smoke test (requires server running)
cd backend && python scripts/smoke_test_api.py

# Run MQTT device simulator
cd backend && python scripts/mock_mqtt_device.py
```

### Frontend

```powershell
# Install dependencies
cd frontend && npm install

# Dev server (hot reload at localhost:5173)
cd frontend && npm run dev

# Type-check and production build
cd frontend && npm run build

# Preview production build
cd frontend && npm run preview
```

### Database

```powershell
# Create database
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS smart_streetlight DEFAULT CHARSET utf8mb4;"
```

### Environment Variables

| File | Purpose |
|------|---------|
| `backend/.env` | Backend config (DB, MQTT, JWT, LLM, scheduler) |
| `frontend/.env` | Frontend config (VITE_SERVICE_MODE, VITE_API_BASE_URL, VITE_API_PROXY_TARGET) |

Key frontend env values:
- `VITE_SERVICE_MODE=mock` — runs with mock data, no backend needed
- `VITE_SERVICE_MODE=api` — connects to real backend
- `VITE_API_PROXY_TARGET=http://127.0.0.1:8000` — Vite proxies `/api` to this backend URL

## Architecture

### Backend (`backend/app/`)

```
app/
├── main.py              # FastAPI app, lifespan, CORS, router mount
├── core/
│   ├── config.py        # Pydantic Settings (reads .env)
│   ├── database.py      # SQLAlchemy engine, session, init_db()
│   └── security.py      # JWT create/decode, password hashing, role guards
├── models/              # SQLAlchemy ORM models
│   ├── device.py        # Device (id, device_code, device_name, location, status, last_heartbeat_at)
│   ├── light_data.py    # LightData (device_id, light_intensity, voltage, lamp_status, timestamp)
│   ├── threshold_config.py  # ThresholdConfig (device_id, low_threshold, high_threshold, enabled)
│   ├── control_log.py   # ControlLog (device_id, command, brightness, source, created_at)
│   ├── alarm_log.py     # AlarmLog (device_id, alarm_type, alarm_level, alarm_content, handled, created_at)
│   └── user.py          # User (username, password_hash, role, is_active)
├── schemas/             # Pydantic request/response models
├── routers/             # FastAPI routers (mounted under /api)
│   ├── __init__.py      # Aggregates all routers into api_router
│   ├── health.py        # GET /api/health
│   ├── auth.py          # POST /api/auth/login, POST /api/auth/init-admin, GET /api/auth/me
│   ├── devices.py       # CRUD /api/devices
│   ├── light_data.py    # POST /api/devices/{id}/light-data, GET latest/history
│   ├── thresholds.py    # GET/PUT /api/devices/{id}/threshold
│   ├── commands.py      # POST/GET /api/devices/{id}/commands
│   ├── alarms.py        # GET /api/alarms, PUT /api/alarms/{id}/handle
│   ├── users.py         # User management (admin only)
│   ├── agent.py         # POST /api/agent/chat (AI Ops agent)
│   └── simulator.py     # Simulator management endpoints
├── services/
│   ├── device_service.py    # Device DB queries
│   ├── auth_service.py      # Auth business logic
│   ├── auto_control.py      # Threshold → action logic (TURN_ON/TURN_OFF/KEEP/DISABLED)
│   ├── offline_check.py     # Heartbeat → offline detection → alarm creation
│   ├── agent_context.py     # Agent context builder
│   ├── llm_client.py        # OpenAI-compatible LLM client (disabled by default)
│   ├── simulator_service.py # In-process device simulator (threaded MQTT publisher)
│   └── offline_check.py     # Periodic offline device detection
├── mqtt/
│   ├── client.py        # MqttClient: connects, subscribes streetlight/+/telemetry and +/status
│   └── handlers.py      # handle_telemetry_message, handle_status_message (inserts data)
├── tasks/
│   └── scheduler.py     # APScheduler: every 60s checks device offline status
```

### Lifecycle (lifespan in `main.py`)

1. `init_db()` — creates tables via `Base.metadata.create_all`
2. `simulator_manager.start()` — starts the in-process device simulator thread
3. `mqtt_client.start()` — connects to MQTT broker (if `MQTT_ENABLED=true`)
4. `scheduler.start()` — starts APScheduler (if `SCHEDULER_ENABLED=true`)

### Frontend (`frontend/src/`)

```
src/
├── main.ts              # App bootstrap, initTheme()
├── App.vue              # Root: <RouterView />
├── style.css            # Global styles (~30KB, dark/light theme via [data-theme])
├── config/env.ts        # Runtime config (apiBaseUrl, serviceMode)
├── lib/http.ts          # fetch-based HTTP client with JWT Bearer headers
├── types/models.ts      # TypeScript interfaces
├── router/index.ts      # Vue Router with auth guards and role-based route access
├── layouts/AppShell.vue # Main layout: sidebar nav + topbar + <RouterView />
├── pages/               # Page components (Dashboard, DeviceList, DeviceDetail, etc.)
├── components/          # Reusable components (StatCard, PanelCard, StatusBadge, charts)
└── services/
    ├── serviceRuntime.ts    # Mock/API service switcher factory
    ├── authStorage.ts       # JWT token persistence in localStorage
    ├── themeStorage.ts      # Dark/light theme persistence
    ├── permissions.ts       # Role-based permission checks (admin/maintainer/user)
    ├── api/                 # Real API service implementations
    └── mock/                # Mock service implementations (return static data)
```

### Service Mode Pattern

The frontend uses a **service switcher** pattern via `createServiceSwitcher<T>(mockImpl, apiImpl)`:
- When `VITE_SERVICE_MODE=mock` — all API calls return local mock data (no backend needed)
- When `VITE_SERVICE_MODE=api` — calls go to the real backend via the fetch-based HTTP client

### Role-Based Access Control

Three roles with hierarchical permissions:

| Role | Capabilities |
|------|-------------|
| `admin` | Full access: all CRUD, simulator, user management, agent |
| `maintainer` | View data, operate devices, handle alarms, agent chat |
| `user` | View-only (dashboard, devices, agent chat) |

Roles are enforced on **both** sides:
- **Backend**: `security.py` provides `require_admin()`, `require_maintainer_or_admin()`, `require_user_or_above()` dependency guards per route
- **Frontend**: `router/index.ts` checks role in `beforeEach` guard; `AppShell.vue` filters nav items by `can(permission)`; route meta `roles` arrays define allowed roles

### Auto Control Logic

When light data is reported (via HTTP or MQTT), `evaluate_auto_control()` checks threshold config:
- `light < low_threshold` → `TURN_ON`
- `light > high_threshold` → `TURN_OFF`
- Otherwise → `KEEP`
- `enabled=false` → `DISABLED`

### Offline Detection

APScheduler runs every 60s: finds devices with `status=online` and `last_heartbeat_at` older than `DEVICE_OFFLINE_SECONDS` (default 180s), marks them offline, and creates an `offline` alarm.

### MQTT Topics

| Topic | Direction | Purpose |
|-------|-----------|---------|
| `streetlight/{device_code}/telemetry` | Device → Backend | Light intensity, voltage, lamp status |
| `streetlight/{device_code}/status` | Device → Backend | Online/lamp status heartbeat |
| `streetlight/{device_code}/command` | Backend → Device | TURN_ON/TURN_OFF/SET_BRIGHTNESS commands |

### Database Tables

| Table | Key Fields |
|-------|-----------|
| `devices` | id, device_code (unique), device_name, location, status, last_heartbeat_at |
| `light_data` | id, device_id (FK), light_intensity, voltage, lamp_status, timestamp |
| `threshold_config` | id, device_id (FK, unique), low_threshold, high_threshold, enabled |
| `control_log` | id, device_id (FK), command, brightness, source, created_at |
| `alarm_log` | id, device_id (FK), alarm_type, alarm_level, alarm_content, handled |
| `users` | id, username (unique), password_hash, role, is_active |

## Key Design Decisions

- **In-process simulator**: `SimulatorManager` runs a daemon thread that generates realistic sensor data (ambient light with variance, voltage fluctuation) and publishes via MQTT. It subscribes to command topics to respond to control messages.
- **Tables created on startup**: `Base.metadata.create_all()` runs on every startup — safe for dev but won't migrate schema changes. Manual ALTER needed for new columns.
- **Agent MVP**: The AI Ops agent (`POST /api/agent/chat`) runs in rule-based mode when `LLM_ENABLED=false` (default). When enabled, it calls an OpenAI-compatible API.
- **No migration framework**: Schema changes require manual SQL `ALTER TABLE` statements.
