import os
from PIL import Image
from super_image import EdsrModel, ImageLoader

def aumentar_resolucao_ia(pasta_entrada, pasta_saida, escala=3):
    """
    Aplica IA para aumentar a resolução da imagem criando novos detalhes.
    escala = 2, 3 ou 4 (ex: 480p -> 1440p para escala 3)
    """
    # Garante que a pasta de destino exista
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    print("Carregando o modelo de Inteligência Artificial... (Aguarde alguns segundos)")
    # Carrega o modelo EDSR treinado para super-resolução
    modelo = EdsrModel.from_pretrained('eugenesiow/edsr-base', scale=escala)

    # Filtra arquivos PNG na pasta
    arquivos = [arq for arq in os.listdir(pasta_entrada) if arq.lower().endswith('.png')]

    if not arquivos:
        print("Nenhum arquivo .png foi encontrado na pasta.")
        return

    print(f"Processando {len(arquivos)} imagens com IA...\n")

    for nome in arquivos:
        caminho_in = os.path.join(pasta_entrada, nome)
        caminho_out = os.path.join(pasta_saida, nome)

        try:
            # 1. Carrega a imagem original
            imagem_original = Image.open(caminho_in).convert('RGB')
            largura_orig, altura_orig = imagem_original.size

            # 2. Prepara e processa a imagem no modelo de IA
            inputs = ImageLoader.load_image(imagem_original)
            preds = modelo(inputs)

            # 3. Salva a imagem gerada pela IA
            ImageLoader.save_image(preds, caminho_out)

            # 4. Ajusta os metadados de DPI para 300 DPI (alta qualidade de impressão)
            img_processada = Image.open(caminho_out)
            largura_nova, altura_nova = img_processada.size
            img_processada.save(caminho_out, dpi=(300, 300))

            print(f"✅ {nome}: {largura_orig}x{altura_orig}p ➔ {largura_nova}x{altura_nova}p (com 300 DPI)")

        except Exception as e:
            print(f"❌ Erro ao processar {nome}: {e}")

    print("\nProcessamento concluído com sucesso!")

# === DEFINA SEUS CAMINHOS AQUI ===
PASTA_ORIGEM = "C:/Users/Renato/Documents/data_science/pln_social_media/images"
PASTA_DESTINO = "C:/Users/Renato/Documents/data_science/pln_social_media/images_melhoradas"

# Escala 3 transforma 480p em aproximadamente 1440p (acima de 1080p)
ESCALA_AUMENTO = 3 

# Executa
aumentar_resolucao_ia(PASTA_ORIGEM, PASTA_DESTINO, escala=ESCALA_AUMENTO)