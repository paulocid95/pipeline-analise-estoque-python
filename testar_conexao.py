import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

print("Tentando conectar ao PostgreSQL no Neon...")

try:
    engine = create_engine(database_url)
    with engine.connect() as conexao:
        resultado = conexao.execute(text("SELECT version();"))
        print("\nConexão realizada com sucesso!")
        print(f"Versão do Banco: {resultado.fetchone()[0]}")
except Exception as e:
    print(f"\nErro ao conectar: {e}")