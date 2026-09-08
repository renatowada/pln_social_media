# 🚗 EV Social Listening BR: Análise de Sentimento do Mercado Automotivo

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)
![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)
![Reddit](https://img.shields.io/badge/Reddit-FF4500?style=for-the-badge&logo=reddit&logoColor=white)

## 📌 Visão Geral do Projeto
Este projeto é uma Prova de Conceito (PoC) de **Inteligência de Mercado** focada no setor de Veículos Elétricos (EVs) no Brasil. O objetivo é transformar dados não estruturados de redes sociais em *insights* acionáveis para montadoras e concessionárias, identificando exatamente quais aspectos (Preço, Acabamento, Desempenho, Consumo, Design, Manutenção, Comparativo aos concorrentes e Sentimento geral) são mais elogiados ou criticados pelos consumidores frente aos concorrentes diretos.

## 🏗️ Arquitetura da Solução
O pipeline de dados foi desenhado com foco em eficiência de custos e escalabilidade:

1. **Extração:** Coleta de comentários de reviews automotivos via API do YouTube (com limiar dinâmico de engajamento para otimização de requisições) e Web Scraping do Reddit via Apify.
2. **Processamento com IA:** Utilização do modelo `gemini-3.5-flash-lite` orquestrado pelo LangChain para classificar o sentimento e o aspecto chave de cada comentário com valor comercial.
3. **Armazenamento e Data Quality:** Consolidação da camada Ouro (Gold) em um banco de dados relacional (Supabase/PostgreSQL), onde consultas SQL são utilizadas para verificação e validação estrita da qualidade dos dados.
4. **Visualização:** Conexão direta via ODBC com o Microsoft Power BI para modelagem em esquema *Star Schema* via DAX e criação de dashboards gerenciais.

## ⚙️ Metodologia e O Pipeline de Dados

Para garantir a qualidade analítica e evitar vieses estatísticos, regras estritas foram aplicadas à ingestão de dados em módulos Python independentes:

* **Estratégia de Coleta (`extract_youtube.py` e Apify):** Extração dos vídeos mais relevantes de 5 modelos de EVs no YouTube, focando estritamente em comentários principais com $\ge$ 50 curtidas. O Reddit foi incorporado via Apify (filtro de $\ge$ 1 curtida) após restrições da API oficial, garantindo alta pertinência técnica de fóruns.
* **Filtros e Rate Limits (`preprocess_comments_yt.py` e `reddit.py`):** Validação rigorosa via IA para garantir que o texto possuísse valor comercial e fizesse referência explícita ao carro alvo, categorizando os resultados em 8 aspectos automotivos. Os scripts gerenciam limites de requisição e salvam checkpoints de segurança.
* **Governança (`consolidar_dados.py` e `upload_supabase.py`):** Concatenação forçando a integridade do esquema, injeção de metadados da fonte e sobrescrita de tabelas fato no PostgreSQL.

## 📊 Resultados do Funil de IA e Ponderação de Fontes

A hipótese de que o comportamento do usuário afeta a densidade do dado foi comprovada na conversão do funil (`gerar_relatorio_funil.py`):

* **YouTube (Escala de Consenso):** A taxa de utilidade oscilou entre 0,4% e 0,6%, evidenciando a alta dispersão temática da plataforma. Contudo, a exigência de $\ge$ 50 curtidas atuou como um multiplicador: os poucos comentários mantidos representam o consenso direto de dezenas ou centenas de consumidores que interagiram com a mensagem.
* **Reddit (Alta Profundidade):** A taxa de retenção variou de 17% a 51,7%, confirmando que os fóruns entregam altíssima densidade de inteligência comercial por texto. O anonimato reduz a pressão estética, favorecendo o detalhamento técnico e a validação por pares (*upvotes*).

## 📈 Resultados de Negócio e Conclusões

Os dados consolidados no painel revelaram *insights* críticos sobre a aceitação do mercado de EVs:

*(inserir as imagens aqui)*

1. **A Dor da Manutenção:** O mapeamento de sentimentos por aspecto revelou que a categoria **Confiabilidade/Manutenção** possui esmagadora rejeição. Isso indica que, independentemente do modelo, o consumidor brasileiro ainda carrega um forte ceticismo em relação ao pós-venda, disponibilidade de peças e infraestrutura de marcas recém-chegadas.
2. **O Trunfo da Experiência:** Em contrapartida, as categorias **Geral** e **Desempenho/Motor** lideram o sentimento positivo, sinalizando que a experiência de direção do veículo elétrico (torque instantâneo, silêncio) surpreende positivamente os motoristas.
3. **A Nova Ordem (NSS):** O comparativo de *Net Sentiment Score* escancara a atual divisão do mercado. Novas gerações de compactos chineses (*Geely EX2, BYD Dolphin Mini, GWM Ora 03*) apresentam saldo de reputação positivo, enquanto projetos mais antigos ou adaptados à combustão (*Renault Kwid E-Tech e JAC E-JS1*) sofrem com NSS negativo, indicando uma rápida perda de apelo competitivo frente às inovações de preço e design da concorrência.

## 🚧 Limitações e Escopo Analítico

A estruturação de projetos de Inteligência Artificial requer a clareza de suas delimitações metodológicas:

* **Auditoria Qualitativa (Human-in-the-Loop):** Para validar a assertividade da IA sem um gabarito prévio, realizou-se uma amostragem auditada manualmente (50 registros da camada Gold). O modelo obteve uma **precisão de 82% a 84%**.
* **Padrão de Erro Identificado (Neutral Drift):** Os Falsos Positivos retidos pela IA concentraram-se majoritariamente na categoria de sentimento **NEUTRO**. Isso atenua o impacto no cálculo do *NSS*, mantendo a polaridade e o saldo comparativo protegidos contra distorções nas métricas positivas e negativas.
* **Isolamento de Escopo (Percepção vs. Conversão):** Este painel mede a reputação digital. O *NSS* e os volumes de engajamento não devem ser utilizados como *proxy* direto para estimar volumes de emplacamentos comerciais.
* **Gestão de Viabilidade (Exclusão do Instagram):** Durante o *Discovery*, testes revelaram forte bloqueio anti-scraping (limite de paginação) no Instagram. Para evitar scripts frágeis, risco de *shadowban* e mitigar o viés de obsolescência temporal de postagens antigas (*Data Decay*), a plataforma foi removida do escopo final.
* **Viés Analítico e Pesos Matemáticos:** Optei por não atribuir multiplicadores numéricos arbitrários baseados na origem do dado (YouTube vs Reddit) para não destruir a integridade estatística da amostra. O rastreamento da linhagem (`fonte_dados`) no modelo relacional garante a correta segmentação contextual.
