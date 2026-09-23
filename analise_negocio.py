"""Passo 4: Análise de Dados e Métricas de Negócio com Pandas.

Este script lê a base consolidada e limpa de estoque e realiza:
1. Cálculo do valor total de estoque (monetário).
2. Agrupamento e KPIs por categoria de produto.
3. Comparativo de desempenho e concentração por fornecedor.
4. Relatório de alerta de ruptura de estoque (itens com estoque zerado).
5. Exportação dos KPIs consolidados para 'dados_processados/resumo_kpis_categoria.csv'.
"""

from pathlib import Path
import sys
import pandas as pd


def carregar_estoque_consolidado(caminho_csv: Path) -> pd.DataFrame:
    """Carrega o arquivo consolidado e limpo de estoque com tratamento de erro.

    Args:
        caminho_csv (Path): Caminho para o arquivo CSV consolidado.

    Returns:
        pd.DataFrame: DataFrame com as colunas canônicas validadas.

    Raises:
        FileNotFoundError: Se o arquivo consolidado não for encontrado.
    """
    if not caminho_csv.exists():
        raise FileNotFoundError(
            f"O arquivo consolidado não foi encontrado em: '{caminho_csv.resolve()}'.\n"
            "Por favor, execute o script 'limpeza_padronizacao.py' antes de rodar esta análise."
        )

    df = pd.read_csv(caminho_csv)

    colunas_obrigatorias = {"id_produto", "produto", "categoria", "preco", "estoque", "fornecedor"}
    if not colunas_obrigatorias.issubset(df.columns):
        raise ValueError(f"O arquivo CSV não possui todas as colunas obrigatórias: {colunas_obrigatorias}")

    return df


