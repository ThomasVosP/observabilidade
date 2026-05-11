"""Transforma linhas cruas das pesquisas em registros normalizados para o Supabase."""

from __future__ import annotations
from pathlib import Path
from typing import Any

import yaml

from pipelines.shared import lojas
from pipelines.shared.utils import (
    normalizar_str,
    normalizar_chassi,
    parse_int,
    parse_nps_score,
    parse_dt,
    classificar_nps,
)

_CONFIG_PATH = Path(__file__).parent / "config" / "perguntas_por_marca.yaml"
_cfg_cache: dict | None = None


def _carregar_config() -> dict:
    global _cfg_cache
    if _cfg_cache is None:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            _cfg_cache = yaml.safe_load(f) or {}
    return _cfg_cache


def _mapping_perguntas(marca: str | None) -> dict[int, str]:
    """Retorna o mapping 'ordem da pergunta → conceito' para a marca."""
    cfg = _carregar_config()
    if marca and marca in cfg:
        return cfg[marca]
    return cfg.get("default", {1: "nps_geral"})


def transformar(row: dict[str, Any]) -> tuple[dict, list[dict]]:
    """
    Recebe linha crua. Devolve (pesquisa_normalizada, lista_de_respostas_raw).
    """
    tipo = row["__tipo__"]
    arquivo = row["__arquivo__"]

    marca = normalizar_str(row.get("Marca"))
    empresa_syonet = normalizar_str(row.get("Empresa"))
    loja_id = lojas.lookup_syonet(empresa_syonet)

    evento = parse_int(row.get("Evento"))
    if evento is None:
        return None, []  # linha sem ID válido — descartar

    reclamacao_evento = parse_int(row.get("Reclamacao Evento"))
    if reclamacao_evento == 0:
        reclamacao_evento = None

    # ── Extrair conceitos NPS a partir das Perguntas ────────────────────────
    mapping = _mapping_perguntas(marca)
    conceitos: dict[str, Any] = {
        "nps_geral": None,
        "nps_processo_compra": None,
        "nps_test_drive": None,
        "nps_acessorios": None,
        "nps_acessorios_obs": None,
        "nps_entrega": None,
        "resposta_aberta": None,
    }

    respostas_raw = []
    for ordem in range(1, 16):
        pergunta = row.get(f"Pergunta {ordem}")
        resposta = row.get(f"Resposta {ordem}")
        motivo   = row.get(f"Motivo {ordem}")

        if not normalizar_str(pergunta) and not normalizar_str(resposta):
            continue

        # Salva no raw sempre que houver algo
        respostas_raw.append({
            "ordem": ordem,
            "pergunta": normalizar_str(pergunta),
            "resposta": normalizar_str(resposta),
            "motivo":   normalizar_str(motivo),
        })

        # Aplica mapping em conceitos canônicos
        conceito = mapping.get(ordem)
        if conceito == "resposta_aberta":
            conceitos["resposta_aberta"] = normalizar_str(resposta)
        elif conceito == "nps_acessorios":
            nota, obs = parse_nps_score(resposta)
            conceitos["nps_acessorios"] = nota
            conceitos["nps_acessorios_obs"] = obs
        elif conceito and conceito.startswith("nps_"):
            nota, _ = parse_nps_score(resposta)
            conceitos[conceito] = nota

    # Demais Perguntas / Demais Respostas / Demais Motivos → ordem=99
    demais_p = normalizar_str(row.get("Demais Perguntas"))
    demais_r = normalizar_str(row.get("Demais Respostas"))
    demais_m = normalizar_str(row.get("Demais Motivos"))
    if demais_p or demais_r:
        respostas_raw.append({
            "ordem": 99,
            "pergunta": demais_p,
            "resposta": demais_r,
            "motivo":   demais_m,
        })

    classificacao = classificar_nps(conceitos["nps_geral"])

    pesquisa = {
        "evento": evento,
        "tipo": tipo,
        "marca": marca,
        "empresa_syonet": empresa_syonet,
        "loja_id": loja_id,
        "status": normalizar_str(row.get("Status da Pesquisa")),
        "origem": normalizar_str(row.get("Origem")),
        "cliente": normalizar_str(row.get("Cliente")),
        "email": normalizar_str(row.get("E-mail")),
        "telefone": normalizar_str(row.get("Tel. Celular")),
        "chassi": normalizar_chassi(row.get("Chassi")),
        "modelo": normalizar_str(row.get("Modelo")),
        "placa": normalizar_str(row.get("Placa")),
        "vendedor": normalizar_str(row.get("Vendedor / Consultor")),
        "operador": normalizar_str(row.get("Operador")),
        "data_inclusao": parse_dt(row.get("Data Inclusão")),
        "data_conclusao": parse_dt(row.get("Data Conclusão")),
        "dias_conclusao": parse_int(row.get("Dias Conclusão Sucesso"))
            or parse_int(row.get("Dias Conclusão Insucesso")),
        "reclamacao_evento": reclamacao_evento,
        "nps_geral":           conceitos["nps_geral"],
        "nps_processo_compra": conceitos["nps_processo_compra"],
        "nps_test_drive":      conceitos["nps_test_drive"],
        "nps_acessorios":      conceitos["nps_acessorios"],
        "nps_acessorios_obs":  conceitos["nps_acessorios_obs"],
        "nps_entrega":         conceitos["nps_entrega"],
        "resposta_aberta":     conceitos["resposta_aberta"],
        "classificacao":       classificacao,
        "arquivo_origem":      arquivo,
    }

    return pesquisa, respostas_raw
