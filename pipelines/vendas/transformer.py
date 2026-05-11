"""Transforma linhas cruas de NF em registros para raw.notas_fiscais."""

from __future__ import annotations
from typing import Any

from pipelines.shared import lojas
from pipelines.shared.utils import (
    normalizar_str,
    normalizar_chassi,
    parse_int,
    parse_valor_brl,
    parse_pct,
    parse_dt,
)


def transformar(row: dict[str, Any]) -> dict | None:
    """Normaliza uma linha de NF para o schema do banco. None se inválida."""
    nf_numero = normalizar_str(row.get("Nº NF"))
    if not nf_numero:
        return None

    nome_empresa_nf = normalizar_str(row.get("Nome Empresa"))
    loja_id = lojas.lookup_nota_fiscal(nome_empresa_nf)

    data_venda = parse_dt(row.get("Data"))
    if data_venda is None:
        return None  # data é obrigatória

    return {
        "nf_numero": nf_numero,
        "nome_empresa_nf": nome_empresa_nf,
        "empresa_codigo": parse_int(row.get("Empresa")),
        "loja_id": loja_id,

        "grupo_operacao": normalizar_str(row.get("Grupo Operação")),
        "data_venda": data_venda.date() if hasattr(data_venda, "date") else data_venda,
        "dias_em_estoque": parse_int(row.get("Dias Em Estoque")),
        "fluxo_operacao": normalizar_str(row.get("Fluxo Operação")),
        "fisico_juridico": normalizar_str(row.get("Fisico Juridico")),

        "cpf_cnpj": normalizar_str(row.get("CPF / CNPJ")),
        "nome_cliente": normalizar_str(row.get("Nome Cliente")),
        "genero": normalizar_str(row.get("Genero")),
        "bairro": normalizar_str(row.get("Bairro")),
        "cidade": normalizar_str(row.get("Cidade")),
        "uf": normalizar_str(row.get("UF")),

        "cpf_vendedor": normalizar_str(row.get("CPF Vendedor")),
        "vendedor": normalizar_str(row.get("Vendedor")),
        "chassi": normalizar_chassi(row.get("Chassi")),
        "placa": normalizar_str(row.get("Placa")),
        "modelo": normalizar_str(row.get("Modelo")),

        "volume": parse_int(row.get("Volume")),
        "volume_dev": parse_int(row.get("Dev.")),
        "faturamento":       parse_valor_brl(row.get("Faturamento")),
        "custo_compra":      parse_valor_brl(row.get("Custo Compra")),
        "vlr_bonus":         parse_valor_brl(row.get("Vlr. Bônus")),
        "lb_def":            parse_valor_brl(row.get("LB (Def)")),
        "pct_lb_def":        parse_pct(row.get("% LB (Def)")),
        "margem":            parse_valor_brl(row.get("Margem")),
        "pct_margem":        parse_pct(row.get("% Margem")),
        "vlr_icm":           parse_valor_brl(row.get("Vlr. ICM")),
        "vlr_pis_cofins":    parse_valor_brl(row.get("Vlr. PIS/COFINS")),
        "vlr_ipi":           parse_valor_brl(row.get("Vlr. IPI")),
        "val_impostos":      parse_valor_brl(row.get("Val. Impostos")),
        "vlr_modalidade":    parse_valor_brl(row.get("Vlr. Modalidade")),
        "vlr_preco_publico": parse_valor_brl(row.get("Vlr. Preço Público")),
        "vlr_desconto":      parse_valor_brl(row.get("Vlr. Desconto")),

        "arquivo_origem": row["__arquivo__"],
    }
