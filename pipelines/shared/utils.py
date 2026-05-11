"""Utilitários compartilhados entre os pipelines."""

from __future__ import annotations
import re
import unicodedata
from datetime import datetime
from typing import Any


# ── Normalização de strings ──────────────────────────────────────────────────

_WS_RE = re.compile(r"\s+")

def normalizar_str(s: Any) -> str | None:
    """Strip + collapse de espaços múltiplos. None se vazio."""
    if s is None:
        return None
    s = str(s).strip()
    if not s or s.lower() in ("nan", "none", ""):
        return None
    return _WS_RE.sub(" ", s)


def normalizar_chassi(s: Any) -> str | None:
    """Chassi: UPPER + strip. None se vazio/inválido."""
    s = normalizar_str(s)
    if not s:
        return None
    s = s.upper().replace(" ", "")
    return s if len(s) == 17 else s  # mantém mesmo se incompleto (audit)


def normalizar_chave_lookup(s: Any) -> str | None:
    """Para comparação tolerante: strip + collapse espaços + sem acento ainda preserva."""
    s = normalizar_str(s)
    return s


# ── Conversões numéricas ─────────────────────────────────────────────────────

def parse_int(v: Any) -> int | None:
    """Converte para int. None se vazio/inválido."""
    if v is None or v == "":
        return None
    try:
        if isinstance(v, str):
            v = v.strip().replace(".", "").replace(",", ".")
            if not v or v.lower() == "nan":
                return None
        return int(float(v))
    except (ValueError, TypeError):
        return None


def parse_nps_score(v: Any) -> tuple[int | None, str | None]:
    """
    Tenta extrair nota NPS (0-10) da resposta.
    Retorna (nota_inteira, observacao_texto).
    Se for texto não-numérico, retorna (None, texto_original).
    """
    if v is None or v == "":
        return None, None
    if isinstance(v, float) and v != v:  # NaN
        return None, None
    if isinstance(v, (int, float)):
        n = int(v)
        return (n, None) if 0 <= n <= 10 else (None, str(v))

    s = str(v).strip()
    if not s or s.lower() == "nan":
        return None, None

    # Tenta extrair número direto
    s_clean = s.replace(",", ".")
    try:
        n = int(float(s_clean))
        if 0 <= n <= 10:
            return n, None
    except (ValueError, TypeError):
        pass

    # Pega o 1º número da string ("10 - excelente", "Nota 8")
    m = re.search(r"\b(\d{1,2})\b", s)
    if m:
        try:
            n = int(m.group(1))
            if 0 <= n <= 10:
                return n, s  # devolve a obs também para audit
        except ValueError:
            pass

    # Texto sem número
    return None, s


def parse_valor_brl(v: Any) -> float | None:
    """Parse de 'R$ 144.900,00' → 144900.00. Aceita também float direto."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v) if v == v else None  # filtra NaN
    s = str(v).strip()
    if not s or s.lower() == "nan":
        return None
    s = s.replace("R$", "").replace(" ", "").strip()
    if not s:
        return None
    # BR: ponto = milhar, vírgula = decimal
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_pct(v: Any) -> float | None:
    """Aceita '5%', '5,00%', 0.05, '0.05'. Retorna sempre fração (0.05)."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v) if v == v else None
    s = str(v).strip().replace("%", "").replace(",", ".").strip()
    if not s or s.lower() == "nan":
        return None
    try:
        n = float(s)
        return n / 100 if n > 1 else n  # 5 vira 0.05, 0.05 fica 0.05
    except ValueError:
        return None


# ── Datas ────────────────────────────────────────────────────────────────────

def parse_dt(v: Any) -> datetime | None:
    """Aceita Timestamp do pandas, datetime, ou string ISO/BR."""
    if v is None or v == "":
        return None
    if hasattr(v, "to_pydatetime"):
        try:
            return v.to_pydatetime()
        except Exception:
            return None
    if isinstance(v, datetime):
        return v
    s = str(v).strip()
    if not s or s.lower() == "nan":
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ── Classificação NPS ────────────────────────────────────────────────────────

def classificar_nps(nota: int | None) -> str:
    """Promotor / Neutro / Detrator a partir da nota NPS Geral."""
    if nota is None:
        return "Sem Resposta"
    if nota >= 9:
        return "Promotor"
    if nota >= 7:
        return "Neutro"
    return "Detrator"


# ── Escape SQL ───────────────────────────────────────────────────────────────

def sql_escape(v: Any) -> str:
    """Escapa valor para uso em SQL inline (INSERTs em batch)."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        if isinstance(v, float) and v != v:  # NaN
            return "NULL"
        return str(v)
    if isinstance(v, datetime):
        return f"'{v.isoformat()}'"
    s = str(v).replace("'", "''")
    return f"'{s}'"
