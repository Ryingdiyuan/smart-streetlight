# 数据库同步功能实现规划

## 目标

不同开发者本地运行项目时数据不一致（各自用独立本地 MySQL），通过后端启动时全量拉取云数据库 + 运行时增量轮询，实现本地与云端数据一致。

## 核心原则

- **云数据库**：权威主数据源，负责所有增删改
- **本地数据库**：只读缓存副本，项目代码只读本地库
- **同步方向**：单向 云 → 本地
- **删除策略**：云端软删除（`deleted_at`），本地同步删除

---

## 一、新增文件清单

### 1. `backend/app/core/cloud_database.py`
云数据库的 SQLAlchemy 引擎与会话工厂。与 `database.py` 结构相同，使用独立的 `CLOUD_MYSQL_*` 连接配置。

```python
# 大致结构
from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

cloud_engine = create_engine(settings.cloud_database_url, pool_pre_ping=True)
CloudSessionLocal = sessionmaker(bind=cloud_engine, autoflush=False, autocommit=False)

def get_cloud_db():
    db = CloudSessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 2. `backend/app/services/db_sync.py`
核心同步逻辑，包含两个函数：

**`full_sync_from_cloud()`** — 启动时全量拉取
- 按外键依赖顺序处理：devices → users → threshold_configs → light_data → control_logs → alarm_logs
- 对每张表：清空本地（DELETE）→ 从云库查询全部 → 批量 INSERT（每 500 行提交）
- 完成后写入 `sync_meta` 记录每张表的 `last_synced_at`（取 `SELECT NOW()` 云时间）

**`incremental_sync_from_cloud()`** — 运行时增量轮询
- 先查询云端 `SELECT NOW()` 作为本次同步基准时间（避免本地时间偏差）
- 对每张表执行三步：
  1. **拉取新增/修改**：`WHERE updated_at > last_synced_at` → `ON DUPLICATE KEY UPDATE`
  2. **同步删除**：`WHERE deleted_at > last_synced_at` → 本地 DELETE 对应 ID
  3. 更新 `sync_meta.last_synced_at = 云时间`
- 每 500 行批量提交一次

**SYNC_TABLES 定义：**
```python
SYNC_TABLES = {
    "devices":          {"model": Device,         "has_updated_at": True},
    "users":            {"model": User,           "has_updated_at": True},
    "threshold_configs": {"model": ThresholdConfig, "has_updated_at": True},
    "light_data":       {"model": LightData,      "has_updated_at": False},
    "control_logs":     {"model": ControlLog,     "has_updated_at": False},
    "alarm_logs":       {"model": AlarmLog,       "has_updated_at": False},
}
```

### 3. `backend/app/models/sync_meta.py`
新增模型 `SyncMeta`，表名 `db_sync_meta`：
- `id` — PK autoincrement
- `table_name` — VARCHAR(64) UNIQUE
- `last_synced_id` — INT DEFAULT 0
- `last_synced_at` — DATETIME nullable

---

## 二、修改文件清单

### 4. 所有 6 个业务模型加 `deleted_at` 字段

每个模型的表添加 `deleted_at` 字段（仅用于接收云端同步删除，本地业务代码无需关心）：

```python
deleted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
```

涉及文件：
- `backend/app/models/device.py`
- `backend/app/models/user.py`
- `backend/app/models/threshold_config.py`
- `backend/app/models/light_data.py`
- `backend/app/models/control_log.py`
- `backend/app/models/alarm_log.py`

### 5. `backend/.env`
添加云数据库配置（替换密码为实际值）：

```ini
CLOUD_DB_ENABLED=true
CLOUD_MYSQL_HOST=8.137.33.226
CLOUD_MYSQL_PORT=3306
CLOUD_MYSQL_USER=root
CLOUD_MYSQL_PASSWORD=xxx
CLOUD_MYSQL_DATABASE=smart_streetlight
DB_SYNC_INTERVAL_SECONDS=30
```

### 6. `backend/app/core/config.py`
在 `Settings` 类中添加：

```python
cloud_db_enabled: bool = False
cloud_mysql_host: str = "127.0.0.1"
cloud_mysql_port: int = 3306
cloud_mysql_user: str = "root"
cloud_mysql_password: str = Field(default="", repr=False)
cloud_mysql_database: str = "smart_streetlight"
db_sync_interval_seconds: int = 30

