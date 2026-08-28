import os
import glob
import pandas as pd

# CONFIGURAÇÃO DE CAMINHOS
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
OUTPUT_MASTER = os.path.join(BASE_DIR, 'data', 'master_dataset_veiculos.csv')

def consolidar_csvs():
    print("Iniciando consolidação inteligente da camada Gold...")
    
    # Busca todos os arquivos processados (YouTube e Reddit)
    padrao_busca = os.path.join(PROCESSED_DIR, "*_processed.csv")
    arquivos_csv = glob.glob(padrao_busca)
    
    if not arquivos_csv:
        print("[ERRO] Nenhum arquivo processado encontrado na pasta data/processed.")
        return

    lista_dfs = []
    
    for arquivo in arquivos_csv:
        nome_arquivo = os.path.basename(arquivo)
        
        try:
            df = pd.read_csv(arquivo)
            
            if nome_arquivo.startswith("yt_"):
                df['fonte_dados'] = 'YouTube'
                modelo = nome_arquivo.replace("yt_", "").replace("_processed.csv", "")
            elif nome_arquivo.startswith("reddit_"):
                df['fonte_dados'] = 'Reddit'
                modelo = nome_arquivo.replace("reddit_", "").replace("_processed.csv", "")
            else:
                df['fonte_dados'] = 'Desconhecido'
                modelo = nome_arquivo.replace("_processed.csv", "")
            
            df['modelo_veiculo'] = modelo
            
            lista_dfs.append(df)
            print(f" -> [{df['fonte_dados'].iloc[0]}] Modelo: {modelo} | Registros: {len(df)}")
                
        except Exception as e:
            print(f" [ERRO] Falha ao ler {nome_arquivo}: {e}")

    if not lista_dfs:
        print("[ERRO] Nenhum dataframe válido para consolidar.")
        return

    # Concatena todas as fontes em um único Master Dataset
    df_master = pd.concat(lista_dfs, ignore_index=True)
    
    df_master.dropna(subset=['aspecto_chave', 'sentimento_produto'], inplace=True)
    
    df_master.to_csv(OUTPUT_MASTER, index=False, encoding='utf-8-sig')
    
    print("\n=======================================================")
    print(f"[SUCESSO] Master Dataset atualizado e unificado!")
    print(f"Total geral de registros limpos: {len(df_master)}")
    print(f"Arquivo salvo em: {OUTPUT_MASTER}")

if __name__ == "__main__":
    consolidar_csvs()