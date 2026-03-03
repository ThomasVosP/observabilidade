# Projeto: Pipeline de Dados CX/CS — Grupo Servopa

## Contexto do Projeto

Você está desenvolvendo um pipeline de dados para a área de **Customer Experience (CX) e Customer Success (CS)** do **Grupo Servopa**, concessionária BYD. O objetivo é extrair dados de duas fontes (Syonet CRM e Apollo Linx), carregá-los no **Google BigQuery** e disponibilizá-los para dashboards no **Looker Studio**.

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Fonte 1 | Syonet CRM REST API (`https://api.syonet.com/v1`) |
| Fonte 2 | Apollo Linx REST API (`https://api.apollolinx.com.br/v2`) |
| Extração | Python 3 + `requests` + `google-cloud-bigquery` |
| Orquestração | Google Cloud Functions + Cloud Scheduler |
| Data Warehouse | Google BigQuery |
| Transformação | SQL (BigQuery) ou dbt |
| Visualização | Looker Studio |

---

## Credenciais e Configuração

```bash
# Syonet CRM
SYONET_API_URL=https://api.syonet.com/v1
SYONET_API_KEY=<bearer-token>
SYONET_AUTH_TYPE=bearer   # ou apikey ou basic

# Apollo Linx
APOLLO_API_URL=https://api.apollolinx.com.br/v2
APOLLO_API_KEY=<api-key>
APOLLO_AUTH_TYPE=bearer

# Google Cloud
GCP_PROJECT_ID=<project-id>
BIGQUERY_DATASET_RAW=raw
BIGQUERY_DATASET_STAGING=staging
BIGQUERY_DATASET_ANALYTICS=analytics
```

---

## Endpoints das APIs

### Syonet CRM

```
GET  /clientes?email={email}              → Perfil do cliente
GET  /clientes?cpf={cpf}                 → Perfil do cliente
GET  /clientes/{id}/tickets              → Tickets de atendimento
GET  /clientes/{id}/feedbacks            → Histórico de feedbacks NPS/CSAT
GET  /feedbacks?status=pendente&limite=50 → Feedbacks pendentes de triagem
POST /feedbacks/{id}/triagem             → Registrar triagem de feedback
```

### Apollo Linx

```
GET /pedidos?email={email}               → Histórico de compras
GET /pedidos?cpf={cpf}                   → Histórico de compras
GET /clientes/{id}/resumo                → Métricas de cliente (LTV, ticket médio)
GET /pedidos/{numero}                    → Detalhes do pedido
GET /pedidos?status=entregue&sem_avaliacao=true&ultimos_dias=30  → Candidatos a pesquisa
```

---

## Estrutura de Dados Reais (Analisados)

Foram analisados 4 arquivos de exportação do mês de Janeiro/2026. Esses são os dados reais que serão ingeridos pelo pipeline.

### Fonte 1 — BYD COMPLETO (Pesquisas de Satisfação)
- **376 registros** | Arquivo: `BYD - COMPLETO.xlsx`
- Atenção: o arquivo tem **duas linhas de cabeçalho**. O cabeçalho real dos dados está na **linha 3 (índice 2)**
- Campos principais:
  - `Evento` → ID único da pesquisa (PK)
  - `Chassi` → FK para dim_vendas (**chave primária de cruzamento**)
  - `Reclamacao Evento` → FK para fato_reclamacoes
  - `NPS`, `NPS NEGOCIAÇÃO`, `NPS TD`, `NPS ACESS`, `NPS ENTREGA` → notas por etapa
  - `RESPOSTA ABERTA` → comentário do cliente
  - `Modelo`, `Empresa`, `Cliente`, `Tipo Pesquisa`, `Origem`

### Fonte 2 — BYD RAC (Reclamações — Detalhe)
- **104 registros** | Arquivo: `BYD RAC 01.26.xlsx`
- Campos principais:
  - `Evento` → ID único (PK) — 100% único
  - `Chassi` → FK para dim_vendas
  - `Relato Cliente` → texto detalhado do cliente
  - `Motivo Reclamação`, `Plano de Acao`, `Status`
  - `Vendedor`, `Consultor`

### Fonte 3 — BYD MOTIVO (Reclamações — Gestão SLA)
- **119 registros** | Arquivo: `BYD MOTIVO 01.2026.xlsx`
- Campos principais:
  - `Evento` → FK para RAC (76 matches = 100% do RAC)
  - `Motivo`, `Nível`, `Período`, `Tempo SLA`
  - `Status` (ANDAMENTO, CONCLUIDO)
  - `Consultor`, `Vendedor`

