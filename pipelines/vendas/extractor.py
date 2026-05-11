"""Extrai NFs das 4 abas mensais do Excel."""

from __future__ import annotations
from pathlib import Path
from typing import Iterator

import pandas as pd

ABAS = [
    ("2026-01", "Notas Fiscais jan"),
    ("2026-02", "Notas Fiscais Fev"),
    ("2026-03", "Notas Fiscais Março"),
    ("2026-04", "Notas Fiscais Abril"),
]


def extrair(xlsx_path: Path) -> Iterator[dict]:
    for periodo, aba in ABAS:
        df = pd.read_excel(xlsx_path, sheet_name=aba)
        for row in df.to_dict(orient="records"):
            row["__periodo__"] = periodo
            row["__arquivo__"] = xlsx_path.name
            yield row