def calcular_coluna_valor_total(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula a coluna 'valor_total' como produto entre preco e estoque.

    Args:
        df (pd.DataFrame): DataFrame original.

    Returns:
        pd.DataFrame: Cópia do DataFrame com a coluna 'valor_total' adicionada.
    """
    df_calc = df.copy()
    df_calc["valor_total"] = (df_calc["preco"] * df_calc["estoque"]).round(2)
    return df_calc


def analisar_por_categoria(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa os produtos por categoria e calcula os KPIs principais.

    Retorna um DataFrame com:
    - Total de itens cadastrados
    - Quantidade física total de unidades em estoque
    - Valor financeiro total retido
    - Preço médio dos produtos
    - Percentual de participação no valor financeiro total
    """
    valor_global = df["valor_total"].sum()

    agrupado = df.groupby("categoria", as_index=False).agg(
        qtd_skus=("id_produto", "count"),
        unidades_estoque=("estoque", "sum"),
        valor_total_estoque=("valor_total", "sum"),
        preco_medio=("preco", "mean"),
    )

    agrupado["participacao_valor_pct"] = (
        (agrupado["valor_total_estoque"] / valor_global) * 100
    ).round(2)

    agrupado["valor_total_estoque"] = agrupado["valor_total_estoque"].round(2)
    agrupado["preco_medio"] = agrupado["preco_medio"].round(2)

    return agrupado.sort_values(by="valor_total_estoque", ascending=False).reset_index(drop=True)


def analisar_por_fornecedor(df: pd.DataFrame) -> pd.DataFrame:
    """Compara os fornecedores avaliando volume, preço médio e capital retido.

    Retorna um DataFrame com:
    - Quantidade de SKUs/produtos fornecidos
    - Quantidade física em estoque
    - Preço médio praticado
    - Valor total em estoque
    - Percentual de participação no valor total
    """
    valor_global = df["valor_total"].sum()

    agrupado = df.groupby("fornecedor", as_index=False).agg(
        qtd_skus=("id_produto", "count"),
        unidades_estoque=("estoque", "sum"),
        preco_medio=("preco", "mean"),
        valor_total_estoque=("valor_total", "sum"),
    )

    agrupado["participacao_valor_pct"] = (
        (agrupado["valor_total_estoque"] / valor_global) * 100
    ).round(2)

    agrupado["preco_medio"] = agrupado["preco_medio"].round(2)
    agrupado["valor_total_estoque"] = agrupado["valor_total_estoque"].round(2)

    return agrupado.sort_values(by="valor_total_estoque", ascending=False).reset_index(drop=True)


def identificar_rupturas(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra todos os itens com estoque zerado (necessidade de reposição imediata)."""
    rupturas = df[df["estoque"] == 0][
        ["id_produto", "produto", "categoria", "fornecedor", "preco"]
    ].copy()
    return rupturas.sort_values(by=["categoria", "produto"]).reset_index(drop=True)


def formatar_moeda(valor: float) -> str:
    """Formata um float como valor monetário brasileiro (R$ X.XXX,XX)."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def imprimir_relatorio_terminal(
    df: pd.DataFrame,
    df_cat: pd.DataFrame,
    df_forn: pd.DataFrame,
    df_rup: pd.DataFrame,
) -> None:
    """Exibe no console os relatórios formatados de forma visual e intuitiva."""
    largura = 85
    linha_dupla = "=" * largura
    linha_simples = "-" * largura

    montante_total = df["valor_total"].sum()
    unidades_totais = df["estoque"].sum()
    total_skus = len(df)
    preco_medio_geral = df["preco"].mean()

    print(linha_dupla)
    print(" PAINEL EXECUTIVO: ANÁLISE DE ESTOQUE E MÉTRICAS DE NEGÓCIO")
    print(linha_dupla)

    print("\n[1] RESUMO FINANCEIRO GERAL:")
    print(f"  - Total de SKUs Cadastrados        : {total_skus}")
    print(f"  - Quantidade Física Total em Estoque: {unidades_totais:,} unidades")
    print(f"  - Preço Médio Geral dos Produtos   : {formatar_moeda(preco_medio_geral)}")
    print(f"  - Capital Financeiro Total Retido  : {formatar_moeda(montante_total)}")

    print(f"\n{linha_simples}")
    print("[2] VISÃO POR CATEGORIA DE PRODUTOS:")
    print(linha_simples)
    cabecalho_cat = f"{'Categoria':<18} | {'SKUs':<5} | {'Unidades':<9} | {'Preço Médio':<14} | {'Valor Retido':<16} | {'Part. %':<7}"
    print(cabecalho_cat)
    print(linha_simples)
    for _, row in df_cat.iterrows():
        print(
            f"{row['categoria']:<18} | "
            f"{row['qtd_skus']:<5} | "
            f"{row['unidades_estoque']:<9} | "
            f"{formatar_moeda(row['preco_medio']):<14} | "
            f"{formatar_moeda(row['valor_total_estoque']):<16} | "
            f"{row['participacao_valor_pct']:>6.2f}%"
        )
    print(linha_simples)

    print(f"\n{linha_simples}")
    print("[3] VISÃO POR FORNECEDOR:")
    print(linha_simples)
    cabecalho_forn = f"{'Fornecedor':<15} | {'SKUs':<5} | {'Unidades':<9} | {'Preço Médio':<14} | {'Valor Retido':<16} | {'Part. %':<7}"
    print(cabecalho_forn)
    print(linha_simples)
    for _, row in df_forn.iterrows():
        print(
            f"{row['fornecedor']:<15} | "
            f"{row['qtd_skus']:<5} | "
            f"{row['unidades_estoque']:<9} | "
            f"{formatar_moeda(row['preco_medio']):<14} | "
            f"{formatar_moeda(row['valor_total_estoque']):<16} | "
            f"{row['participacao_valor_pct']:>6.2f}%"
        )
    print(linha_simples)

    print(f"\n{linha_simples}")
    print(f"[4] ALERTA DE RUPTURA DE ESTOQUE (PRODUTOS ZERADOS - TOTAL: {len(df_rup)}):")
    print(linha_simples)
    cabecalho_rup = f"{'ID':<8} | {'Produto':<38} | {'Categoria':<16} | {'Fornecedor':<14} | {'Preço':<12}"
    print(cabecalho_rup)
    print(linha_simples)
    for _, row in df_rup.iterrows():
        print(
            f"{row['id_produto']:<8} | "
            f"{row['produto']:<38} | "
            f"{row['categoria']:<16} | "
            f"{row['fornecedor']:<14} | "
            f"{formatar_moeda(row['preco']):<12}"
        )
    print(linha_simples)
    print(linha_dupla)


def salvar_kpis_categoria(df_cat: pd.DataFrame, caminho_saida: Path) -> None:
    """Salva a tabela de KPIs por categoria em formato CSV."""
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df_cat.to_csv(caminho_saida, index=False, encoding="utf-8")
    print(f"\n[OK] Arquivo de KPIs por categoria salvo com sucesso em:\n     -> {caminho_saida.resolve()}\n")


def main() -> None:
    """Orquestra a carga, cálculos analíticos, exibição e exportação."""
    diretorio_raiz = Path(__file__).parent
    caminho_dados_limpos = diretorio_raiz / "dados_processados" / "estoque_consolidado_limpo.csv"
    caminho_saida_kpis = diretorio_raiz / "dados_processados" / "resumo_kpis_categoria.csv"

    try:
        # 1. Leitura
        df_estoque = carregar_estoque_consolidado(caminho_dados_limpos)

        # 2. Cálculos Financeiros
        df_estoque = calcular_coluna_valor_total(df_estoque)

        # 3. Análises Agrupadas
        df_kpi_categoria = analisar_por_categoria(df_estoque)
        df_kpi_fornecedor = analisar_por_fornecedor(df_estoque)

        # 4. Detecção de Rupturas
        df_rupturas = identificar_rupturas(df_estoque)

        # 5. Exibição no Console
        imprimir_relatorio_terminal(
            df=df_estoque,
            df_cat=df_kpi_categoria,
            df_forn=df_kpi_fornecedor,
            df_rup=df_rupturas,
        )

        # 6. Exportação do Arquivo de KPIs por Categoria
        salvar_kpis_categoria(df_kpi_categoria, caminho_saida_kpis)

    except FileNotFoundError as fnf_err:
        print(f"\n[ERRO DE ARQUIVO]: {fnf_err}", file=sys.stderr)
        sys.exit(1)
    except Exception as err:
        print(f"\n[ERRO INESPERADO]: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
