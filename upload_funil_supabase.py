import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# CONFIGURAÇÃO DE CAMINHOS
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CSV_FUNIL = os.path.join(BASE_DIR, 'data', 'relatorio_funil_IA.csv')

load_dotenv(os.path.join(BASE_DIR, '.env'))

def enviar_funil_para_supabase():
    print("Iniciando upload do Relatório de Funil para o banco de dados...")
    
    db_uri = os.getenv("SUPABASE_DB_URI")
    if not db_uri:
        print("[ERRO] Variável SUPABASE_DB_URI não encontrada no .env")
        return

    if db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)

    try:
        engine = create_engine(db_uri)
        print(" -> Conexão com Supabase (PostgreSQL) estabelecida.")
    except Exception as e:
        print(f" [ERRO] Falha ao conectar no banco: {e}")
        return

    try:
        df_funil = pd.read_csv(CSV_FUNIL)
        print(f" -> Relatório lido com sucesso. Total de linhas: {len(df_funil)}")
    except Exception as e:
        print(f" [ERRO] Não foi possível ler o arquivo CSV do funil: {e}")
        return

    print(" -> Escrevendo dados na tabela 'relatorio_funil_ia'...")
    try:
        df_funil.to_sql('relatorio_funil_ia', con=engine, if_exists='replace', index=False)
        print("\n[SUCESSO] Relatório de funil inserido com sucesso no Supabase!")
        
    except Exception as e:
        print(f"\n[ERRO] Falha durante a inserção de dados: {e}")

if __name__ == "__main__":
    enviar_funil_para_supabase()