### Fonte 4 — BASE DE VENDAS (Dados Transacionais)
- **429 registros** | Arquivo: `BASE DE VENDAS BYD 01.2026.xlsx`
- Campos principais:
  - `Chassi` → PK (100% único — **chave mestra de cruzamento**)
  - `CPF Cliente`
  - `Faturamento`, `Margem`, `% Margem`, `Custo compra`
  - `Modelo`, `Empresa`, `Vendedor`
  - `Data`, `Cidade`, `Uf`

---

## Chaves de Conexão (Resultado da Análise)

| Chave | Arquivos | Matches Confirmados | Prioridade |
|---|---|---|---|
| **CHASSI** | COMPLETO ↔ VENDAS | 163 registros (43%) | 🥇 Principal |
| **CHASSI** | RAC ↔ VENDAS | 19 registros | 🥇 Principal |
| **EVENTO** | MOTIVO ↔ RAC | 76 registros (100%) | 🥈 Pesquisa/Reclamação |
| **Reclamacao Evento** | COMPLETO → RAC | 49 registros | 🥈 Link pesquisa→reclamação |
| **Nome Cliente** | Todos os 4 | 161 (COMPLETO↔VENDAS) | 🥉 Fallback (risco homonímia) |

> ⚠️ O COMPLETO **não tem CPF** — apenas telefone e e-mail. O Chassi é a única ponte confiável entre pesquisa e venda.

---

## Modelo Relacional no BigQuery

### Datasets

```
raw_syonet.*        → dados brutos do Syonet CRM
raw_apollo.*        → dados brutos do Apollo Linx
staging.*           → dados limpos, tipados, sem duplicatas
analytics.*         → modelos prontos para consumo no Looker Studio
```

### Schema: `analytics.fato_pesquisas`
Origem: BYD COMPLETO (via Syonet API)

