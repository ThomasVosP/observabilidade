# Projeto: Observabilidade do Grupo Servopa

## Contexto

Sistema de observabilidade de negócio para todas as concessionárias do **Grupo Servopa** — conglomerado automotivo com mais de 70 anos de atuação no Sul do Brasil, operando **48 lojas em 11 marcas** (BYD, VW, Audi, Volvo, Hyundai, Honda, Peugeot, Citroën, GAC, Triumph, Harley-Davidson).

O objetivo é entregar um painel unificado que cruze pesquisas de satisfação (NPS), reclamações, vendas (notas fiscais) e operação por vendedor, com visão por loja e consolidada do grupo.

> ⚠️ **Importante:** este projeto é **multi-marca desde o início**. O CLAUDE.md anterior referenciava apenas BYD; a realidade é que todas as 11 marcas estão num único pipeline.

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Fonte primária (atual) | Excel exportado do **Syonet CRM** (1 arquivo, múltiplas abas) |
| Fonte primária (futura) | API Syonet REST |
| Fonte de vendas | **Notas Fiscais** do sistema interno (mensal, formato Excel) |
| Processamento | Python 3 + `pandas` + `openpyxl` |
| Banco de dados | **Supabase** (PostgreSQL gerenciado) |
| Dashboard | HTML estático gerado por script Python (Chart.js inline) |
| Repositório | https://github.com/ThomasVosP/observabilidade |

---

## Escopo de Marcas e Lojas

**11 marcas no Syonet** (valores exatos do campo `Marca`):
`AUDI`, `BYD`, `CITROEN`, `GAC`, `HARLEY-DAVIDSON`, `HMB - Hyundai`, `HONDA`, `PEUGEOT`, `TRIUMPH`, `VOLVO`, `VW - VOLKSWAGEN`, `VWC` (Caminhões VW)

> Observação: `CITROEN` e `PEUGEOT` aparecem como marcas separadas no Syonet, mas operacionalmente compartilham a bandeira **Lyon** (antes Dijon). No dashboard são agrupadas como `PEUGEOT-CITROEN`.

**48 lojas** distribuídas em 4 estados (PR 67%, RS 21%, SP 2%, CE 2%) — lista completa em `data/Lojas_Grupo_Servopa.md`.

**Bandeiras operadoras** (nomes comerciais diferentes da marca):
- Honda → **Prixx**
- Volvo → **Vecodil**
- Triumph → **Mavesul**
- Harley → **Freedom** (The One, Red Wheel)
- Peugeot/Citroën → **Lyon** (Ipiranga, Edu Chaves, Ceará)
- Hyundai → **Sevec** (PR) / **Carway** (RS)
- Audi → **Plaza** (Alto XV, Maringá)
- BYD/VW → **Servopa**

---

## Fontes de Dados — Arquivo `Dados Jan-Abril 2026.xlsx`

Um único Excel com **11 abas**, exportado do Syonet + sistema interno. Volumes referentes ao período 02/01/2026 a 30/04/2026 (4 meses).

### 1. Pesquisas Novos — 3.998 registros
Pesquisas NPS para vendas de carros 0km. 80 colunas. PK: `Evento`.

### 2. Pesquisas Seminovos — 1.474 registros
Mesmo schema da aba "Novos", mas para seminovos.

### 3. Reclamações — 1.275 registros
Reclamações abertas a partir de pesquisas com NPS baixo, ou por canais diretos (WhatsApp, e-mail, Reclame Aqui, etc.). 27 colunas.

### 4. Motivos Reclamação — 1.795 registros (1:N com Reclamações)
Cada reclamação pode ter **vários motivos** (uma linha por motivo). 18 colunas.

### 5. Notas Fiscais (4 abas mensais) — 13.279 NFs no total
- **Notas Fiscais jan**: 3.085
- **Notas Fiscais Fev**: 2.967
- **Notas Fiscais Março**: 3.947
- **Notas Fiscais Abril**: 3.280

37 colunas. Inclui Faturamento, Custo, Margem, Vendedor, Chassi, Modelo, Cliente, Cidade/UF.

### 6. DePara Vendedores SemiNovos — 93 vendedores
Tabela de mapeamento para resolver problema crítico: **vendedores de seminovos podem operar em loja diferente da loja-origem do estoque**. Mapeia `Vendedor → CENTRO DE CUSTO → LOJAS ALOCADO`.

### 7. CENTRO DE CUSTO — 90 vendedores
Mapeamento de vendedores de **NOVOS** → loja (centro de custo). Vendedor de novos trabalha em uma única loja.

---

## Schema das Pesquisas (Novos / Seminovos)

**80 colunas idênticas** entre as duas abas. Resumo dos campos críticos:

