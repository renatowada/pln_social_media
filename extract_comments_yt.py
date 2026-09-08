import os
import time
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv() # Carrega variáveis de ambiente do arquivo .env

# CONFIGURAÇÕES DO PROJETO

API_KEY = os.getenv("YOUTUBE_API_KEY")
OUTPUT_DIR = os.path.join("data", "raw")


VIDEOS_POR_MODELO = {
    "Geely_EX2": ["l6PvLsdLVwQ", "5V0kXn_AlMk", "yioJoB-DtkQ"],
    "BYD_Dolphin_Mini": ["0agSJfeXYqc", "PWinNdl-uSo"],
    "GWM_Ora_03": ["ZPIeXUtxxYg", "9m_E40Zp6ZE"],
    "Renault_Kwid_E_Tech": ["SbQQiMvodDU", "ilv5qvGS5-c"],
    "JAC_E_JS1": ["Uv8woM3l6zE", "Kc4nALejCWs"],
}


def extract_top_comments(video_id: str, api_key: str) -> pd.DataFrame:
    """Extrai os comentários principais de um vídeo específico."""
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        comentarios_dados = []
        next_page_token = None
        pagina_atual = 1
        
        print(f"  -> Varrendo vídeo ID: {video_id}...")

        while True:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat="plainText"
            )
            response = request.execute()
            
            items = response.get('items', [])
            if not items:
                break

            for item in items:
                top_comment = item['snippet']['topLevelComment']
                snippet = top_comment['snippet']
                
                comentarios_dados.append({
                    'video_id': video_id,
                    'comentario_id': top_comment['id'],
                    'autor': snippet['authorDisplayName'],
                    'texto': snippet['textDisplay'],
                    'likes': int(snippet['likeCount']),
                    'data_publicacao': snippet['publishedAt']
                })
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
                
            pagina_atual += 1
            time.sleep(0.1)

        df = pd.DataFrame(comentarios_dados)
        if not df.empty:
            df['data_publicacao'] = pd.to_datetime(df['data_publicacao'])
            
        return df

    except HttpError as e:
        print(f"  [ERRO DE API no vídeo {video_id}]: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"  [ERRO INESPERADO no vídeo {video_id}]: {e}")
        return pd.DataFrame()


def salvar_dados_modelo(df: pd.DataFrame, nome_modelo: str, diretorio_destino: str):
    """Salva o DataFrame consolidado de um modelo."""
    if df.empty:
        print(f"[AVISO] Nenhum comentário extraído para {nome_modelo}.")
        return
    
    os.makedirs(diretorio_destino, exist_ok=True)
    
    caminho_parquet = os.path.join(diretorio_destino, f"yt_raw_{nome_modelo}.parquet")
    caminho_csv = os.path.join(diretorio_destino, f"yt_raw_{nome_modelo}.csv")
    
    df.to_parquet(caminho_parquet, index=False)
    df.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
    
    print(f"\n[SUCESSO] Dados de {nome_modelo} salvos")
    print(f" -> Total de comentários consolidados: {len(df)}")
    print(f" -> Salvo em: {caminho_parquet}\n")


# EXECUÇÃO PRINCIPAL
if __name__ == "__main__":
    if not API_KEY:
        print("[ERRO] Chave YOUTUBE_API_KEY não encontrada")
    else:
        print("Iniciando pipeline de extração\n")
        
        for modelo, lista_videos in VIDEOS_POR_MODELO.items():
            print(f"=== Processando Modelo: {modelo} ===")
            
            dfs_modelo = []
            
            for vid in lista_videos:
                df_video = extract_top_comments(vid, API_KEY)
                if not df_video.empty:
                    dfs_modelo.append(df_video)

            
            if dfs_modelo:
                df_consolidado = pd.concat(dfs_modelo, ignore_index=True)
                
                df_consolidado.drop_duplicates(subset=['comentario_id'], inplace=True)
                
                salvar_dados_modelo(df_consolidado, modelo, OUTPUT_DIR)
            else:
                print(f"Nenhum dado retornado para {modelo}.\n")