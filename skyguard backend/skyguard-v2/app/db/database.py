"""SkyGuard V2 — Async SQLite Database Manager."""

import aiosqlite
import os
from contextlib import asynccontextmanager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

_db_path: str = "data/skyguard_v2.db"
_connection: aiosqlite.Connection | None = None


def is_db_open() -> bool:
    """False after close_db(); background loops should skip SQL while shutting down."""
    return _connection is not None


async def init_db(db_path: str = None) -> None:
    """Initialize the database: create tables from schema."""
    global _db_path, _connection
    if db_path:
        _db_path = db_path

    os.makedirs(os.path.dirname(_db_path), exist_ok=True)

    _connection = await aiosqlite.connect(_db_path)
    _connection.row_factory = aiosqlite.Row

    # Enable WAL mode for concurrent reads
    await _connection.execute("PRAGMA journal_mode=WAL")
    await _connection.execute("PRAGMA foreign_keys=ON")

    # Read and execute schema
    schema_path = os.path.join(os.path.dirname(__file__), "schemas.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        await _connection.executescript(schema_sql)
        await _connection.commit()
        logger.info(f"Database initialized: {_db_path}")
    else:
        logger.warning(f"Schema file not found: {schema_path}")


async def close_db() -> None:
    """Close the database connection."""
    global _connection
    if _connection:
        await _connection.close()
        _connection = None
        logger.info("Database connection closed")


@asynccontextmanager
async def get_db():
    """Get the database connection as an async context manager."""
    global _connection
    if _connection is None:
        await init_db()
    if _connection is None:
        raise RuntimeError("Database not available")
    try:
        yield _connection
    except Exception as e:
        if _connection is not None:
            logger.error(f"Database error: {e}")
        raise


async def execute(sql: str, params: tuple = ()) -> aiosqlite.Cursor | None:
    """Execute a SQL statement. Returns None if DB is closed (e.g. during shutdown)."""
    global _connection
    if _connection is None:
        return None
    try:
        cursor = await _connection.execute(sql, params)
        await _connection.commit()
        return cursor
    except Exception as e:
        err = str(e).lower()
        if "closed" in err or "disconnect" in err:
            return None
        logger.error(f"Database error: {e}")
        raise


async def fetch_one(sql: str, params: tuple = ()) -> dict | None:
    """Fetch a single row as a dict."""
    global _connection
    if _connection is None:
        return None
    try:
        cursor = await _connection.execute(sql, params)
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception as e:
        if "closed" in str(e).lower():
            return None
        logger.error(f"Database error: {e}")
        raise


async def fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    """Fetch all rows as a list of dicts."""
    global _connection
    if _connection is None:
        return []
    try:
        cursor = await _connection.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        if "closed" in str(e).lower():
            return []
        logger.error(f"Database error: {e}")
        raise
