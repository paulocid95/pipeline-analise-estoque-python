"""Passo 5: Visualização de Dados e Geração de Gráficos Executivos.

Este script lê a base consolidada em 'dados_processados/estoque_consolidado_limpo.csv'
e utiliza matplotlib e seaborn para criar gráficos executivos com acabamento profissional:
1. 'graficos/valor_por_categoria.png' : Valor financeiro retido por categoria (barras horizontais com percentuais).
2. 'graficos/distribuicao_estoque_fornecedor.png': Comparativo de unidades em estoque e SKUs por fornecedor.
3. 'graficos/alerta_ruptura_estoque.png': Produtos zerados ranqueados por ticket unitário (risco de receita).
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import seaborn as sns


# ==============================================================================
# CONFIGURAÇÃO DE ESTILO E CORES
# ==============================================================================
def configurar_estilo_visual() -> None:
    """Configura o tema global e parâmetros tipográficos do matplotlib e seaborn."""
    sns.set_theme(style="whitegrid", font="sans-serif")
    plt.rcParams.update({
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelsize": 12,
        "axes.labelweight": "medium",
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.titlesize": 16,
        "figure.titleweight": "bold",
        "figure.facecolor": "#ffffff",
        "axes.facecolor": "#fafbfc",
        "grid.color": "#e2e8f0",
        "grid.linestyle": "--",
        "grid.alpha": 0.7,
    })


def formatar_brl(valor: float) -> str:
    """Formata número para o padrão monetário brasileiro."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ==============================================================================
# GERAÇÃO DOS GRÁFICOS
# ==============================================================================
def gerar_grafico_valor_categoria(df: pd.DataFrame, pasta_saida: Path) -> Path:
    """Gera gráfico de barras horizontais do capital total retido por categoria."""
    df_cat = df.groupby("categoria", as_index=False).agg(
        valor_total=("valor_total", "sum"),
        unidades=("estoque", "sum"),
    ).sort_values(by="valor_total", ascending=True)

    total_global = df_cat["valor_total"].sum()
    df_cat["pct"] = (df_cat["valor_total"] / total_global) * 100

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)

    cores = ["#94a3b8", "#38bdf8", "#0284c7"]
    barras = ax.barh(
        df_cat["categoria"],
        df_cat["valor_total"],
        color=cores,
        edgecolor="#0f172a",
        linewidth=0.8,
        height=0.55,
    )

    # Rótulos de dados e percentuais em cada barra
    for barra, pct, val in zip(barras, df_cat["pct"], df_cat["valor_total"]):
        largura = barra.get_width()
        texto = f"{formatar_brl(val)}  ({pct:.1f}%)"
        ax.text(
            largura + (total_global * 0.015),
            barra.get_y() + barra.get_height() / 2,
            texto,
            va="center",
            ha="left",
            fontsize=10.5,
            fontweight="bold",
            color="#0f172a",
        )

    ax.set_xlim(0, df_cat["valor_total"].max() * 1.35)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"R$ {x/1e3:.0f}k" if x > 0 else "R$ 0"))
    ax.set_title("Capital Financeiro Total Retido em Estoque por Categoria", pad=20)
    ax.set_xlabel("Montante Retido (R$)")
    ax.set_ylabel("Categoria")

    fig.text(
        0.5,
        -0.03,
        f"Montante Financeiro Consolidado: {formatar_brl(total_global)}",
        ha="center",
        fontsize=11,
        fontstyle="italic",
        color="#475569",
    )

    sns.despine(top=True, right=True, left=False, bottom=False)
    arquivo_saida = pasta_saida / "valor_por_categoria.png"
    plt.savefig(arquivo_saida, dpi=300, bbox_inches="tight")
    plt.close()
    return arquivo_saida


def gerar_grafico_distribuicao_fornecedor(df: pd.DataFrame, pasta_saida: Path) -> Path:
    """Gera gráfico comparativo de volume físico de estoque vs. diversidade de SKUs."""
    df_forn = df.groupby("fornecedor", as_index=False).agg(
        unidades=("estoque", "sum"),
        skus=("id_produto", "count"),
        valor_total=("valor_total", "sum"),
    ).sort_values(by="unidades", ascending=False)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # Painel 1: Unidades em Estoque
    cores_unidades = ["#2563eb", "#3b82f6", "#60a5fa"]
    barras1 = ax1.bar(
        df_forn["fornecedor"],
        df_forn["unidades"],
        color=cores_unidades,
        edgecolor="#1e293b",
        linewidth=0.8,
        width=0.55,
    )
    for barra in barras1:
        altura = barra.get_height()
        ax1.text(
            barra.get_x() + barra.get_width() / 2,
            altura + 6,
            f"{int(altura)} un",
            ha="center",
            va="bottom",
            fontweight="bold",
            color="#0f172a",
        )
    ax1.set_ylim(0, df_forn["unidades"].max() * 1.18)
    ax1.set_title("Volume Físico Total (Unidades)", pad=15)
    ax1.set_ylabel("Quantidade de Peças")
    ax1.set_xlabel("Fornecedor")

    # Painel 2: Variedade de SKUs
    cores_skus = ["#0d9488", "#14b8a6", "#2dd4bf"]
    barras2 = ax2.bar(
        df_forn["fornecedor"],
        df_forn["skus"],
        color=cores_skus,
        edgecolor="#1e293b",
        linewidth=0.8,
        width=0.55,
    )
    for barra in barras2:
        altura = barra.get_height()
        ax2.text(
            barra.get_x() + barra.get_width() / 2,
            altura + 0.2,
            f"{int(altura)} SKUs",
            ha="center",
            va="bottom",
            fontweight="bold",
            color="#0f172a",
        )
    ax2.set_ylim(0, 11)
    ax2.set_title("Diversidade de Catálogo (SKUs Ativos)", pad=15)
    ax2.set_ylabel("Número de Produtos")
    ax2.set_xlabel("Fornecedor")

    fig.suptitle("Comparativo de Fornecedores: Volume Físico vs. Variedade de Catálogo", y=1.03)
    sns.despine(top=True, right=True)

    arquivo_saida = pasta_saida / "distribuicao_estoque_fornecedor.png"
    plt.savefig(arquivo_saida, dpi=300, bbox_inches="tight")
    plt.close()
    return arquivo_saida


