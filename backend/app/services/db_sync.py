"""Cloud-to-local database synchronization logic.

Provides:
  - full_sync_from_cloud()   — called at startup, truncates local tables and
                                pulls the full cloud dataset.
  - incremental_sync_from_cloud() — periodic delta sync (used by APScheduler).

Architecture:
  Cloud DB = authoritative source of truth (read-only from this module).
  Local DB = read-only cache for the application.
  Sync direction: one-way cloud → local.
"""

import logging
from datetime import datetime
from itertools import chain
from typing import Any

from sqlalchemy import Text, text
from sqlalchemy.orm import Session

from app.core.cloud_database import CloudSessionLocal
from app.core.database import SessionLocal, engine
from app.models.alarm_log import AlarmLog
from app.models.control_log import ControlLog
from app.models.device import Device
from app.models.light_data import LightData
from app.models.sync_meta import SyncMeta
from app.models.threshold_config import ThresholdConfig
from app.models.user import User

logger = logging.getLogger("app.services.db_sync")

# ---------------------------------------------------------------------------
# Sync table registry
# ---------------------------------------------------------------------------

SyncTableInfo = dict[str, Any]

SYNC_TABLES: list[SyncTableInfo] = [
    {
        "table_name": "devices",
        "model": Device,
        "has_updated_at": True,
        "id_field": "id",
    },
    {
        "table_name": "users",
        "model": User,
        "has_updated_at": True,
        "id_field": "id",
    },
    {
        "table_name": "threshold_configs",
        "model": ThresholdConfig,
        "has_updated_at": True,
        "id_field": "id",
    },
    {
        "table_name": "light_data",
        "model": LightData,
        "has_updated_at": False,
        "id_field": "id",
    },
    {
        "table_name": "control_logs",
        "model": ControlLog,
        "has_updated_at": False,
        "id_field": "id",
    },
    {
        "table_name": "alarm_logs",
        "model": AlarmLog,
        "has_updated_at": False,
        "id_field": "id",
    },
]

# Tables that have an `updated_at` column for delta queries.
_TABLES_WITH_UPDATED_AT = {t["table_name"] for t in SYNC_TABLES if t["has_updated_at"]}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BATCH_SIZE = 500


def _chunks(lst: list, size: int):
    """Yield successive *size*-sized chunks from *lst*."""
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def _columns_for_insert(model) -> list[str]:
    """Return column names (excluding PK `id` if autoincrement) for a model."""
    table = model.__table__
    pk_cols = {c.name for c in table.primary_key.columns}
    cols = [c.name for c in table.columns if c.name not in pk_cols]
    # always include PK so ON DUPLICATE KEY UPDATE works
    return [c.name for c in table.columns]


def _bulk_upsert(local: Session, model, rows: list[dict]):
    """Insert rows with ON DUPLICATE KEY UPDATE (MySQL dialect)."""
    if not rows:
        return
    table = model.__table__
    pk_cols = [c.name for c in table.primary_key.columns]
    non_pk_cols = [c.name for c in table.columns if c.name not in pk_cols]

    stmt = table.insert().values(rows)
    update_dict = {col: getattr(stmt.inserted, col) for col in non_pk_cols}
    stmt = stmt.on_duplicate_key_update(**update_dict)
    local.execute(stmt)
    local.commit()


def _bulk_insert_ignore(local: Session, model, rows: list[dict]):
    """INSERT IGNORE rows (append-only tables)."""
    if not rows:
        return
    table = model.__table__
    stmt = table.insert().prefix_with("IGNORE").values(rows)
    local.execute(stmt)
    local.commit()


def _get_cloud_now(cloud: Session) -> datetime:
    """Query cloud DB's current datetime."""
    result = cloud.execute(text("SELECT NOW()")).scalar()
    return result


def _load_sync_meta(local: Session) -> dict[str, SyncMeta]:
    """Return a dict of {table_name: SyncMeta} for all tracked tables."""
    rows = local.query(SyncMeta).all()
    return {r.table_name: r for r in rows}


def _upsert_sync_meta(local: Session, table_name: str, synced_at: datetime):
    """Insert or update the sync meta row for *table_name*."""
    row = local.query(SyncMeta).filter(SyncMeta.table_name == table_name).first()
    if row is None:
        row = SyncMeta(table_name=table_name, last_synced_at=synced_at)
        local.add(row)
    else:
        row.last_synced_at = synced_at
    local.commit()


def _upsert_sync_meta_id(
    local: Session, table_name: str, last_id: int, synced_at: datetime
):
    """Insert or update the sync meta row for append-only tables."""
    row = local.query(SyncMeta).filter(SyncMeta.table_name == table_name).first()
    if row is None:
        row = SyncMeta(
            table_name=table_name,
            last_synced_id=last_id,
            last_synced_at=synced_at,
        )
        local.add(row)
    else:
        row.last_synced_id = last_id
        row.last_synced_at = synced_at
    local.commit()


def _clean_local_table(local: Session, table_name: str):
    """Delete all rows from the local table (used during full sync)."""
    local.execute(text(f"DELETE FROM {table_name}"))
    local.commit()


def _rows_to_dicts(rows) -> list[dict]:
    """Convert SQLAlchemy row proxy objects to plain dicts."""
    return [dict(row._mapping) for row in rows]


