"""Passo 3: Pipeline de Limpeza, Padronização e Tratamento de Dados com Pandas.

Este script executa:
1. Padronização de schema para o padrão canônico (id_produto, produto, categoria, preco, estoque, fornecedor).
2. Sanitização e conversão de dados numéricos (preço em float, estoque em int não-negativo).
3. Normalização textual e classificação inteligente em 3 categorias canônicas.
4. Tratamento transparente de valores ausentes (imputação e descarte justificado com logs).
5. Consolidação e exportação para 'dados_processados/estoque_consolidado_limpo.csv'.
6. Exibição de comparativo antes vs. depois no console.
"""

from pathlib import Path
import re
import numpy as np
import pandas as pd


# ==============================================================================
# CONFIGURAÇÃO DE COLUNAS CANÔNICAS E MAPEAMENTOS POR FORNECEDOR
# ==============================================================================
COLUNAS_CANONICAS = ["id_produto", "produto", "categoria", "preco", "estoque", "fornecedor"]

MAPEAMENTO_SCHEMAS = {
    "Fornecedor A": {
        "arquivo": "fornecedor_a.csv",
        "fornecedor_nome": "Fornecedor A",
        "de_para": {
            "id_produto": "id_produto",
            "nm_produto": "produto",
            "categoria": "categoria",
            "preco_unitario": "preco",
            "qtd_estoque": "estoque",
        },
    },
    "Fornecedor B": {
        "arquivo": "fornecedor_b.csv",
        "fornecedor_nome": "Fornecedor B",
        "de_para": {
            "codigo_item": "id_produto",
            "produto": "produto",
            "departamento": "categoria",
            "Preco": "preco",
            "Quantidade": "estoque",
            "fornecedor": "fornecedor",
        },
    },
    "Fornecedor C": {
        "arquivo": "fornecedor_c.csv",
        "fornecedor_nome": "Fornecedor C",
        "de_para": {
            "sku": "id_produto",
            "item": "produto",
            "tipo_produto": "categoria",
            "valor_brl": "preco",
            "estoque_disponivel": "estoque",
        },
    },
}

CATEGORIAS_OFICIAIS = ["Smartphones", "Fones de Ouvido", "Carregadores"]


# ==============================================================================
# FUNÇÕES DE TRATAMENTO E SANITIZAÇÃO
# ==============================================================================
def sanitizar_preco(serie: pd.Series) -> pd.Series:
    """Higieniza e converte uma série de preços para float.

    - Remove prefixos como 'R$' e espaços.
    - Trata pontos de milhar e vírgulas decimais (formato brasileiro).
    - Força coerção para float (converte textos como 'consultar' em NaN).
    - Converte valores <= 0 em NaN (considerados inválidos).
    """
    # Converte para string e limpa espaços
    s = serie.astype(str).str.strip()

    # Normaliza representações de nulos em string
    s = s.replace(["nan", "None", "<NA>", ""], np.nan)

    # Remove símbolo de moeda e caracteres não numéricos exceto ponto e vírgula
    s = s.str.replace(r"R\$\s*", "", regex=True)

    # Se contiver ponto de milhar seguido de vírgula decimal (ex: 4.299,00), remove o ponto
    s = s.str.replace(r"\.(?=\d{3}(,|$))", "", regex=True)

    # Substitui a vírgula decimal pelo ponto padrão do Python
    s = s.str.replace(",", ".", regex=False)

    # Coerção numérica segura
    precos = pd.to_numeric(s, errors="coerce")

    # Regra de negócio: preços zerados ou negativos são inválidos
    precos = precos.mask(precos <= 0, np.nan)

    return precos


def sanitizar_estoque(serie: pd.Series) -> pd.Series:
    """Higieniza e converte uma série de estoque para inteiros não-negativos.

    - Substitui 'SEM ESTOQUE', nulos e vazios por 0.
    - Remove sufixos de texto (ex: 'un', 'unidades').
    - Coerção numérica para float inicial (suporta '30.0') e depois inteiro.
    - Converte estoques negativos para 0 (registrando como inconsistência tratada).
    """
    s = serie.astype(str).str.strip().str.lower()

    # Mapeia valores nulos ou indicativos de indisponibilidade para '0'
    s = s.replace({
        "sem estoque": "0",
        "nan": "0",
        "none": "0",
        "<na>": "0",
        "": "0"
    })

    # Extrai apenas dígitos, ponto e sinal de menos
    s = s.str.replace(r"[^\d\-.]", "", regex=True)

    # Coerção numérica e preenchimento de falhas com 0
    numeros = pd.to_numeric(s, errors="coerce").fillna(0)

    # Garante que valores negativos sejam convertidos para 0
    numeros = numeros.clip(lower=0)

    return numeros.astype(int)


