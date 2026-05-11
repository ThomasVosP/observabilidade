"""Extrai pesquisas das abas 'Pesquisas Novos' e 'Pesquisas seminovos'."""

from __future__ import annotations
from pathlib import Path
from typing import Iterator

import pandas as pd

ABAS = {
    "NOVOS":     "Pesquisas Novos",
    "SEMINOVOS": "Pesquisas seminovos",
}


def extrair(xlsx_path: Path) -> Iterator[dict]:
    """Itera sobre todas as pesquisas (Novos + Seminovos), preservando o tipo."""
    for tipo, aba in ABAS.items():
        df = pd.read_excel(xlsx_path, sheet_name=aba)
        for row in df.to_dict(orient="records"):
            row["__tipo__"] = tipo
            row["__arquivo__"] = xlsx_path.name
            yield row
