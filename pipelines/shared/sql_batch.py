"""Gera batches de INSERT SQL idempotentes (ON CONFLICT) a partir de listas de dicts."""

from __future__ import annotations
from datetime import datetime, date
from typing import Iterable


def _escape(v) -> str:
    """Escapa valor para SQL inline."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int,)):
        return str(v)
    if isinstance(v, float):
        if v != v:  # NaN
            return "NULL"
        return repr(v)
    if isinstance(v, (datetime, date)):
        return f"'{v.isoformat()}'"
    s = str(v).replace("\\", "\\\\").replace("'", "''")
    return f"'{s}'"


def gerar_upsert_sql(
    schema: str,
    table: str,
    rows: list[dict],
    columns: list[str],
    pk: str | tuple[str, ...],
    batch_size: int = 500,
) -> Iterable[str]:
    """Yields strings SQL com INSERT ... ON CONFLICT DO UPDATE."""
    if not rows:
        return

    pks = (pk,) if isinstance(pk, str) else tuple(pk)
    update_cols = [c for c in columns if c not in pks]
    update_set = ", ".join(f"{c}=EXCLUDED.{c}" for c in update_cols)
    cols_csv = ", ".join(columns)
    conflict_target = ", ".join(pks)

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        values_sql = ",\n  ".join(
            "(" + ", ".join(_escape(r.get(c)) for c in columns) + ")"
            for r in batch
        )
        sql = (
            f"INSERT INTO {schema}.{table} ({cols_csv})\nVALUES\n  {values_sql}\n"
            f"ON CONFLICT ({conflict_target}) DO UPDATE SET {update_set};"
        )
        yield sql