@property
def cloud_database_url(self) -> str:
    password = quote_plus(self.cloud_mysql_password)
    return (
        f"mysql+pymysql://{self.cloud_mysql_user}:{password}"
        f"@{self.cloud_mysql_host}:{self.cloud_mysql_port}/{self.cloud_mysql_database}"
        "?charset=utf8mb4"
    )
```

### 7. `backend/app/tasks/scheduler.py`
添加定时同步任务：

```python
from app.services.db_sync import incremental_sync_from_cloud
from app.core.config import settings

if settings.cloud_db_enabled:
    scheduler.add_job(
        incremental_sync_from_cloud,
        "interval",
        seconds=settings.db_sync_interval_seconds,
        id="db_sync",
        replace_existing=True,
    )
```

### 8. `backend/app/main.py`
调整 `lifespan` 启动顺序：

```python
# 启动阶段
init_db()

if settings.cloud_db_enabled:
    from app.services.db_sync import full_sync_from_cloud
    full_sync_from_cloud()       # 先全量同步

simulator_manager.start()
if settings.mqtt_enabled:
    mqtt_client.start()
if settings.scheduler_enabled:
    scheduler.start()            # 再启动调度器（含增量轮询）
```

### 9. `backend/app/core/database.py`
在 `init_db()` 的 import 中加入 `sync_meta`：

```python
def init_db() -> None:
    from app.models import (
        alarm_log, control_log, device, light_data,
        threshold_config, user, sync_meta,  # 新增 sync_meta
    )
    Base.metadata.create_all(bind=engine)
```

---

## 三、增量同步伪代码

```
def incremental_sync_from_cloud():
    cloud_now = query_cloud("SELECT NOW()")   # 用云端时间
    meta_rows = query_local_sync_meta()
    
    for table_name, info in SYNC_TABLES:
        last = meta_rows.get(table_name, {})
        
        if info.has_updated_at:
            # Step 1: Upsert modified/new
            rows = cloud.query(f"SELECT * FROM {table_name} WHERE updated_at > :last")
            for batch in chunks(rows, 500):
                local.execute(INSERT ... ON DUPLICATE KEY UPDATE ...)
            
            # Step 2: Sync deletes
            deleted_ids = cloud.query(
                f"SELECT id FROM {table_name} WHERE deleted_at > :last")
            if deleted_ids:
                local.execute(f"DELETE FROM {table_name} WHERE id IN :ids")
        else:
            # Append-only tables: insert new rows by ID
            rows = cloud.query(
                f"SELECT * FROM {table_name} WHERE id > :last_id")
            for batch in chunks(rows, 500):
                local.execute(INSERT IGNORE INTO ...)
        
        # Update sync_meta
        upsert_sync_meta(table_name, cloud_now)
```

---

## 四、启动时序

```
lifespan startup:
  1. init_db()               # 创建所有本地表（含 db_sync_meta）
  2. full_sync_from_cloud()  # 清空本地，拉云全量（同步阻塞）
  3. simulator_manager.start()
  4. mqtt_client.start()
  5. scheduler.start()       # 启动后，增量轮询才开始运行
```

---

## 五、边界处理

| 场景 | 处理方式 |
|------|---------|
| 云库不可达 | 捕获异常，打 warn 日志，不阻塞启动 |
| 网络超时 | 当前增量轮询周期跳过，下周期重试 |
| `CLOUD_DB_ENABLED=false` | 完全不执行同步代码 |
| 大表 | 每 500 行批量提交 |
| 本地时间偏差 | 用 `SELECT NOW()` 云时间作为同步基准 |
| 全量同步未完成 | 轮询任务在全量完成后才注册到 scheduler |

---

## 六、验证方式

1. 启动后端，观察日志 `[db_sync] Full sync completed`
2. 在云库修改某设备 status + updated_at，等待一个轮询周期，检查本地库是否更新
3. 在云库软删除一条记录（设置 deleted_at），检查本地是否同步删除
4. 在云库新增一条 light_data，检查本地是否追加
5. 关闭 `CLOUD_DB_ENABLED=false`，确认同步功能完全关闭，本地数据不受影响
