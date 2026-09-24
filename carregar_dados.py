import glob
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 1. Carregar variáveis de ambiente do arquivo .env
load_dotenv()
database_url = os.getenv("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url)


def carregar_pipeline():
    # 2. Localizar o arquivo processado mais recente
    arquivos = glob.glob("dados_processados/*.csv")
    if not arquivos:
        print("Erro: Nenhum arquivo encontrado na pasta dados_processados/")
        return

    caminho_arquivo = arquivos[0]
    print(f"Lendo dados limpos de: {caminho_arquivo}")
    df = pd.read_csv(caminho_arquivo)

    # 3. Engenharia de atributos e regras de negócio para a tabela fato
    df["preco"] = pd.to_numeric(df["preco"], errors="coerce").fillna(0.0)
    df["estoque"] = pd.to_numeric(df["estoque"], errors="coerce").fillna(0).astype(int)
    df["valor_total"] = (df["preco"] * df["estoque"]).round(2)

    def classificar_status(qtd):
        if qtd == 0:
            return "CRITICO"
        elif qtd <= 15:
            return "ALERTA"
        elif qtd > 100:
            return "EXCESSO"
        return "NORMAL"

    df["status_reposicao"] = df["estoque"].apply(classificar_status)

    print("Iniciando transação de carga no PostgreSQL...")

    with engine.begin() as conexao:
        # 4. Inserir Categorias (dim_categorias)
        categorias_unicas = df["categoria"].dropna().unique().tolist()
        for cat in categorias_unicas:
            conexao.execute(
                text("""
                    INSERT INTO core.dim_categorias (nome_categoria)
                    VALUES (:nome)
                    ON CONFLICT (nome_categoria) DO NOTHING;
                """),
                {"nome": str(cat).strip()},
            )

        # Criar mapa em memória: nome_categoria -> id_categoria
        resultado_cats = conexao.execute(
            text("SELECT id_categoria, nome_categoria FROM core.dim_categorias;")
        ).fetchall()
        mapa_categorias = {nome: id_cat for id_cat, nome in resultado_cats}

        # 5. Inserir / Atualizar Produtos (dim_produtos)
        for _, linha in df.iterrows():
            id_cat = mapa_categorias.get(str(linha["categoria"]).strip())
            sku_val = str(linha["id_produto"]).strip()

            conexao.execute(
                text("""
                    INSERT INTO core.dim_produtos (sku, nome_produto, id_categoria, preco_unitario, estoque_minimo)
                    VALUES (:sku, :nome, :id_cat, :preco, 10)
                    ON CONFLICT (sku) DO UPDATE SET
                        nome_produto = EXCLUDED.nome_produto,
                        id_categoria = EXCLUDED.id_categoria,
                        preco_unitario = EXCLUDED.preco_unitario;
                """),
                {
                    "sku": sku_val,
                    "nome": str(linha["produto"]).strip(),
                    "id_cat": id_cat,
                    "preco": float(linha["preco"]),
                },
            )

        # Criar mapa em memória: sku -> id_produto_banco
        resultado_prods = conexao.execute(
            text("SELECT id_produto, sku FROM core.dim_produtos;")
        ).fetchall()
        mapa_produtos = {sku: id_prod for id_prod, sku in resultado_prods}

        # 6. Inserir registros na Tabela Fato (fato_estoque)
        for _, linha in df.iterrows():
            sku_val = str(linha["id_produto"]).strip()
            id_prod_banco = mapa_produtos.get(sku_val)

            if id_prod_banco:
                conexao.execute(
                    text("""
                        INSERT INTO core.fato_estoque 
                        (id_produto, quantidade_disponivel, valor_total_estoque, status_reposicao)
                        VALUES (:id_prod, :qtd, :val_total, :status);
                    """),
                    {
                        "id_prod": id_prod_banco,
                        "qtd": int(linha["estoque"]),
                        "val_total": float(linha["valor_total"]),
                        "status": linha["status_reposicao"],
                    },
                )

    print("Carga concluída com sucesso no schema 'core'!")


if __name__ == "__main__":
    carregar_pipeline()