# 📦 Sistema Integrado de Engenharia de Dados, Análise e Monitoramento de Estoque

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?logo=pandas&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon_Serverless-336791?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM%2FCore-D71F00?logo=sqlalchemy&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)
![Git](https://img.shields.io/badge/Git-VCS-F05032?logo=git&logoColor=white)
![Status](https://img.shields.io/badge/Status-Concluído-success)
![License](https://img.shields.io/badge/Licença-MIT-green)

Solução modular e automatizada de **Engenharia e Análise de Dados** ponta a ponta (ETL). O projeto abrange desde o profiling e higienização de arquivos heterogêneos com **Python e Pandas**, passando por modelagem dimensional (*Star Schema*) com persistência transacional em nuvem via **PostgreSQL (Neon)** e **SQLAlchemy**, orquestração automatizada com logs estruturados, até a disponibilização de relatórios executivos estáticos e um **Dashboard Interativo em Streamlit**.

---

## 🏛️ Arquitetura do Sistema de Dados

O pipeline opera sob uma esteira modular e desacoplada, garantindo rastreabilidade desde a extração até o consumo analítico:

```text
[ Fontes Despadronizadas ] (dados_brutos/ - Fornecedores A, B, C)
            │
            ▼
[ Profiling & Diagnóstico ] (exploracao_diagnostico.py)
            │
            ▼
[ Higienização & Regex ] (limpeza_padronizacao.py - Pandas)
            │
            ▼
[ Base Canônica SSOT ] (dados_processados/estoque_consolidado_limpo.csv)
            │
            ├───────────────┬───────────────────────────────┐
            ▼               ▼                               ▼
    [ Análise & KPIs ] [ Gráficos Executivos ]    [ Carga Relacional / Upsert ]
    (analise_negocio.py) (visualizacao_graficos.py) (carregar_dados.py - SQLAlchemy)
            │               │                               │
            ▼               ▼                               ▼
    [ CSV de KPIs ]   [ Imagens 300 DPI ]           [ PostgreSQL em Nuvem ]
                                                    (Neon.tech - Schema 'core')
                                                     ├── dim_categorias
                                                     ├── dim_produtos
                                                     └── fato_estoque
                                                            │
                                                            ▼
                                                [ Dashboard Interativo ]
                                                (app.py - Streamlit & Plotly)