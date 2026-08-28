import os
import sys
import json
import time
import pandas as pd
import sys
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


AspectosPermitidos = Literal[
    "Preço/Custo-Benefício", "Desempenho/Motor", "Consumo/Economia", 
    "Design/Estética", "Acabamento/Conforto", "Confiabilidade/Manutenção", 
    "Comparativo Concorrentes", "Geral"
]

SentimentoPermitido = Literal["POSITIVO", "NEGATIVO", "NEUTRO"]

class AvaliacaoBIComentario(BaseModel):
    valor_comercial_produto: bool = Field(
        description="TRUE se o comentário traz opinião útil sobre o carro/marca. FALSE se for piada, spam ou meta-comentário do canal."
    )
    justificativa_descarte: Optional[str] = Field(
        default=None, 
        description="Motivo da rejeição caso valor_comercial_produto = False."
    )
    sentimento_produto: Optional[SentimentoPermitido] = Field(
        default=None, 
        description="Sentimento quanto ao veículo/marca."
    )
    aspecto_chave: Optional[AspectosPermitidos] = Field(
        default=None, 
        description="Categoria exata do atributo automotivo citado."
    )
    resumo_insight: Optional[str] = Field(
        default=None, 
        description="Resumo técnico do que o usuário relatou em poucas palavras."
    )


parser_bi = JsonOutputParser(pydantic_object=AvaliacaoBIComentario)


llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    max_output_tokens=1000
)


# SYSTEM PROMPT
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
def processar_comentarios_modelo(nome_modelo: str, batch_size: int = 50, min_likes: int = 50):
    input_path = os.path.join(RAW_DIR, f"yt_raw_{nome_modelo}.parquet")
    output_path = os.path.join(PROCESSED_DIR, f"yt_{nome_modelo}_processed.parquet")
    checkpoint_path = os.path.join(PROCESSED_DIR, f"yt_{nome_modelo}_checkpoint.json")

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    if not os.path.exists(input_path):
        print(f" [ERRO] Arquivo bruto não encontrado em {input_path}")
        return


    df_raw = pd.read_parquet(input_path)
    

    df_raw = df_raw[df_raw['likes'] >= min_likes].reset_index(drop=True)
    total_registros = len(df_raw)

    if total_registros == 0:
        print(f" [AVISO] Nenhum comentário atingiu o critério de {min_likes} likes para {nome_modelo}.")
        return


    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            resultados = json.load(f)
        inicio_idx = len(resultados)
        print(f" Checkpoint encontrado! Retomando do índice {inicio_idx}/{total_registros}...")
    else:
        inicio_idx = 0
        resultados = []

    print(f"\nIniciando pipeline para '{nome_modelo}' | {total_registros} comentários de alto valor (Min Likes: {min_likes})...")


    try:
        for i in range(inicio_idx, total_registros):
            texto = df_raw.iloc[i]['texto']
            print(f"[{i+1}/{total_registros}] Processando...")

            sucesso = False
            tentativas = 0

            while not sucesso and tentativas < 3:
                try:
                    res = chain_bi.invoke({
                        "modelo": nome_modelo.replace("_", " "), 
                        "comentario": texto
                    })
                    
                    if isinstance(res, dict):
                        resultados.append(res)
                        sucesso = True
                        print("   ->  Sucesso.")
                    else:
                        raise ValueError("Resposta da API não é um dicionário.")

                except Exception as e:
                    tentativas += 1
                    erro_str = str(e)
                    
                    if "429" in erro_str or "RESOURCE_EXHAUSTED" in erro_str:
                        print(f"   -> Rate Limit detectado. Pausando 15s...")
                        time.sleep(15)
                    else:
                        print(f"   ->  ERRO na API (Tentativa {tentativas}/3): {erro_str[:100]}")
                        time.sleep(2)

            if not sucesso:
                resultados.append({
                    "valor_comercial_produto": False,
                    "justificativa_descarte": f"Erro de Parsing/API: {erro_str[:80]}",
                    "sentimento_produto": None,
                    "aspecto_chave": None,
                    "resumo_insight": None
                })

            if (i + 1) % batch_size == 0 or (i + 1) == total_registros:
                with open(checkpoint_path, 'w', encoding='utf-8') as f:
                    json.dump(resultados, f, ensure_ascii=False, indent=2)
                print(f" >>> Checkpoint salvo com sucesso no disco! ({len(resultados)}/{total_registros})")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n[AVISO] Processamento interrompido pelo usuário (Ctrl+C)!")
        print("Salvando estado atual no checkpoint antes de sair...")
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        print("Checkpoint salvo de forma segura. Saindo do script.")
        sys.exit(0)


    df_analises = pd.DataFrame(resultados)
    df_final = pd.concat([df_raw, df_analises], axis=1)
    
    df_gold = df_final[df_final['valor_comercial_produto'] == True].copy()
    
    df_gold.to_parquet(output_path, index=False)
    df_gold.to_csv(output_path.replace(".parquet", ".csv"), index=False, encoding="utf-8-sig")
    
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    print(f"\n Pipeline concluído com sucesso para {nome_modelo}!")
    print(f"Total analisado: {total_registros} | Retidos (Gold): {len(df_gold)}")

if __name__ == "__main__":
    MODELOS_PARA_PROCESSAR = [
        "Geely_EX2",
        "BYD_Dolphin_Mini",
        "GWM_Ora_03",
        "Renault_Kwid_E_Tech",
        "JAC_E_JS1"
    ]
    
    for modelo in MODELOS_PARA_PROCESSAR:
        print(f"\n=======================================================")
        print(f" INICIANDO AVALIAÇÃO DE IA: {modelo}")
        processar_comentarios_modelo(modelo, batch_size=50, min_likes=50)