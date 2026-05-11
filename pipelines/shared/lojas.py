"""Carrega o de-para de lojas e expõe helpers de lookup."""

from __future__ import annotations
from pathlib import Path
from typing import Optional

import yaml

from .utils import normalizar_str

_MAPPING_PATH = Path(__file__).parent / "lojas_mapping.yaml"
_cache: dict | None = None


def _load() -> dict:
    global _cache
    if _cache is None:
        with open(_MAPPING_PATH, encoding="utf-8") as f:
            _cache = yaml.safe_load(f) or {}
        # Pre-normaliza as chaves para lookup tolerante
        for ns in ("syonet", "nota_fiscal"):
            raw = _cache.get(ns) or {}
            normalized = {}
            for k, v in raw.items():
                key = normalizar_str(k)
                if key:
                    normalized[key] = v
            _cache[ns] = normalized
    return _cache


def lookup_syonet(empresa: str | None) -> Optional[str]:
    """Mapeia 'Empresa' do Syonet → loja_id. Retorna None se não mapeado."""
    if not empresa:
        return None
    key = normalizar_str(empresa)
    return _load().get("syonet", {}).get(key) if key else None


def lookup_nota_fiscal(nome_empresa: str | None) -> Optional[str]:
    """Mapeia 'Nome Empresa' da NF → loja_id."""
    if not nome_empresa:
        return None
    key = normalizar_str(nome_empresa)
    return _load().get("nota_fiscal", {}).get(key) if key else None
