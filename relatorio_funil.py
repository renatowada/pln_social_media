import os
import glob
import pandas as pd

# CONFIGURAÇÃO DE CAMINHOS
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
OUTPUT_FUNIL = os.path.join(BASE_DIR, 'data', 'relatorio_funil_IA.csv')

def extrair_info_arquivo(nome_arquivo):
    """Extrai a fonte e o nome do modelo com base no padrão do arquivo."""
    fonte = "Desconhecida"
    modelo = nome_arquivo.replace(".csv", "").replace(".parquet", "")
    
    if "yt_" in nome_arquivo:
        fonte = "YouTube"
        modelo = modelo.replace("yt_raw_", "").replace("yt_", "").replace("_processed", "")
    elif "reddit_" in nome_arquivo:
        fonte = "Reddit"
        modelo = modelo.replace("reddit_raw_", "").replace("reddit_", "").replace("_processed", "")
        
    return fonte, modelo

def gerar_relatorio():
    print("Analisando volumes de dados (Raw vs Processed)...")
    dados_funil = {}

    for ext in ["*.csv", "*.parquet"]:
        for arquivo in glob.glob(os.path.join(RAW_DIR, ext)):
            nome = os.path.basename(arquivo)
            
            # Pula os arquivos 'apify_' para evitar contagem dupla (usamos os normalizados reddit_raw)
            if nome.startswith("apify_"):
                continue
                
            try:
                df = pd.read_csv(arquivo) if arquivo.endswith('.csv') else pd.read_parquet(arquivo)
                fonte, modelo = extrair_info_arquivo(nome)
                chave = f"{fonte}_{modelo}"
                
                if chave not in dados_funil:
                    dados_funil[chave] = {'Fonte': fonte, 'Modelo': modelo, 'Total_Bruto_Extraido': 0, 'Total_Util_IA': 0}
                
                dados_funil[chave]['Total_Bruto_Extraido'] += len(df)
            except Exception as e:
                print(f" [ERRO] Falha ao ler raw {nome}: {e}")

    for arquivo in glob.glob(os.path.join(PROCESSED_DIR, "*.csv")):
        nome = os.path.basename(arquivo)
        try:
            df = pd.read_csv(arquivo)
            fonte, modelo = extrair_info_arquivo(nome)
            chave = f"{fonte}_{modelo}"
            
            if chave not in dados_funil:
                dados_funil[chave] = {'Fonte': fonte, 'Modelo': modelo, 'Total_Bruto_Extraido': 0, 'Total_Util_IA': 0}
            
            dados_funil[chave]['Total_Util_IA'] += len(df)
        except Exception as e:
            print(f" [ERRO] Falha ao ler processed {nome}: {e}")

    df_funil = pd.DataFrame(list(dados_funil.values()))
    
    if not df_funil.empty:
        df_funil['Taxa_Sinal_Ruido (%)'] = round((df_funil['Total_Util_IA'] / df_funil['Total_Bruto_Extraido']) * 100, 1)
        
        df_funil = df_funil.sort_values(by=['Fonte', 'Modelo']).reset_index(drop=True)
        
        print("\n=== RELATÓRIO DE RETENÇÃO DO GEMINI ===")
        print(df_funil.to_string(index=False))
        
        df_funil.to_csv(OUTPUT_FUNIL, index=False, encoding='utf-8-sig')
        print(f"\n[SUCESSO] Relatório de funil exportado para: {OUTPUT_FUNIL}")
    else:
        print("\n[AVISO] Nenhum dado encontrado para gerar o relatório.")

if __name__ == "__main__":
    gerar_relatorio()