def deduzir_categoria(produto: str, categoria_original: str) -> str:
    """Classifica o produto em uma das 3 categorias oficiais.

    Utiliza mapeamento das categorias originais e, caso nula ou ambígua,
    deduz através de padrões textuais (regex/keywords) presentes no nome do produto.
    """
    cat = str(categoria_original).strip().lower() if pd.notna(categoria_original) else ""
    prod = str(produto).strip().lower() if pd.notna(produto) else ""

    # 1. Tentativa por palavras-chave na categoria original
    if any(k in cat for k in ["smart", "celular", "telefonia"]):
        return "Smartphones"
    if any(k in cat for k in ["fone", "headphone", "headset", "earbud", "audio"]):
        return "Fones de Ouvido"
    if any(k in cat for k in ["carregador", "cabo", "acessorio"]):
        return "Carregadores"

    # 2. Deduzir a partir do nome do produto (para categorias nulas ou mal formatadas)
    if any(k in prod for k in ["galaxy", "iphone", "smartfone", "smartphone", "edge", "redmi", "poco", "zenfone", "moto"]):
        return "Smartphones"
    if any(k in prod for k in ["fone", "headphone", "headset", "earbud", "air dots", "tws", "audio", "bluetoth", "bluetooth"]):
        return "Fones de Ouvido"
    if any(k in prod for k in ["carregador", "power bank", "magsafe", "cabo", "lightning", "fonte", "indussão", "indução"]):
        return "Carregadores"

    return "Outros"


# ==============================================================================
# PIPELINE DE TRATAMENTO POR DATASET
# ==============================================================================
def processar_fornecedor(chave: str, config: dict, diretorio_dados: Path) -> tuple[pd.DataFrame, dict]:
    """Lê, padroniza e higieniza os dados de um fornecedor individualmente.

    Retorna o DataFrame limpo e um dicionário de métricas do processo.
    """
    caminho = diretorio_dados / config["arquivo"]
    df_raw = pd.read_csv(caminho, dtype=str)
    qtd_inicial = len(df_raw)

    print(f"\n--- Processando {chave} ({qtd_inicial} registros brutos) ---")

    # 1. Renomeação para Schema Canônico
    df = df_raw.rename(columns=config["de_para"])

    # 2. Garantir coluna de identificação de fornecedor
    if "fornecedor" not in df.columns or df["fornecedor"].isna().all():
        df["fornecedor"] = config["fornecedor_nome"]
    else:
        df["fornecedor"] = df["fornecedor"].fillna(config["fornecedor_nome"]).str.strip()

    # 3. Manter apenas colunas do padrão canônico
    df = df[COLUNAS_CANONICAS].copy()

    # 4. Normalização textual do nome do produto
    df["produto"] = df["produto"].astype(str).str.strip()
    # Remove espaços duplos
    df["produto"] = df["produto"].str.replace(r"\s+", " ", regex=True)

    # 5. Tratamento de Categorias (com dedução inteligente)
    categorias_antes_nulas = df["categoria"].isna().sum()
    df["categoria"] = [
        deduzir_categoria(p, c) for p, c in zip(df["produto"], df["categoria"])
    ]
    print(f"  [OK] Categorias normalizadas (Deduções aplicadas: {categorias_antes_nulas})")

    # 6. Sanitização de Estoque
    estoques_negativos = (pd.to_numeric(df["estoque"].str.replace(r"[^\d\-.]", "", regex=True), errors="coerce") < 0).sum()
    df["estoque"] = sanitizar_estoque(df["estoque"])
    print(f"  [OK] Estoques sanitizados (Negativos ajustados para 0: {estoques_negativos})")

    # 7. Sanitização de Preço
    precos_brutos = df["preco"].copy()
    df["preco"] = sanitizar_preco(df["preco"])

    # 8. Tratamento de Nulos em Preço (Descarte justificado)
    linhas_sem_preco = df["preco"].isna()
    qtd_descarte_preco = linhas_sem_preco.sum()

    if qtd_descarte_preco > 0:
        produtos_descartados = df.loc[linhas_sem_preco, "produto"].tolist()
        precos_originais = precos_brutos[linhas_sem_preco].tolist()
        print(f"  [ALERTA] Descartando {qtd_descarte_preco} registro(s) sem preço válido (<= 0 ou texto não-conversível):")
        for p, pr in zip(produtos_descartados, precos_originais):
            print(f"    - Produto: '{p}' | Preço Original: '{pr}'")
        df = df[~linhas_sem_preco].copy()

    # Arredonda preço para 2 casas decimais
    df["preco"] = df["preco"].round(2)

    metricas = {
        "qtd_inicial": qtd_inicial,
        "qtd_final": len(df),
        "descartes_preco": qtd_descarte_preco,
        "categorias_deduzidas": categorias_antes_nulas,
        "estoques_negativos_ajustados": estoques_negativos,
    }

    return df, metricas