def gerar_grafico_alerta_ruptura(df: pd.DataFrame, pasta_saida: Path) -> Path:
    """Gera gráfico destacando os itens com estoque zerado ranqueados por ticket unitário."""
    df_rup = df[df["estoque"] == 0].copy()
    df_rup = df_rup.sort_values(by="preco", ascending=True)

    # Nomes concisos com identificador e fornecedor para a legenda
    df_rup["rotulo"] = df_rup["produto"].apply(lambda x: x if len(x) <= 32 else x[:30] + "...")
    df_rup["rotulo_completo"] = [
        f"{r}  [{f}]" for r, f in zip(df_rup["rotulo"], df_rup["fornecedor"])
    ]

    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)

    # Gradiente em tons quentes de alerta
    paleta_alerta = sns.color_palette("YlOrRd", n_colors=len(df_rup))

    barras = ax.barh(
        df_rup["rotulo_completo"],
        df_rup["preco"],
        color=paleta_alerta,
        edgecolor="#7f1d1d",
        linewidth=0.8,
        height=0.6,
    )

    for barra, preco, cat in zip(barras, df_rup["preco"], df_rup["categoria"]):
        largura = barra.get_width()
        texto = f"{formatar_brl(preco)}  • {cat}"
        ax.text(
            largura + 120,
            barra.get_y() + barra.get_height() / 2,
            texto,
            va="center",
            ha="left",
            fontsize=9.5,
            fontweight="bold",
            color="#991b1b",
        )

    ax.set_xlim(0, df_rup["preco"].max() * 1.35)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"R$ {x/1e3:.1f}k" if x >= 1000 else f"R$ {x:.0f}"))
    ax.set_title("Alerta de Ruptura de Estoque: Produtos Zerados (Ordem por Ticket)", pad=20)
    ax.set_xlabel("Preço Unitário / Potencial de Faturamento Unitário (R$)")
    ax.set_ylabel("Produto [Fornecedor]")

    fig.text(
        0.5,
        -0.03,
        "Itens que demandam reposição prioritária pelo alto valor unitário e risco de perda de receita.",
        ha="center",
        fontsize=10.5,
        fontstyle="italic",
        color="#7f1d1d",
    )

    sns.despine(top=True, right=True)
    arquivo_saida = pasta_saida / "alerta_ruptura_estoque.png"
    plt.savefig(arquivo_saida, dpi=300, bbox_inches="tight")
    plt.close()
    return arquivo_saida


# ==============================================================================
# EXECUÇÃO PRINCIPAL
# ==============================================================================
def main() -> None:
    diretorio_raiz = Path(__file__).parent
    caminho_dados = diretorio_raiz / "dados_processados" / "estoque_consolidado_limpo.csv"
    pasta_graficos = diretorio_raiz / "graficos"
    pasta_graficos.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(" INICIANDO GERAÇÃO DE GRÁFICOS EXECUTIVOS COM MATPLOTLIB & SEABORN")
    print("=" * 80)

    if not caminho_dados.exists():
        raise FileNotFoundError(f"Base de dados não encontrada: {caminho_dados.resolve()}")

    # 1. Carrega dados e calcula valor financeiro
    df = pd.read_csv(caminho_dados)
    df["valor_total"] = df["preco"] * df["estoque"]

    # 2. Configura estética dos gráficos
    configurar_estilo_visual()

    # 3. Geração e salvamento das imagens
    grafico1 = gerar_grafico_valor_categoria(df, pasta_graficos)
    print(f"[OK] Gráfico 1 gerado: {grafico1.name} (Resolução: 300 DPI)")

    grafico2 = gerar_grafico_distribuicao_fornecedor(df, pasta_graficos)
    print(f"[OK] Gráfico 2 gerado: {grafico2.name} (Resolução: 300 DPI)")

    grafico3 = gerar_grafico_alerta_ruptura(df, pasta_graficos)
    print(f"[OK] Gráfico 3 gerado: {grafico3.name} (Resolução: 300 DPI)")

    print("=" * 80)
    print(" TODOS OS GRÁFICOS FORAM SALVOS COM SUCESSO NA PASTA:")
    print(f" -> {pasta_graficos.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
