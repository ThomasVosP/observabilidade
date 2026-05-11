"""Loader rápido usando psycopg2.extras.execute_values para upserts em batch."""

from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Iterable

import psycopg2
import psycopg2.extras


def _read_env() -> str:
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    return line.split("=", 1)[1]
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não encontrado (.env ou variável)")
    return url


def get_conn():
    return psycopg2.connect(_read_env())


def upsert(
    conn,
    schema: str,
    table: str,
    rows: list[dict],
    columns: list[str],
    pk: str | tuple[str, ...],
    page_size: int = 1000,
) -> int:
    """Upsert idempotente. Retorna nº de linhas afetadas."""
    if not rows:
        return 0

    pks = (pk,) if isinstance(pk, str) else tuple(pk)
    update_cols = [c for c in columns if c not in pks]
    cols_sql = ", ".join(columns)
    conflict_target = ", ".join(pks)

    if update_cols:
        set_sql = ", ".join(f"{c}=EXCLUDED.{c}" for c in update_cols)
        on_conflict = f"DO UPDATE SET {set_sql}"
    else:
        on_conflict = "DO NOTHING"

    sql = (
        f"INSERT INTO {schema}.{table} ({cols_sql}) VALUES %s "
        f"ON CONFLICT ({conflict_target}) {on_conflict}"
    )

    values = [tuple(r.get(c) for c in columns) for r in rows]

    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, values, page_size=page_size)
    conn.commit()
    return len(rows)


def truncate(conn, schema: str, table: str, cascade: bool = False) -> None:
    sql = f"TRUNCATE TABLE {schema}.{table}"
    if cascade:
        sql += " CASCADE"
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def count(conn, schema: str, table: str) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {schema}.{table}")
        return cur.fetchone()[0]