# ==============================================================================
# FUNÇÃO PRINCIPAL / ORQUESTRADOR
# ==============================================================================
def main() -> None:
    diretorio_raiz = Path(__file__).parent
    diretorio_dados_brutos = diretorio_raiz / "dados_brutos"
    diretorio_processados = diretorio_raiz / "dados_processados"
    diretorio_processados.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(" INICIANDO PIPELINE DE LIMPEZA E PADRONIZAÇÃO DE DADOS")
    print("=" * 80)

    dataframes_limpos = []
    total_linhas_brutas = 0
    metricas_consolidadas = []

    # Processar cada fornecedor isoladamente
    for chave, config in MAPEAMENTO_SCHEMAS.items():
        df_limpo, metrica = processar_fornecedor(chave, config, diretorio_dados_brutos)
        dataframes_limpos.append(df_limpo)
        total_linhas_brutas += metrica["qtd_inicial"]
        metricas_consolidadas.append((chave, metrica))

    # Concatenação e consolidação
    df_consolidado = pd.concat(dataframes_limpos, ignore_index=True)

    # Ordenação canônica para leitura limpa
    df_consolidado = df_consolidado.sort_values(by=["categoria", "fornecedor", "id_produto"]).reset_index(drop=True)

    # Exportação para CSV limpo
    caminho_saida = diretorio_processados / "estoque_consolidado_limpo.csv"
    df_consolidado.to_csv(caminho_saida, index=False, encoding="utf-8")
    print(f"\n[SUCESSO] Arquivo consolidado salvo em: {caminho_saida}")

    # ==============================================================================
    # RESUMO COMPARATIVO ANTES VS DEPOIS
    # ==============================================================================
    total_linhas_finais = len(df_consolidado)
    nulos_finais = df_consolidado.isna().sum().sum()

    print("\n" + "=" * 80)
    print(" RELATÓRIO COMPARATIVO: ANTES (BRUTO) VS DEPOIS (TRATADO)")
    print("=" * 80)
    print(f"Total de Registros Brutos Ingeridos  : {total_linhas_brutas}")
    print(f"Total de Registros Validados e Salvos: {total_linhas_finais}")
    print(f"Total de Registros Descartados (Preço): {total_linhas_brutas - total_linhas_finais}")
    print(f"Total de Valores Nulos Restantes     : {nulos_finais}")

    print("\n[Dtypes Finais do DataFrame Consolidado]:")
    for col, dtype in df_consolidado.dtypes.items():
        print(f"  - {col:<15} : {dtype}")

    print("\n[Distribuição de Registros por Categoria Canônica]:")
    for cat, count in df_consolidado["categoria"].value_counts().items():
        print(f"  - {cat:<20} : {count} itens")

    print("\n[Distribuição de Registros por Fornecedor]:")
    for forn, count in df_consolidado["fornecedor"].value_counts().items():
        print(f"  - {forn:<20} : {count} itens")

    print("\n[Amostra dos Dados Tratados (Primeiras 10 Linhas)]:")
    print("-" * 80)
    print(df_consolidado.head(10).to_string(index=False))
    print("-" * 80)
    print("=" * 80)


if __name__ == "__main__":
    main()
