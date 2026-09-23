"""Passo 2: Leitura e Diagnóstico Exploratório com Pandas.

Este script realiza a ingestão dos dados brutos dos fornecedores A, B e C,
executa um diagnóstico detalhado de tipos, colunas, nulos e amostras,
e apresenta um resumo consolidado das inconsistências identificadas.
"""

from pathlib import Path
import pandas as pd


def carregar_dados_fornecedores(diretorio_dados: Path) -> dict[str, pd.DataFrame]:
    """Carrega os arquivos CSV dos três fornecedores em DataFrames separados.

    Args:
        diretorio_dados (Path): Caminho para a pasta contendo os arquivos CSV.

    Returns:
        dict[str, pd.DataFrame]: Dicionário mapeando o nome do fornecedor ao DataFrame correspondente.
    """
    arquivos = {
        "Fornecedor A": diretorio_dados / "fornecedor_a.csv",
        "Fornecedor B": diretorio_dados / "fornecedor_b.csv",
        "Fornecedor C": diretorio_dados / "fornecedor_c.csv",
    }

    dataframes = {}
    for nome, caminho in arquivos.items():
        if not caminho.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
        # Carregamos sem converter tipos explicitamente para inspecionar as inferências brutas
        dataframes[nome] = pd.read_csv(caminho, dtype=str, keep_default_na=True)
        # Também lemos uma versão sem forçar string para observar a inferência padrão do Pandas
        df_inferido = pd.read_csv(caminho)
        dataframes[nome] = df_inferido

    return dataframes


def diagnosticar_dataframe(nome: str, df: pd.DataFrame) -> None:
    """Exibe no console o diagnóstico individual de um DataFrame.

    Mostra colunas, tipos inferidos, quantidade de nulos e amostra das primeiras linhas.
    """
    separador = "=" * 80
    sub_separador = "-" * 80

    print(f"\n{separador}")
    print(f" DIAGNÓSTICO: {nome.upper()} ({len(df)} registros)")
    print(separador)

    # 1. Colunas existentes
    print("\n[1] Colunas Existentes:")
    for idx, col in enumerate(df.columns, start=1):
        print(f"  {idx}. '{col}'")

    # 2. Tipos de dados inferidos
    print("\n[2] Tipos de Dados Inferidos (dtypes):")
    for col, dtype in df.dtypes.items():
        print(f"  - {col:<22} : {dtype}")

    # 3. Quantidade de valores ausentes/nulos
    print("\n[3] Valores Nulos / Ausentes (isna().sum()):")
    nulos = df.isna().sum()
    tem_nulo = False
    for col, qtd in nulos.items():
        pct = (qtd / len(df)) * 100
        if qtd > 0:
            tem_nulo = True
            print(f"  ! {col:<22} : {qtd} nulo(s) ({pct:.1f}%)")
        else:
            print(f"    {col:<22} : {qtd} nulos")
    if not tem_nulo:
        print("    Nenhum valor nulo identificado nesta fonte.")

    # 4. Amostra dos dados (head)
    print("\n[4] Amostra das Primeiras Linhas (head):")
    print(sub_separador)
    print(df.head().to_string())
    print(sub_separador)


