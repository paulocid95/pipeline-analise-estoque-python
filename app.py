import os
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
import streamlit as st

# 1. Configuração da página da aplicação
st.set_page_config(
    page_title="Dashboard de Análise de Estoque",
    page_icon="📦",
    layout="wide",
)

# 2. Conexão com o banco de dados Neon
load_dotenv()
database_url = os.getenv("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)


@st.cache_resource
def obter_conexao():
    return create_engine(database_url)


engine = obter_conexao()


# 3. Consulta analítica no PostgreSQL (Traz apenas a carga mais recente por produto)
@st.cache_data(ttl=60)
def carregar_dados_analiticos():
    query = """
        SELECT DISTINCT ON (p.sku)
            p.sku,
            p.nome_produto,
            c.nome_categoria,
            p.preco_unitario,
            f.quantidade_disponivel,
            f.valor_total_estoque,
            f.status_reposicao,
            f.data_carga
        FROM core.fato_estoque f
        JOIN core.dim_produtos p ON f.id_produto = p.id_produto
        LEFT JOIN core.dim_categorias c ON p.id_categoria = c.id_categoria
        ORDER BY p.sku, f.data_carga DESC;
    """
    df_raw = pd.read_sql(text(query), engine)
    return df_raw.sort_values(by="valor_total_estoque", ascending=False)


# Carrega os dados do banco
df = carregar_dados_analiticos()

# 4. Barra Lateral - Filtros
st.sidebar.header("🔍 Filtros de Consulta")

categorias_disponiveis = ["Todas"] + sorted(df["nome_categoria"].dropna().unique().tolist())
categoria_selecionada = st.sidebar.selectbox("Filtrar por Categoria:", categorias_disponiveis)

status_disponiveis = ["Todos"] + sorted(df["status_reposicao"].unique().tolist())
status_selecionado = st.sidebar.selectbox("Filtrar por Status de Reposição:", status_disponiveis)

# Aplicação dos filtros no DataFrame
df_filtrado = df.copy()
if categoria_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["nome_categoria"] == categoria_selecionada]
if status_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["status_reposicao"] == status_selecionado]

# 5. Cabeçalho e KPIs Principais
st.title("📦 Monitoramento e Gestão Analítica de Estoque")
st.markdown("Painel conectado diretamente ao **PostgreSQL (Neon)** em tempo real.")
st.divider()

col1, col2, col3, col4 = st.columns(4)

total_itens = int(df_filtrado["quantidade_disponivel"].sum())
valor_total = float(df_filtrado["valor_total_estoque"].sum())
itens_criticos = int((df_filtrado["status_reposicao"] == "CRITICO").sum())
itens_alerta = int((df_filtrado["status_reposicao"] == "ALERTA").sum())

col1.metric("📦 Volume Físico Total", f"{total_itens:,}".replace(",", "."))
col2.metric("💰 Capital Imobilizado", f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("🚨 Produtos Críticos (Zerados)", itens_criticos)
col4.metric("⚠️ Produtos em Alerta", itens_alerta)

st.divider()

# 6. Gráficos Analíticos
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("Capital Imobilizado por Categoria")
    if valor_total > 0:
        fig_cat = px.bar(
            df_filtrado.groupby("nome_categoria", as_index=False)["valor_total_estoque"].sum(),
            x="nome_categoria",
            y="valor_total_estoque",
            labels={"nome_categoria": "Categoria", "valor_total_estoque": "Valor Total (R$)"},
            color="nome_categoria",
            text_auto=".2s",
        )
        fig_cat.update_layout(showlegend=False)
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("ℹ️ Não há capital imobilizado para os filtros selecionados (Estoque Zerado / R$ 0,00).")

with col_graf2:
    st.subheader("Distribuição do Status de Reposição")
    if len(df_filtrado) > 0:
        # Se todos os itens somarem R$ 0 (ex.: status CRITICO), calcula por quantidade de produtos
        coluna_valor = "valor_total_estoque" if valor_total > 0 else None
        
        if coluna_valor:
            fig_status = px.pie(
                df_filtrado,
                names="status_reposicao",
                values=coluna_valor,
                hole=0.4,
                color="status_reposicao",
                color_discrete_map={
                    "CRITICO": "#d9534f",
                    "ALERTA": "#f0ad4e",
                    "NORMAL": "#5cb85c",
                    "EXCESSO": "#0275d8",
                },
            )
        else:
            # Gráfico de pizza pela quantidade de itens em ruptura
            contagem_status = df_filtrado["status_reposicao"].value_counts().reset_index()
            contagem_status.columns = ["status_reposicao", "quantidade_skus"]
            fig_status = px.pie(
                contagem_status,
                names="status_reposicao",
                values="quantidade_skus",
                hole=0.4,
                color="status_reposicao",
                color_discrete_map={"CRITICO": "#d9534f"},
            )
        st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.info("ℹ️ Nenhum dado disponível para os filtros selecionados.")

# 7. Detalhamento dos Registros
st.subheader("📋 Tabela Operacional de Produtos")
st.dataframe(
    df_filtrado[[
        "sku", "nome_produto", "nome_categoria", "preco_unitario", 
        "quantidade_disponivel", "valor_total_estoque", "status_reposicao"
    ]],
    use_container_width=True,
    hide_index=True,
)