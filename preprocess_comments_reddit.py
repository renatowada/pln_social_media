import os
import sys
import json
import time
import pandas as pd
from dotenv import load_dotenv
from typing import Literal, Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')

load_dotenv(os.path.join(BASE_DIR, '.env'))
os.makedirs(PROCESSED_DIR, exist_ok=True)


# SCHEMA DE SAÍDA E LLM
AspectosPermitidos = Literal[
    "Preço/Custo-Benefício", "Desempenho/Motor", "Consumo/Economia", 
    "Design/Estética", "Acabamento/Conforto", "Confiabilidade/Manutenção", 
    "Comparativo Concorrentes", "Geral"
]
SentimentoPermitido = Literal["POSITIVO", "NEGATIVO", "NEUTRO"]

class AvaliacaoBIComentario(BaseModel):
    valor_comercial_produto: bool = Field(description="TRUE se for útil, FALSE se for piada/spam.")
    justificativa_descarte: Optional[str] = Field(default=None)
    sentimento_produto: Optional[SentimentoPermitido] = Field(default=None)
    aspecto_chave: Optional[AspectosPermitidos] = Field(default=None)
    resumo_insight: Optional[str] = Field(default=None)

parser_bi = JsonOutputParser(pydantic_object=AvaliacaoBIComentario)

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", max_output_tokens=1000)

system_bi = """
## Persona: Analista de Inteligência de Mercado Sênior especializado na Indústria Automotiva.
Sua missão é extrair métricas acionáveis de comentários de redes sociais ESPECIFICAMENTE para um CARRO ALVO.

REGRAS DE OURO PARA FILTRAGEM:
1. DESCARTE IMEDIATO (valor_comercial_produto = False): Piadas, spam, OU comentários que falem exclusivamente de outras marcas/carros sem fazer nenhuma relação ou comparativo com o CARRO ALVO.
2. APROVAÇÃO (valor_comercial_produto = True): Opiniões diretas sobre o CARRO ALVO, relatos de donos, ou comparativos onde o CARRO ALVO é mencionado frente aos concorrentes.
3. PADRONIZAÇÃO: Escolha o aspecto estritamente entre as opções fornecidas.
"""

human_bi = "CARRO ALVO DA ANÁLISE: {modelo}\n\nAvalie o seguinte comentário:\n{comentario}\n\n{format_instructions}"

prompt_bi = ChatPromptTemplate.from_messages([("system", system_bi), ("human", human_bi)]).partial(format_instructions=parser_bi.get_format_instructions())
chain_bi = prompt_bi | llm | parser_bi


# PIPELINE DE PROCESSAMENTO
def processar_comentarios_reddit(nome_modelo: str, batch_size: int = 20):
    input_path = os.path.join(RAW_DIR, f"reddit_raw_{nome_modelo}.csv")
    output_path = os.path.join(PROCESSED_DIR, f"reddit_{nome_modelo}_processed.parquet")
    checkpoint_path = os.path.join(PROCESSED_DIR, f"reddit_{nome_modelo}_checkpoint.json")

    if not os.path.exists(input_path):
        print(f" [ERRO] Arquivo bruto não encontrado: {input_path}")
        return

    df_bruto = pd.read_csv(input_path)
    
    mapa_colunas = {
        'id': 'comentario_id',
        'username': 'autor',
        'author': 'autor', 
        'body': 'texto',
        'text': 'texto',
        'upVotes': 'likes',    
        'upvotes': 'likes',
        'score': 'likes',
        'createdAt': 'data_publicacao'
    }
    
    colunas_presentes = [col for col in mapa_colunas.keys() if col in df_bruto.columns]
    
    df_raw = df_bruto[colunas_presentes].rename(columns=mapa_colunas)
    
    df_raw['fonte_dados'] = 'Reddit'
    
    if 'texto' not in df_raw.columns:
        print(f" [ALERTA] Coluna de texto não encontrada no arquivo {nome_modelo}.")
        return

    df_raw = df_raw.dropna(subset=['texto']).reset_index(drop=True)

    if 'likes' not in df_raw.columns:
        df_raw['likes'] = 0
    else:
        df_raw['likes'] = pd.to_numeric(df_raw['likes'], errors='coerce').fillna(0).astype(int)


    minimo_likes_reddit = 1 if df_raw['likes'].max() > 0 else 0
    df_raw = df_raw[df_raw['likes'] >= minimo_likes_reddit].reset_index(drop=True)
    
    total_registros = len(df_raw)

    if total_registros == 0:
        print(f" [ALERTA] Nenhum comentário qualificado para {nome_modelo}.")
        return

    print(f"\nIniciando pipeline Reddit para '{nome_modelo}' | {total_registros} comentários...")


    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            resultados = json.load(f)
        inicio_idx = len(resultados)
        print(f" -> Retomando do checkpoint ({inicio_idx}/{total_registros})")
    else:
        inicio_idx = 0
        resultados = []


    try:
        for i in range(inicio_idx, total_registros):
            texto = df_raw.iloc[i]['texto']
            print(f"[{i+1}/{total_registros}] Processando...")

            sucesso = False
            tentativas = 0

            while not sucesso and tentativas < 3:
                try:
                    res = chain_bi.invoke({"modelo": nome_modelo.replace("_", " "), "comentario": texto})
                    
                    if isinstance(res, dict):
                        resultados.append(res)
                        sucesso = True
                        print("   -> Sucesso.")
                    else:
                        raise ValueError(f"IA não retornou um dicionário. Retornou: {type(res)}")
                        
                except Exception as e:
                    tentativas += 1
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        time.sleep(15)
                    else:
                        time.sleep(2)

            if not sucesso:
                resultados.append({"valor_comercial_produto": False, "justificativa_descarte": "Erro de API"})

            if (i + 1) % batch_size == 0 or (i + 1) == total_registros:
                with open(checkpoint_path, 'w', encoding='utf-8') as f:
                    json.dump(resultados, f, ensure_ascii=False, indent=2)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[AVISO] Interrompido. Salvando checkpoint...")
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        sys.exit(0)


    resultados_limpos = [
        r if isinstance(r, dict) 
        else {"valor_comercial_produto": False, "justificativa_descarte": "Falha na formatação da IA"} 
        for r in resultados
    ]
    
    if len(resultados_limpos) != len(resultados):
        print(f" [AVISO] {len(resultados) - len(resultados_limpos)} respostas inválidas da IA foram descartadas.")
    
    df_analises = pd.DataFrame(resultados_limpos)
    
    df_final = pd.concat([df_raw, df_analises], axis=1)
    

    df_gold = df_final[df_final['valor_comercial_produto'] == True].copy()
    
    df_gold.to_parquet(output_path, index=False)
    df_gold.to_csv(output_path.replace(".parquet", ".csv"), index=False, encoding="utf-8-sig")
    
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    print(f"\n[SUCESSO] Pipeline Reddit concluído para {nome_modelo}!")
    print(f"Total analisado: {total_registros} | Retidos com valor: {len(df_gold)}")

if __name__ == "__main__":
    MODELOS_PARA_PROCESSAR = [
        "Geely_EX2",
        "BYD_Dolphin_Mini",
        "GWM_Ora_03",
        "Renault_Kwid_E_Tech",
        "JAC_E_JS1"
    ]
    
    for modelo in MODELOS_PARA_PROCESSAR:
        caminho_teste = os.path.join(RAW_DIR, f"reddit_raw_{modelo}.csv")
        if os.path.exists(caminho_teste):
            print(f"\n=======================================================")
            print(f" INICIANDO AVALIAÇÃO REDDIT: {modelo}")
            processar_comentarios_reddit(modelo)