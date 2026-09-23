import os
import csv
from pathlib import Path

def criar_dados_fornecedores():
    # Define diretório de saída
    pasta_destino = Path(__file__).parent / "dados_brutos"
    pasta_destino.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # FORNECEDOR A
    # Colunas: id_produto, nm_produto, categoria, preco_unitario, qtd_estoque, data_registro
    # Inconsistências: 'R$' e vírgulas nos preços, categorias com erros e caixa mista,
    # valores nulos, strings no estoque ('SEM ESTOQUE', '-5')
    # -------------------------------------------------------------
    dados_fornecedor_a = [
        ["id_produto", "nm_produto", "categoria", "preco_unitario", "qtd_estoque", "data_registro"],
        ["FA001", "Smarthphone Samsung Galaxy S23 128GB", "Smartfone", "R$ 4.299,00", "15", "2026-01-10"],
        ["FA002", "iPhone 14 128GB Estelar", "smartphones", "R$ 4.899,90", "8", "2026-01-11"],
        ["FA003", "Fone Bluetooth sem Fio Intra-auricular", "FONE DE OUVIDO", "R$ 149,90", "42", "2026-01-11"],
        ["FA004", "Carregador Turbo 30W USB-C", "carregadores", "R$ 89,90", "120", "2026-01-12"],
        ["FA005", "Smartfone Motorola Moto G84 5G", "Smartfone", "", "25", "2026-01-12"],  # Preço nulo
        ["FA006", "Headphone Bluetooth com Cancelamento Ruido", "fones", "R$ 389,00", "-3", "2026-01-13"],  # Estoque negativo
        ["FA007", "Carregador Indução MagSafe", "Carregadores", "R$ 199,99", "SEM ESTOQUE", "2026-01-14"],  # Estoque texto
        ["FA008", "Xiaomi Redmi Note 13", "smartphones", "R$ 1.350,00", None, "2026-01-14"],  # Estoque nulo
        ["FA009", "Fone de Ouvido P2 Basico", None, "R$ 29,90", "80", "2026-01-15"],  # Categoria nula
        ["FA010", "Carregador Portatil Power Bank 10000mAh", "carregador", "R$ 129,00", "0", "2026-01-15"],
    ]

    arquivo_a = pasta_destino / "fornecedor_a.csv"
    with open(arquivo_a, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(dados_fornecedor_a)
    print(f"[OK] Arquivo gerado: {arquivo_a}")

    # -------------------------------------------------------------
    # FORNECEDOR B
    # Colunas: codigo_item, produto, departamento, Preco, Quantidade, fornecedor
    # Inconsistências: nomes de colunas diferentes, preços misturando ponto e texto ('consultar'),
    # categorias em maiúsculas e abreviações, quantidades decimais ('10.0', '15 un')
    # -------------------------------------------------------------
    dados_fornecedor_b = [
        ["codigo_item", "produto", "departamento", "Preco", "Quantidade", "fornecedor"],
        ["B-101", "Galaxy A54 5G 256GB", "SMARTPHONES", "1799.00", "12", "Fornecedor B"],
        ["B-102", "Apple iPhone 13 128GB Meia-Noite", "SMARTPHONE", "3699.50", "5", "Fornecedor B"],
        ["B-103", "Fone TWS Air Dots 3", "FONES", "119.90", "30.0", "Fornecedor B"],  # Qtd float
        ["B-104", "Fonte Carregador 20W Tipo-C", "CARREGADOR", "45.00", "100", "Fornecedor B"],
        ["B-105", "Smarthfone Xiaomi Poco X6 Pro", "SMARTPHONES", "consultar", "8", "Fornecedor B"],  # Preço texto
        ["B-106", "Headset Gamer 7.1 Surround", "FONE DE OUVIDO", "249.90", "15 un", "Fornecedor B"],  # Qtd com unidade
        ["B-107", "Cabo e Adaptador Turbo 65W", "CARREGADORES", "99.00", "-10", "Fornecedor B"],  # Estoque negativo
        ["B-108", "Fone Esportivo Bluetooth Neckband", None, "79.90", "18", "Fornecedor B"],  # Categoria nula
        ["B-109", "Smartphone Samsung S24 Ultra", "SMARTPHONES", "6899.00", "", "Fornecedor B"],  # Estoque nulo
        ["B-110", "Carregador Veicular Rapido Duplo", "CARREGADOR", None, "45", "Fornecedor B"],  # Preço nulo
    ]

    arquivo_b = pasta_destino / "fornecedor_b.csv"
    with open(arquivo_b, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(dados_fornecedor_b)
    print(f"[OK] Arquivo gerado: {arquivo_b}")

    # -------------------------------------------------------------
    # FORNECEDOR C
    # Colunas: sku, item, tipo_produto, valor_brl, estoque_disponivel, status_item
    # Inconsistências: preços com vírgula sem símbolo ('1299,99'),
    # erros de digitação nos nomes ('Smartfone', 'Indussão', 'bluetoth'),
    # valores zerados inválidos, estoque com valores nulos e negativos
    # -------------------------------------------------------------
    dados_fornecedor_c = [
        ["sku", "item", "tipo_produto", "valor_brl", "estoque_disponivel", "status_item"],
        ["SKU-C01", "Smartfone Motorola Edge 40 Neo", "telefonia/smartphone", "1899,90", "14", "ATIVO"],
        ["SKU-C02", "iPhone 15 Pro Max 256GB Titânio", "smartphone", "7499,00", "4", "ATIVO"],
        ["SKU-C03", "Fone bluetoth cancelamento ativo ANC", "audio / fone ouvido", "329,50", "22", "ATIVO"],
        ["SKU-C04", "Base Carregador Indussão 15W Sem Fio", "acessorios/carregador", "110,00", "50", "ATIVO"],
        ["SKU-C05", "Smarthphone Asus Zenfone 10", "smartphone", "0,00", "3", "EM REVISAO"],  # Preço zero suspeito
        ["SKU-C06", "Earbuds Fone TWS Pro Stereo", "fone_ouvido", "89,90", None, "ATIVO"],  # Estoque nulo
        ["SKU-C07", "Carregador Super Rápido 45W Type-C", "carregadores", "135,00", "-1", "ERRO"],  # Estoque negativo
        ["SKU-C08", "Cabo Lightning Reforcado 1.5m", "carregadores", None, "85", "ATIVO"],  # Preço nulo
        ["SKU-C09", "Smartfone Realme 11 Pro Plus", None, "1999,00", "7", "ATIVO"],  # Categoria nula
        ["SKU-C10", "Headphone Over-Ear Studio Monitor", "audio/fone", "459,99", "11", "ATIVO"],
    ]

    arquivo_c = pasta_destino / "fornecedor_c.csv"
    with open(arquivo_c, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(dados_fornecedor_c)
    print(f"[OK] Arquivo gerado: {arquivo_c}")

if __name__ == "__main__":
    criar_dados_fornecedores()