### Identificação
| Campo | Tipo | Obs |
|---|---|---|
| `Evento` | INT | **PK** — ID único Syonet |
| `Cliente` | TEXT | Nome completo |
| `Tel. Celular`, `Tel. Comercial`, `Tel. Residencial` | TEXT | 3 campos separados |
| `Telefones Adicionais`, `E-mail` | TEXT | |

### Classificação
| Campo | Valores possíveis |
|---|---|
| `Marca` | 10 marcas (sem TRIUMPH e GAC — esses aparecem só em reclamações) |
| `Empresa` | 38 strings de loja Syonet (formato verbose) |
| `Grupo Evento` | sempre `PESQUISA VEICULOS` |
| `Tipo Evento` | `NOVOS` ou `SEMINOVOS` |
| `Status da Pesquisa` | `CONCLUIDO`, `ANDAMENTO`, `PENDENTE` |
| `Origem` | `PESQUISA SATISFACAO`, `LOJA`, `INTERNET` |

### Veículo
`Chassi` (FK para NF) · `Placa` · `Modelo`

### Datas e Operação
`Data Inclusão` · `Data Conclusão` · `Operador` · `Vendedor / Consultor` · `Dias Conclusão Sucesso` · `Dias Conclusão Insucesso` · `Tempo Conclusão`

### Reclamação Vinculada (1:1 opcional)
`Reclamacao Evento` (FK; **valor `0` significa sem reclamação — não é FK válida**) · `Observacao reclamacao` · `Data Inclusão da reclamacao` · `Status da reclamacao vinculada`

### Pesquisa (estrutura Q&A)
`Pergunta 1` … `Pergunta 15` + `Demais Perguntas`
`Resposta 1` … `Resposta 15` + `Demais Respostas`
`Motivo 1` … `Motivo 15` + `Demais Motivos`

⚠️ **As perguntas têm texto diferente por marca** — o conceito é o mesmo, mas a redação é específica:

| Pergunta # | Conceito padrão | Variação por marca |
|---|---|---|
| **Pergunta 1** | **NPS Geral** (escala 0-10) | "Qual é a probabilidade de você recomendar o Grupo Servopa..." (todas) — Harley e VWC têm texto próprio |
| **Pergunta 2** | **Satisfação com processo de compra** | "Pensando em todo o processo de compra... qual seu nível de satisfação com a **{BANDEIRA}**?" |
| **Pergunta 3** | **NPS Test-Drive** | Texto similar, mas Harley/Triumph dizem "Test-Ride" |
| **Perguntas 4-15** | Detalhes (pontos a melhorar, sugestões, etc.) | Varia |

→ O pipeline precisa de um **mapeamento Pergunta→conceito por marca** (config YAML).

---

## Schema das Reclamações

### Reclamações (1 linha por reclamação)
| Campo | Obs |
|---|---|
| `Evento` | **PK** |
| `Tipo Evento` | `VENDAS NOVOS`, `VENDAS SEMINOVOS`, `VENDA DIRETA` |
| `Origem` | 12 canais (WhatsApp, Telefone, Email, Google, Reclame Aqui, Montadora, etc.) |
| `Grupo e Tipo Evento` | ex: `RECLAMACAO / VENDAS NOVOS` |
| `Marca`, `Empresa` | mesma convenção das pesquisas |
| `Modelo Veiculo`, `Cliente`, telefones | |
| `Chassi` | FK para NF |
| `Data Entrega Tec`, `Data 7º Dia`, `Data 28º Dia` | marcos de SLA |
| `Data Inclusão`, `Data Alteração`, `Dt Agendada` | |
| `Status` | `SUCESSO`, `INSUCESSO`, `AGUARDANDO`, `ANDAMENTO` |
| `Usuario Atual`, `Vendedor`, `Consultor` | |
| `Plano de Acao`, `Relato Cliente` | textos livres |
| `Motivo Reclamação`, `Motivo` | 43 valores (`ENTREGA`, `PROCESSO DE VENDA`, `F.I`, `TEST-DRIVE`, etc.) |
| `Tipo` | sempre `Fluxo Dia` |

### Motivos Reclamação (1:N — 1.795 linhas para 1.275 reclamações)
Detalhamento de cada motivo individual de uma reclamação + SLA específico.

| Campo | Obs |
|---|---|
| `Evento` | FK para Reclamações |
| `Usuario Evento Original` | quem registrou a reclamação |
| `Grupo Evento`, `Tipo Evento`, `Status` | |
| `Data Inclusao`, `Data Conclusao` | |
| `Consultor`, `Vendedor`, `Empresa`, `Marca`, `Usuario` | |
| `Motivo` | 46 valores (mais granulares que em Reclamações) |
| `Cliente` | |
| `Tempo SLA` | **texto** ex: `"524 horas e 48 minutos"` — exige parse |
| `Periodo` | ex: `"Período 2026/04/30 - 2026/05/01"` |
| `Nivel` | sempre `"Nivel: 1"` |
| `Observação` | texto livre — frequentemente cita a nota dada pelo cliente |