# ---------------------------------------------------------------------------
# Full sync (startup)
# ---------------------------------------------------------------------------


def full_sync_from_cloud():
    """Full one-time sync: clear local tables and pull all cloud data.

    Must be called at application startup, before the scheduler starts
    incremental polling.
    """
    logger.info("[db_sync] === Starting full sync from cloud ===")
    cloud = CloudSessionLocal()
    local = SessionLocal()
    try:
        # Order respects foreign-key dependencies: parents before children.
        for info in SYNC_TABLES:
            table_name = info["table_name"]
            model = info["model"]
            logger.info("[db_sync]  Syncing table: %s", table_name)

            # Query all rows from cloud
            cloud_rows = cloud.execute(
                text(f"SELECT * FROM {table_name}")
            ).fetchall()
            dict_rows = _rows_to_dicts(cloud_rows)

            # Clear local table and bulk insert
            _clean_local_table(local, table_name)
            for batch in _chunks(dict_rows, BATCH_SIZE):
                _bulk_upsert(local, model, batch)

            # Record sync meta
            cloud_now = _get_cloud_now(cloud)
            last_id = max((r["id"] for r in dict_rows), default=0)
            _upsert_sync_meta_id(local, table_name, last_id, cloud_now)

            logger.info(
                "[db_sync]    %s: %d rows synced, last_id=%d",
                table_name,
                len(dict_rows),
                last_id,
            )

        logger.info("[db_sync] === Full sync completed ===")
    except Exception:
        logger.warning("[db_sync] Full sync failed (cloud unreachable?), skipping", exc_info=True)
    finally:
        cloud.close()
        local.close()


# ---------------------------------------------------------------------------
# Incremental sync (periodic)
# ---------------------------------------------------------------------------


def incremental_sync_from_cloud():
    """Periodic delta sync: pull changes since the last sync timestamp.

    Designed to be called from APScheduler every *DB_SYNC_INTERVAL_SECONDS*.
    """
    cloud = CloudSessionLocal()
    local = SessionLocal()
    try:
        cloud_now = _get_cloud_now(cloud)
        meta_rows = _load_sync_meta(local)

        for info in SYNC_TABLES:
            table_name = info["table_name"]
            model = info["model"]
            meta = meta_rows.get(table_name)

            if info["has_updated_at"]:
                _sync_with_updated_at(
                    cloud, local, table_name, model, meta, cloud_now
                )
            else:
                _sync_append_only(
                    cloud, local, table_name, model, meta, cloud_now
                )

        logger.debug("[db_sync] Incremental sync finished at %s", cloud_now)
    except Exception:
        logger.warning(
            "[db_sync] Incremental sync failed, will retry next cycle",
            exc_info=True,
        )
    finally:
        cloud.close()
        local.close()


def _sync_with_updated_at(
    cloud: Session,
    local: Session,
    table_name: str,
    model,
    meta: SyncMeta | None,
    cloud_now: datetime,
):
    """Sync tables that have an `updated_at` column (upsert + delete)."""
    last_at = meta.last_synced_at if meta else datetime(2000, 1, 1)

    # Step 1: Pull new/modified rows
    cloud_rows = cloud.execute(
        text(f"SELECT * FROM {table_name} WHERE updated_at > :last_at"),
        {"last_at": last_at},
    ).fetchall()
    dict_rows = _rows_to_dicts(cloud_rows)

    for batch in _chunks(dict_rows, BATCH_SIZE):
        _bulk_upsert(local, model, batch)

    # Step 2: Sync soft deletes
    deleted_ids = cloud.execute(
        text(
            f"SELECT id FROM {table_name} "
            "WHERE deleted_at IS NOT NULL AND deleted_at > :last_at"
        ),
        {"last_at": last_at},
    ).scalars().all()

    if deleted_ids:
        for batch in _chunks(deleted_ids, BATCH_SIZE):
            ids_tuple = tuple(batch)
            local.execute(
                text(f"DELETE FROM {table_name} WHERE id IN :ids"),
                {"ids": ids_tuple},
            )
        local.commit()

    if dict_rows or deleted_ids:
        logger.info(
            "[db_sync]  %s: %d upserted, %d deleted",
            table_name,
            len(dict_rows),
            len(deleted_ids),
        )

    _upsert_sync_meta(local, table_name, cloud_now)


def _sync_append_only(
    cloud: Session,
    local: Session,
    table_name: str,
    model,
    meta: SyncMeta | None,
    cloud_now: datetime,
):
    """Sync append-only tables (no updated_at) by ID range."""
    last_id = meta.last_synced_id if meta else 0

    cloud_rows = cloud.execute(
        text(f"SELECT * FROM {table_name} WHERE id > :last_id"),
        {"last_id": last_id},
    ).fetchall()
    dict_rows = _rows_to_dicts(cloud_rows)

    for batch in _chunks(dict_rows, BATCH_SIZE):
        _bulk_insert_ignore(local, model, batch)

    if dict_rows:
        new_last_id = max(r["id"] for r in dict_rows)
        logger.info(
            "[db_sync]  %s: %d new rows (last_id %d → %d)",
            table_name,
            len(dict_rows),
            last_id,
            new_last_id,
        )
        _upsert_sync_meta_id(local, table_name, new_last_id, cloud_now)
    else:
        _upsert_sync_meta(local, table_name, cloud_now)
