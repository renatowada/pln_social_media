import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'data', 'master_dataset_veiculos.csv')

load_dotenv(os.path.join(BASE_DIR, '.env'))

def enviar_para_supabase():
    print("Iniciando processo de ingestão no banco de dados...")
    

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
        df_master = pd.read_csv(CSV_PATH)
        print(f" -> Arquivo lido. Total de registros para upload: {len(df_master)}")
    except Exception as e:
        print(f" [ERRO] Não foi possível ler o arquivo CSV: {e}")
        return


    print(" -> Escrevendo dados na tabela...")
    try:

        df_master.to_sql('avaliacoes_comentarios', con=engine, if_exists='replace', index=False)
        print("\n[SUCESSO] Todos os dados foram inseridos na tabela 'avaliacoes_comentarios' no Supabase!")
        
    except Exception as e:
        print(f"\n[ERRO] Falha durante a inserção de dados: {e}")

if __name__ == "__main__":
    enviar_para_supabase()