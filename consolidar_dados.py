import os
import glob
import pandas as pd


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
OUTPUT_MASTER = os.path.join(BASE_DIR, 'data', 'master_dataset_veiculos.csv')

def consolidar_csvs():
    print("Iniciando consolidação de dados da camada Gold...")
    

    padrao_busca = os.path.join(PROCESSED_DIR, "*_processed.csv")
    arquivos_csv = glob.glob(padrao_busca)
    
    if not arquivos_csv:
        print("[ERRO] Nenhum arquivo processado encontrado na pasta data/processed.")
        return

    lista_dfs = []
    
    for arquivo in arquivos_csv:

        nome_arquivo = os.path.basename(arquivo)
        modelo = nome_arquivo.replace("yt_", "").replace("_processed.csv", "")
        
        try:
            df = pd.read_csv(arquivo)
            df['modelo_veiculo'] = modelo  # Adiciona a dimensão do carro
            lista_dfs.append(df)
            print(f" -> {modelo}: {len(df)} registros válidos carregados.")
        except Exception as e:
            print(f" [ERRO] Falha ao ler {nome_arquivo}: {e}")


    df_master = pd.concat(lista_dfs, ignore_index=True)
    

    df_master.dropna(subset=['aspecto_chave', 'sentimento_produto'], inplace=True)
    

    df_master.to_csv(OUTPUT_MASTER, index=False, encoding='utf-8-sig')
    
    print("\n=======================================================")
    print(f"[SUCESSO] Dataset Master gerado com sucesso!")
    print(f"Total de registros consolidados: {len(df_master)}")
    print(f"Arquivo salvo em: {OUTPUT_MASTER}")

if __name__ == "__main__":
    consolidar_csvs()