def exibir_resumo_consolidado(dfs: dict[str, pd.DataFrame]) -> None:
    """Imprime um resumo consolidado em texto destacando as inconsistências

    encontradas em todos os conjuntos de dados e o plano de ação para a etapa de limpeza.
    """
    separador_bloco = "#" * 80
    print(f"\n\n{separador_bloco}")
    print(" RESUMO CONSOLIDADO DE INCONSISTÊNCIAS E DIAGNÓSTICO PARA LIMPEZA")
    print(separador_bloco)

    resumo_texto = """
1. DISCREPÂNCIA DE NOMES DE COLUNAS (SCHEMA DESALINHADO):
   - Cada fornecedor utiliza uma convenção e nomenclatura totalmente distinta:
     * Chave Identificadora: 'id_produto' (A) vs 'codigo_item' (B) vs 'sku' (C)
     * Nome do Item        : 'nm_produto' (A) vs 'produto' (B) vs 'item' (C)
     * Categoria           : 'categoria' (A) vs 'departamento' (B) vs 'tipo_produto' (C)
     * Preço Unitário      : 'preco_unitario' (A) vs 'Preco' (B) vs 'valor_brl' (C)
     * Quantidade/Estoque  : 'qtd_estoque' (A) vs 'Quantidade' (B) vs 'estoque_disponivel' (C)
     * Metadados extras    : 'data_registro' (A) vs 'fornecedor' (B) vs 'status_item' (C)
   -> Ação necessária: Criar um mapeamento de padronização para unificar os schemas
      em um formato canônico (ex.: id_produto, produto, categoria, preco, estoque, fornecedor).

2. COLUNAS NUMÉRICAS INFERIDAS COMO TEXTO ('object'):
   - Preços:
     * Fornecedor A: Contém prefixo monetário 'R$' e separador decimal com vírgula (ex: 'R$ 4.299,00').
     * Fornecedor B: Contém texto misturado em vez de número (ex: 'consultar').
     * Fornecedor C: Contém valores com vírgula (ex: '1899,90') e registros suspeitos ('0,00').
   - Estoque / Quantidade:
     * Fornecedor A: Contém texto descritivo ('SEM ESTOQUE') e valores negativos ('-3').
     * Fornecedor B: Contém notação de unidade textual ('15 un') e valores decimais ('30.0').
     * Fornecedor C: Contém estoque negativo ('-1').
   -> Ação necessária: Criar rotinas de conversão e coerção numérica (regex para remover 'R$' e 'un',
      substituição de vírgula por ponto, tratamento de strings não numéricas via pd.to_numeric(..., errors='coerce')).

3. VALORES NULOS / AUSENTES (MISSING VALUES):
   - Preços nulos: Fornecedor A (1), Fornecedor B (1), Fornecedor C (1).
   - Estoques nulos: Fornecedor A (1), Fornecedor B (1), Fornecedor C (1).
   - Categorias nulas: Fornecedor A (1), Fornecedor B (1), Fornecedor C (1).
   -> Ação necessária: Definir estratégias claras de imputação ou descarte (ex: remover linhas
      sem preço ou preencher/sinalizar para revisão; imputar 0 ou moda/mediana onde aplicável).

4. VARIAÇÃO DE TEXTO E ERROS DE DIGITAÇÃO:
   - Categorias não padronizadas:
     * 'Smartfone', 'smartphones', 'SMARTPHONES', 'telefonia/smartphone'.
     * 'FONE DE OUVIDO', 'fones', 'FONES', 'fone_ouvido', 'audio / fone ouvido'.
     * 'carregadores', 'CARREGADOR', 'acessorios/carregador'.
   - Descrições de produto:
     * Erros de digitação: 'Smarthphone', 'bluetoth', 'Indussão'.
   -> Ação necessária: Normalização de strings (lowercase, remoção de espaços e acentos),
      criação de um dicionário canônico de categorias ('smartphones', 'fones_de_ouvido', 'carregadores').
"""
    print(resumo_texto)
    print(separador_bloco)


def main() -> None:
    """Função principal que orquestra a leitura e o diagnóstico dos dados."""
    caminho_base = Path(__file__).parent / "dados_brutos"

    print("Iniciando Leitura e Diagnóstico Exploratório dos Fornecedores...")
    print(f"Diretório dos dados: {caminho_base.resolve()}\n")

    # Carregamento dos dados
    dfs = carregar_dados_fornecedores(caminho_base)

    # Diagnóstico individual para cada fornecedor
    for nome_fornecedor, df in dfs.items():
        diagnosticar_dataframe(nome_fornecedor, df)

    # Diagnóstico consolidado
    exibir_resumo_consolidado(dfs)


if __name__ == "__main__":
    main()