```sql
CREATE TABLE analytics.fato_pesquisas (
  evento_pesquisa   STRING NOT NULL,   -- PK
  chassi            STRING,            -- FK → dim_vendas
  reclamacao_evento STRING,            -- FK → fato_reclamacoes
  cliente           STRING,
  empresa           STRING,
  modelo            STRING,
  tipo_pesquisa     STRING,
  origem            STRING,
  data_pesquisa     TIMESTAMP,
  status_pesquisa   STRING,
  nps_geral         INT64,
  nps_negociacao    INT64,
  nps_test_drive    INT64,
  nps_acessorios    INT64,
  nps_entrega       INT64,
  resposta_aberta   STRING,
  dt_ingestao       TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

### Schema: `analytics.dim_vendas`
Origem: BASE DE VENDAS (via Apollo Linx API ou exportação)

```sql
CREATE TABLE analytics.dim_vendas (
  chassi            STRING NOT NULL,   -- PK (100% único)
  cpf_cliente       STRING,
  cliente           STRING,
  modelo            STRING,
  empresa           STRING,
  vendedor          STRING,
  cidade            STRING,
  uf                STRING,
  data_venda        DATE,
  faturamento       FLOAT64,
  custo_compra      FLOAT64,
  margem            FLOAT64,
  pct_margem        FLOAT64,
  dias_estoque      INT64,
  nro_nf            STRING,
  dt_ingestao       TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

### Schema: `analytics.fato_reclamacoes`
Origem: RAC + MOTIVO (via Syonet API)

```sql
CREATE TABLE analytics.fato_reclamacoes (
  evento_reclamacao STRING NOT NULL,   -- PK
  chassi            STRING,            -- FK → dim_vendas
  cliente           STRING,
  empresa           STRING,
  modelo            STRING,
  relato_cliente    STRING,
  motivo_reclamacao STRING,
  plano_acao        STRING,
  status            STRING,            -- ANDAMENTO, SUCESSO, INSUCESSO
  tempo_sla         STRING,
  nivel             STRING,
  periodo           STRING,
  consultor         STRING,
  vendedor          STRING,
  data_inclusao     TIMESTAMP,
  data_conclusao    TIMESTAMP,
  dt_ingestao       TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

---

## View Analítica Principal (Para o Looker Studio)

```sql
-- analytics.vw_cx_consolidado
SELECT
  p.evento_pesquisa,
  p.cliente,
  p.empresa,
  p.modelo,
  p.chassi,
  p.data_pesquisa,
  p.tipo_pesquisa,
  p.nps_geral,
  p.nps_negociacao,
  p.nps_test_drive,
  p.nps_acessorios,
  p.nps_entrega,
  CASE
    WHEN p.nps_geral >= 9 THEN 'Promotor'
    WHEN p.nps_geral >= 7 THEN 'Neutro'
    WHEN p.nps_geral IS NOT NULL THEN 'Detrator'
    ELSE 'Sem Resposta'
  END AS classificacao_nps,
  p.resposta_aberta,
  p.reclamacao_evento,
  CASE WHEN r.evento_reclamacao IS NOT NULL THEN TRUE ELSE FALSE END AS tem_reclamacao,
  r.motivo_reclamacao,
  r.status AS status_reclamacao,
  r.tempo_sla,
  v.faturamento,
  v.margem,
  v.pct_margem,
  v.vendedor AS vendedor_venda,
  v.data_venda,
  v.cpf_cliente
FROM analytics.fato_pesquisas p
LEFT JOIN analytics.dim_vendas v ON p.chassi = v.chassi
LEFT JOIN analytics.fato_reclamacoes r ON p.reclamacao_evento = r.evento_reclamacao
```

---

## Estrutura do Projeto (Diretórios)

```
cx_pipeline/
├── extractors/
│   ├── syonet_extractor.py      # Extrai pesquisas, tickets, feedbacks
│   └── apollo_extractor.py      # Extrai pedidos, resumo de clientes
├── loaders/
│   └── bigquery_loader.py       # Carrega dados no BigQuery (incremental)
├── transformations/
│   ├── staging/
│   │   ├── stg_pesquisas.sql    # Limpa dados do COMPLETO
│   │   ├── stg_reclamacoes.sql  # Limpa RAC + MOTIVO
│   │   └── stg_vendas.sql       # Limpa BASE DE VENDAS
│   └── analytics/
│       ├── fato_pesquisas.sql
│       ├── dim_vendas.sql
│       ├── fato_reclamacoes.sql
│       └── vw_cx_consolidado.sql
├── utils/
│   ├── auth.py                  # Gerencia tokens das APIs
│   ├── retry.py                 # Retry com backoff exponencial
│   └── logger.py                # Logging estruturado
├── tests/
│   ├── test_extractors.py
│   └── test_transformations.py
├── main.py                      # Entry point para Cloud Functions
├── requirements.txt
└── .env.example
```

---

## Regras de Negócio Importantes

1. **Cabeçalho duplo no COMPLETO**: ao ler o arquivo Excel ou API, usar o cabeçalho da linha 3 (índice 2), não da linha 1.
2. **Chassi como PK**: sempre normalizar o chassi (strip + upper) antes de qualquer join.
3. **Reclamacao Evento = 0**: no COMPLETO, valor `0` significa sem reclamação vinculada (não é FK válida).
4. **Carga incremental**: usar `data_inclusao` como watermark para extrair apenas registros novos.
5. **NPS ACESS pode ser texto**: nem sempre é numérico (ex: "FOI OFERECIDO, MAS NÃO QUIS ACESSÓRIOS") — tratar como string quando não numérico.
6. **CPF não disponível no COMPLETO**: campo "Cpf/Cnpj" no cabeçalho errado na verdade contém telefone. CPF real só existe na BASE DE VENDAS.

---

## Dashboards Planejados no Looker Studio

1. **CX Overview** — NPS geral, por empresa, por etapa, tendência temporal
2. **Atendimento** — Volume de tickets, SLA, canais
3. **Reclamações** — Motivos, prioridade, status de tratativa, tempo de resolução
4. **Vendedor vs CX** — NPS e reclamações por vendedor
5. **Impacto Financeiro** — Faturamento por classificação NPS (Promotor/Neutro/Detrator)

---

## Tarefa Inicial Sugerida

Comece implementando o extrator do Syonet para pesquisas:

```python
# Implemente extractors/syonet_extractor.py com:
# 1. Autenticação via Bearer token
# 2. Extração incremental de feedbacks (GET /feedbacks com filtro de data)
# 3. Enriquecimento com dados do cliente (GET /clientes/{id})
# 4. Retry com backoff exponencial para erros 429/5xx
# 5. Logging estruturado de cada requisição
# 6. Retorno de lista de dicts prontos para carga no BigQuery
```

---

*Projeto iniciado em Março/2026 | Área de Customer Experience | Grupo Servopa*