---

## Schema das Notas Fiscais (37 colunas)

A fonte real de **vendas** — não usar a pesquisa para contar vendas (nem toda venda gera pesquisa).

### Identificação da loja
| Campo | Valor exemplo |
|---|---|
| `Nome Empresa` | `"1.1 SERVOPA MATRIZ"` (formato `<código>.<código> NOME`) |
| `Empresa` | INT (código numérico) |
| `Revenda` | INT |

⚠️ **Atenção:** o `Nome Empresa` na NF é totalmente diferente do `Empresa` no Syonet. Exemplo:
- NF: `"1.1 SERVOPA MATRIZ"`
- Syonet: `"Servopa Rockfeller - Volkswagen - Curitiba-PR"`

→ Precisa de **de-para manual** entre as duas convenções, mapeando ambas para `store_id`.

### Tipo de operação
| Campo | Valores |
|---|---|
| `Grupo Operação` | `VN` (novos), `VU` (seminovos), `VD` (venda direta/frota) |
| `Fluxo Operação` | `SAIDA` (sempre nas vendas) |
| `Fisico Juridico` | `F` (PF) ou `J` (PJ) |

### Cliente, veículo e vendedor
`CPF / CNPJ`, `Nome Cliente`, `Genero`, `Bairro`, `Cidade`, `UF`, `CPF Vendedor`, `Vendedor`, `Chassi`, `Placa`, `Modelo`

### Datas e estoque
`Data` (data de venda) · `Dias Em Estoque` (FK pra calcular idade do estoque)

### Financeiro
`Volume`, `Dev.`, `Volume (-Dev)`, `Faturamento`, `Custo Compra`, `Vlr. Bônus`, `LB (Def)`, `% LB (Def)`, `Margem`, `% Margem`, `Vlr. ICM`, `Vlr. PIS/COFINS`, `Vlr. IPI`, `Val. Impostos`, `Vlr. Modalidade`, `Vlr. Preço Público`, `Vlr. Desconto`

---

## DePara de Vendedores — por que importa

### Vendedores de NOVOS (aba `CENTRO DE CUSTO` — 90 registros)
- Trabalham em **uma única loja** (centro de custo = loja)
- Mapeamento direto: `Vendedor → CENTRO DE CUSTO → ALOCADO EM`
- Exemplo: `EDUARDO PEREIRA → SERVOPA MATRIZ → SERVOPA MATRIZ`

### Vendedores de SEMINOVOS (aba `DePara Vendedores SemiNovos` — 93 registros)
- Podem ter o **centro de custo em uma loja** mas operar em **outra loja**
- A loja-origem do veículo seminovo no estoque pode ser diferente da loja de venda
- Mapeamento: `Vendedor → CENTRO DE CUSTO (loja origem) → LOJAS ALOCADO (loja real) → GESTOR → GERENTE`
- Exemplo: vendedor pode estar no centro de custo "BYD Servopa - Umuarama PR" mas atuar fisicamente em "Audi Center Cascavel"

**Implicação para o pipeline:**
Para atribuir corretamente uma venda de seminovo à loja, use `LOJAS ALOCADO` do DePara — não confie no campo `Empresa` da NF.

---

## Chaves de Junção entre as Fontes

| Chave | Liga | Cobertura | Prioridade |
|---|---|---|---|
| **Chassi** | Pesquisa ↔ NF | Alta (toda venda tem chassi) | 🥇 Principal |
| **Chassi** | Reclamação ↔ NF | Alta | 🥇 Principal |
| **Evento** | Reclamação ↔ Motivos Reclamação | 100% | 🥇 1:N obrigatória |
| **Reclamacao Evento** | Pesquisa → Reclamação | Parcial (só pesquisas que geraram reclamação; valor `0` significa sem reclamação) | 🥈 Pesquisa → Reclamação |
| **Vendedor** | NF ↔ CENTRO DE CUSTO ou DePara | Por CPF idealmente, fallback por nome | 🥉 Atribuição de loja |
| **Cliente + telefone** | Pesquisa ↔ Reclamação ↔ NF | Risco de homonímia | 🥉 Fallback |

---

## Modelo Relacional Proposto no Supabase

