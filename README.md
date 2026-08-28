# 🚗 EV Social Listening BR: Análise de Sentimento do Mercado Automotivo

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![Apify](https://img.shields.io/badge/Apify-97CA3F?style=for-the-badge&logo=apify&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/Supabase_PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)
![Reddit](https://img.shields.io/badge/Reddit-FF4500?style=for-the-badge&logo=reddit&logoColor=white)

## 📌 Visão Geral do Projeto
Este projeto é uma Prova de Conceito (PoC) de **Inteligência de Mercado** focada no setor de Veículos Elétricos (EVs) no Brasil. O objetivo é transformar dados não estruturados de redes sociais em *insights* acionáveis para montadoras e concessionárias, identificando exatamente quais aspectos (Preço, Acabamento, Desempenho, Consumo, Design, Manutenção, Comparativo aos concorrentes e Sentimento geral) são mais elogiados ou criticados pelos consumidores frente aos concorrentes diretos.

## 🏗️ Arquitetura da Solução
O pipeline de dados foi desenhado com foco em eficiência de custos e escalabilidade:
1. **Extração:** Coleta de comentários de reviews automotivos via API do YouTube (com limiar dinâmico de engajamento para otimização de requisições).
2. **Processamento com IA:** Utilização do modelo `gemini-3.5-flash-lite` orquestrado pelo LangChain para classificar o sentimento e o aspecto chave de cada comentário com valor comercial.
3. **Armazenamento e Data Quality:** Consolidação da camada Ouro (Gold) em um banco de dados relacional (Supabase/PostgreSQL), onde consultas SQL são utilizadas para verificação e validação estrita da qualidade dos dados.
4. **Visualização:** Conexão direta via ODBC com o Microsoft Power BI para modelagem em DAX e criação de dashboards gerenciais.

## ⚙️ Metodologia e Regras de Negócio

Para garantir a qualidade analítica e evitar vieses estatísticos, regras estritas foram aplicadas à ingestão de dados:

* Extração dos 2 a 3 vídeos mais relevantes de cada modelo no YouTube, focando estritamente em comentários principais com mais de 50 curtidas.
* Pivotagem estratégica para o Apify no Reddit após restrições de API oficial, utilizando um filtro leniente de curtidas para aproveitar a alta pertinência técnica e o baixo viés dos "foristas".
* Validação rigorosa via IA para garantir que o texto possuísse valor comercial e fizesse referência explícita ao carro alvo, evitando ruídos sobre montadoras concorrentes.
* Categorização automatizada das opiniões validadas em 8 aspectos automotivos predefinidos.

## 🐍 O Pipeline de Dados

O ecossistema foi construído em módulos Python independentes, preparados para orquestração futura:

* `extract_youtube.py`: Acessa a API do Google, pagina os resultados e salva a camada bruta.
* `preprocess_comments_yt.py` e `preprocess_comments_reddit.py`: Atuam como o motor da IA, aplicando validações de tipagem e contornando limites de requisição (*Rate Limits*).
* `consolidar_dados.py`: Concatena os arquivos processados, forçando a integridade do esquema e injetando o metadado da fonte.
* `upload_supabase.py` e `gerar_relatorio_funil.py`: Sobrescrevem as tabelas no PostgreSQL e calculam a eficiência de retenção analítica.

## 📊 Resultados do Funil de IA

A hipótese de que o Reddit possui dados mais densos e focados do que o YouTube foi comprovada na conversão do funil de retenção:

* **YouTube:** A taxa de utilidade oscilou entre 0,4% e 0,6%, evidenciando a alta dispersão temática da plataforma e o acerto da heurística de curtidas.
* **Reddit:** A taxa de retenção variou de 17% a 51,7%, confirmando que os fóruns, apesar do menor volume absoluto, entregam dados com altíssima densidade de inteligência comercial.
