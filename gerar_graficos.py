import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Configurações iniciais
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'master_dataset_veiculos.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'images')

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Estilo global dos gráficos
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.size': 12, 'font.family': 'sans-serif'})

def gerar_graficos():
    print("Lendo dados...")
    df = pd.read_csv(DATA_PATH)
    
    # Filtra apenas os que têm valor comercial (Ouro) e remove nulos nos aspectos
    df = df[df['valor_comercial_produto'] == True].copy()
    df.dropna(subset=['sentimento_produto', 'aspecto_chave'], inplace=True)

    cores_sentimento = {'POSITIVO': '#006400', 'NEGATIVO': '#FF0000', 'NEUTRO': '#808080'}

    # ==========================================
    # GRÁFICO 1: Sentimento por Aspecto (100% Stacked Bar)
    # ==========================================
    print("Gerando Gráfico 1: Aspectos...")
    
    # Prepara os dados (Crosstab)
    crosstab_aspectos = pd.crosstab(df['aspecto_chave'], df['sentimento_produto'], normalize='index') * 100
    
    # Ordena pelo volume de negativos para ficar igual ao seu Power BI (maior barra vermelha em cima)
    if 'NEGATIVO' in crosstab_aspectos.columns:
        crosstab_aspectos = crosstab_aspectos.sort_values(by='NEGATIVO', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Cria as barras empilhadas
    bottom = np.zeros(len(crosstab_aspectos))
    for sentimento in ['NEGATIVO', 'POSITIVO']: # Removendo o Neutro para espelhar o PBI, ou adicione se preferir
        if sentimento in crosstab_aspectos.columns:
            valores = crosstab_aspectos[sentimento]
            ax.barh(crosstab_aspectos.index, valores, left=bottom, 
                    color=cores_sentimento[sentimento], edgecolor='white', label=sentimento.capitalize())
            bottom += valores

    ax.set_xlim(0, 100)
    ax.set_xlabel('Porcentagem (%)')
    ax.set_ylabel('')
    ax.set_title('Avaliações Negativas e Positivas por Aspecto Chave', loc='left', pad=20, fontweight='bold')
    
    # Remove bordas
    sns.despine(left=True, bottom=True)
    ax.legend(loc='lower left', bbox_to_anchor=(0, -0.15), ncol=2, frameon=False)
    
    plt.tight_layout()
    path_g1 = os.path.join(OUTPUT_DIR, 'sentimento_aspectos.png')
    plt.savefig(path_g1, dpi=300, bbox_inches='tight')
    plt.close()

    # ==========================================
    # GRÁFICO 2: Net Sentiment Score (NSS) por Modelo
    # ==========================================
    print("Gerando Gráfico 2: NSS por Modelo...")
    
    # Calcula Positivos e Negativos totais por modelo
    agg_nss = df.groupby('modelo_veiculo')['sentimento_produto'].value_counts().unstack(fill_value=0)
    agg_nss['Total'] = agg_nss.sum(axis=1)
    
    # Calcula o percentual
    agg_nss['Perc_Positivo'] = agg_nss.get('POSITIVO', 0) / agg_nss['Total']
    agg_nss['Perc_Negativo'] = agg_nss.get('NEGATIVO', 0) / agg_nss['Total']
    
    # Calcula NSS e ordena
    agg_nss['NSS'] = (agg_nss['Perc_Positivo'] - agg_nss['Perc_Negativo']) * 100
    agg_nss = agg_nss.sort_values(by='NSS', ascending=False)

    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Define a cor com base no valor (Verde se > 0, Vermelho se < 0)
    cores_barras = ['#006400' if val > 0 else '#FF0000' for val in agg_nss['NSS']]
    
    ax.bar(agg_nss.index.str.replace("_", " "), agg_nss['NSS'], color=cores_barras, width=0.5)
    
    ax.set_title('Net Sentiment Score (NSS) por Modelo', loc='left', pad=20, fontweight='bold')
    ax.set_ylabel('NSS (%)')
    
    # Formata eixo Y como percentual
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: f'{int(x)}%'))
    plt.xticks(rotation=45, ha='right')
    
    # Linha zero de referência
    ax.axhline(0, color='black', linewidth=1.2)
    sns.despine(left=True, bottom=True)
    
    plt.tight_layout()
    path_g2 = os.path.join(OUTPUT_DIR, 'nss_por_modelo.png')
    plt.savefig(path_g2, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"\n[SUCESSO] Imagens em alta resolução salvas na pasta '{OUTPUT_DIR}'!")

if __name__ == "__main__":
    gerar_graficos()