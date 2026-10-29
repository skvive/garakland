"""SQLite (local) or Neon Postgres (DATABASE_URL) for GARAKLAND."""
from __future__ import annotations

import os
import re
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("GARAK_DB_PATH", str(ROOT / "data" / "garakland.sqlite")))
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or ""

IGNORE_CONFLICT = {
    "stores": "(id)",
    "merchant_meta": "(shop_id)",
    "campaigns": "(id)",
    "visits": "(session_id, shop_id, day)",
    "v5_participants": "(shop_id)",
    "v5_outbox": "(broadcast_id, recipient)",
}

DB_LOCK = threading.Lock()


def backend_name() -> str:
    return "postgres" if DATABASE_URL else "sqlite"


def use_postgres() -> bool:
    return bool(DATABASE_URL)


def _adapt_sql(sql: str) -> str:
    if not use_postgres():
        return sql
    out = sql
    m = re.search(r"INSERT\s+OR\s+IGNORE\s+INTO\s+(\w+)", out, re.I)
    if m:
        table = m.group(1).lower()
        out = re.sub(r"INSERT\s+OR\s+IGNORE", "INSERT", out, flags=re.I)
        target = IGNORE_CONFLICT.get(table)
        if target and "ON CONFLICT" not in out.upper():
            out = out.rstrip().rstrip(";") + f" ON CONFLICT {target} DO NOTHING"
    out = out.replace("?", "%s")
    out = out.replace('AUTOINCREMENT', '')
    return out


from collections.abc import Mapping


class _PgRow(Mapping):
    __slots__ = ("_names", "_values")

    def __init__(self, names, values):
        self._names = names
        self._values = values

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._values[self._names.index(key)]

    def __iter__(self):
        return iter(self._names)

    def __len__(self):
        return len(self._names)


class _PgCursor:
    def __init__(self, cur, names):
        self._cur = cur
        self._names = names or []

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return _PgRow(self._names, row)

    def fetchall(self):
        return [_PgRow(self._names, r) for r in self._cur.fetchall()]


class _PgCompat:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        cur = self._conn.cursor()
        cur.execute(_adapt_sql(sql), params or ())
        names = [d[0] for d in (cur.description or [])]
        return _PgCursor(cur, names)

    def executescript(self, script: str):
        for stmt in filter(None, (s.strip() for s in script.split(";"))):
            if not stmt or stmt.startswith("--"):
                continue
            upper = stmt.upper()
            if upper.startswith("PRAGMA"):
                continue
            self.execute(stmt + ";")

    def commit(self):
        self._conn.commit()


class _SqliteCompat:
    def __init__(self, con):
        self._con = con

    def execute(self, sql, params=()):
        return self._con.execute(sql, params)

    def executescript(self, script: str):
        self._con.executescript(script)

    def commit(self):
        self._con.commit()


@contextmanager
def db_connect():
    if use_postgres():
        import ssl
        from urllib.parse import urlparse

        import pg8000.dbapi

        u = urlparse(DATABASE_URL)
        conn = pg8000.dbapi.connect(
            user=u.username,
            password=u.password,
            host=u.hostname,
            port=u.port or 5432,
            database=u.path.lstrip("/"),
            ssl_context=ssl.create_default_context(),
        )
        wrapper = _PgCompat(conn)
        try:
            yield wrapper
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(DB_PATH, timeout=30)
        con.row_factory = sqlite3.Row
        wrapper = _SqliteCompat(con)
        try:
            with con:
                yield wrapper
        finally:
            con.close()


def table_columns(db, table: str) -> set[str]:
    if use_postgres():
        cur = db.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s",
            (table.lower(),),
        )
        return {r[0] for r in cur.fetchall()}
    cur = db.execute(f"PRAGMA table_info({table})")
    return {r[1] for r in cur.fetchall()}