```
raw.nps_pesquisas       (Pesquisas Novos + Seminovos unificadas — 5.472 linhas/4m)
raw.reclamacoes         (Reclamações — 1.275 linhas/4m)
raw.motivos_reclamacao  (Motivos Reclamação — 1.795 linhas/4m)
raw.notas_fiscais       (NFs unificadas dos 4 meses — 13.279 linhas/4m)
raw.vendedores_novos    (CENTRO DE CUSTO — 90)
raw.vendedores_seminovos (DePara — 93)

dim.lojas               (48 lojas — mapeamento entre nomes Syonet/NF e store_id)
dim.marcas              (11 marcas + bandeiras)
dim.motivos_reclamacao  (taxonomia normalizada dos 46 motivos)

analytics.vw_nps_loja_mes
analytics.vw_reclamacoes_loja_mes
analytics.vw_vendas_loja_mes  -- com VN/VU/VD
analytics.vw_cx_consolidado   -- view principal do dashboard
```

---

## Regras de Negócio Importantes

1. **Pergunta 1 = NPS Geral** sempre (escala 0-10) — `Resposta 1` numérica é a nota NPS.
2. **`Reclamacao Evento = 0`** na Pesquisa significa **sem reclamação vinculada**, não é FK.
3. **Chassi como ponte** entre Pesquisa, Reclamação e NF — sempre normalizar (`UPPER + strip`).
4. **Marca multi-valor**: separar `CITROEN` de `PEUGEOT` no schema bruto, agrupar `PEUGEOT-CITROEN` no analytics. `VWC` (caminhões) é separado de `VW - VOLKSWAGEN`.
5. **Atribuição de loja para Seminovos**: usar `LOJAS ALOCADO` do DePara, não o campo `Empresa` da NF.
6. **NPS por etapa varia por marca**: Pergunta 2 pode ser "Negociação", "Atendimento" ou outra, dependendo do questionário. Precisa de mapeamento `Pergunta_X → conceito` por marca.
7. **`Tempo SLA` é texto**: parse de `"524 horas e 48 minutos"` → minutos inteiros.
8. **Pesquisa com `Status PENDENTE`** não tem resposta — não contar como respondida.
9. **Reclamações por canal direto** (WhatsApp, Reclame Aqui) não têm `Reclamacao Evento` vindo de pesquisa — entram direto via `Origem`.
10. **De-para de nomes de loja**: NF usa `"1.1 SERVOPA MATRIZ"`, Syonet usa `"Servopa Rockfeller - Volkswagen - Curitiba-PR"` — ambos mapeados para `store_id="servopa-matriz"`.

---

## Estrutura do Projeto

```
Observabilidade/
├── observabilidade.py              # Gera dashboard_observabilidade.html
├── dashboard_observabilidade.html  # Output (Chart.js inline)
├── mocks/
│   └── gerar_mock.py               # Mock atual (substituído por pipelines reais aos poucos)
├── data/
│   ├── raw/                        # Drop dos arquivos Excel
│   │   └── Dados Jan-Abril 2026.xlsx
│   └── Lojas_Grupo_Servopa.md      # Estrutura de referência
├── pipelines/                      # Pipelines de dados (em desenvolvimento)
│   ├── nps/                        # 1º pipeline — pesquisas NPS
│   ├── reclamacoes/                # 2º pipeline — reclamações + motivos
│   ├── vendas/                     # 3º pipeline — notas fiscais
│   └── shared/
│       ├── lojas_mapping.yaml      # de-para Syonet/NF → store_id
│       └── marcas.yaml             # marca → bandeira(s)
├── supabase/
│   └── migrations/                 # SQL schema versionado
├── logs/
│   └── stores_data.json            # consumido pelo dashboard
└── README.md
```

---

## Fluxo de Build do Dashboard

```bash
# Geração com dados reais (estado-alvo)
python3 pipelines/nps/run.py            # 1. Carrega pesquisas
python3 pipelines/reclamacoes/run.py    # 2. Carrega reclamações
python3 pipelines/vendas/run.py         # 3. Carrega NFs
python3 observabilidade.py              # 4. Lê Supabase, gera dashboard
```

Estado atual: mocks até cada pipeline estar implementado e validado.

---

## Roadmap dos Pipelines

| Ordem | Pipeline | Fonte | Status |
|---|---|---|---|
| 1 | **NPS** | Pesquisas Novos + Seminovos | A implementar |
| 2 | **Reclamações** | Reclamações + Motivos | A implementar |
| 3 | **Vendas** | NFs jan-abril | A implementar |
| 4 | **Vendedores** | CENTRO DE CUSTO + DePara | A implementar (suporta os 3 acima) |
| - | Estoque | a definir | Fora do escopo inicial |
| - | Leads / Pipeline de vendas | a definir (Syonet CRM tem isso?) | Fora do escopo inicial |
| - | Pós-Venda | a definir | Fora do escopo inicial |

---

*Projeto multi-marca · Grupo Servopa · Maio/2026 · Repositório: ThomasVosP/observabilidade*
