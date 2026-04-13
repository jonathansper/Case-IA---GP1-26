**Modelagem Quantamental e Clusterização Hierárquica** aplicada a Fundos de Investimento Imobiliário (FIIs):


# Reunião dia 29/03

Gui Matos montou um slide apresentando nosso tema, trazendo a proposta construída junto com Jonathan. Segue esboço da apresentação:

### **1. Objetivo Central**
O projeto visa utilizar **Machine Learning e Econometria** para identificar clusters de risco estrutural no mercado de FIIs. A inovação está em agrupar os fundos não apenas por setor (como é o padrão), mas sim por métricas quantamentais que misturam fatores micro (balanços) e macro (sensibilidades a índices como CDI e IPCA).

### **2. Metodologia e Desafios Técnicos**
* **HRP (Hierarchical Risk Parity):** Será utilizado o estágio 1 do algoritmo HRP para focar no agrupamento hierárquico de ativos.
* **Tratamento de Dados:** Um desafio grande é a **multicolinearidade** entre fatores macro (ex: CDI vs. IPCA). A solução proposta é usar regressões **OLS (Mínimos Quadrados Ordinários)** para isolar os "choques puros" de cada fator através da ortogonalização.
* **Métricas Micro:** Serão analisadas variáveis como P/VPA, LTV, Dividend Yield, Vacância e WALT.
* **Métricas Macro:** Foco nos Betas de sensibilidade ao CDI, IPCA e IMA-B.

### **3. Prova de Conceito**
Guilherme apresentou um teste realizado com dados simulados onde o modelo conseguiu separar com precisão "Fundos de Tijolo" de "Fundos de Papel", e sub-agrupá-los em categorias como *High Yield* e *High Grade*, validando a lógica da taxonomia do algoritmo.

### **4. Próximos Passos e Cronograma**
A entrega final está prevista para o dia **26 de abril**. O plano de ação imediato é:
1.  **Mutirão de Dados (Esta semana):** Foco total na raspagem e coleta de dados micro (CVM, Banco Central) e macro.
2.  **Modelagem Econométrica (Início de abril):** Ortogonalização e extração dos Betas.
3.  **Lab de Machine Learning (Meados de abril):** Execução do algoritmo HAC e plotagem dos dendrogramas.
4.  **Análise Final:** Interpretação econômica dos clusters.

### **5. Divisão de Tarefas**
* **Engenharia de Dados:** Coleta e limpeza (ênfase na dificuldade de obter dados micro históricos).
* **Econometria:** Rodar as regressões e tratar as variáveis.
* **Ciência de Dados:** Padronização Z-score e calibração do modelo de clusterização.
* **Análise e Redação:** Interpretação dos resultados e fechamento do relatório técnico em LaTeX.

# Dia 11/04/2026

* ####Tratamento e reamostragem mensal
- **Correção aplicada:** CDI passou de média simples diária (`resample().mean()`) para
  acumulado mensal por capitalização composta (`resample().prod()`)
  - Motivo: média diária e retorno mensal têm escalas incompatíveis para a regressão de betas
  - Fórmula: `(1 + CDI_dia)^n - 1` via produto composto das taxas diárias
- IPCA: média mensal (dado já é mensal, resample não altera)
- IMAB11: retorno percentual mensal calculado sobre último preço do mês (`pct_change * 100`)
- **Corte temporal aplicado:** dados filtrados até `2025-12-31` (sem vazamento)
- Shape final: 71 meses × 3 colunas (fev/2020 → dez/2025)
- Colunas: `CDI_Mensal`, `IPCA_Mensal`, `IMAB_ret`
- Exportado: `dados_macro_tratados.csv`

---

### Ortogonalização das Variáveis Macroeconômicas
 
**Arquivo:** `etapa2_ortogonalizacao.py`
 
#### Bloco 2.1 — Carregamento e validação
- Leitura do `dados_macro_tratados.csv` com validação das 3 colunas esperadas
- Exibição de estatísticas descritivas e contagem de NaNs
 
#### Bloco 2.2 — Ortogonalização via OLS (Gram-Schmidt econométrico)
- CDI, IPCA e IMA-B são colineares e não podem entrar juntos na regressão de betas
- ortogonalização sequencial em 2 passos via OLS
  - **Passo 1:** `IPCA_Mensal ~ CDI_Mensal` → resíduo `u1_IPCA` (choque puro de inflação)
  - **Passo 2:** `IMAB_ret ~ CDI_Mensal + IPCA_Mensal` → resíduo `u2_IMAB` (choque puro de juro real)
  - CDI_Mensal permanece inalterado como vetor-âncora
-  vetores (CDI_Mensal, u1_IPCA, u2_IMAB) estatisticamente independentes
 
#### Bloco 2.3 — Validação da ortogonalidade
- Teste de correlação de Pearson entre todos os pares de vetores
- Correlações resultantes: r = 0.000000 em todos os pares (p = 1.0)

 
#### Bloco 2.4 — Visualização
- Painel 2×2: séries originais normalizadas, vetores ortogonalizados, heatmaps de correlação antes/depois
- Exportado: `diagnostico_ortogonalizacao.png`
 
#### Bloco 2.5 — Exportação
- Exportado: `macro_ortogonalizada.csv` (71 meses × 3 colunas)
 
---
 
### Extração de Betas via Regressão de Séries Temporais
 
**Arquivo:** `etapa3_extracao_betas.py`
 
#### Bloco 3.1 — Universo de FIIs
- Definida lista com 377 FIIs extraídos da base micro do projeto
- Parâmetros: `DATA_INICIO = 2020-01-01`, `DATA_FIM = 2025-12-31`, `MIN_OBSERVACOES = 24`
 
#### Bloco 3.2 — Download de retornos via yfinance
- Download em lotes de 50 tickers para evitar timeout da API
- Preços ajustados por dividendos e splits (`auto_adjust=True`)
- Reamostragem para último fechamento mensal (`resample("ME").last()`)
- Retorno simples mensal calculado via `pct_change()`
- Exportado: `retornos_fiis_mensais.csv` (71 meses × 377 FIIs)
 
#### Bloco 3.3 — Regressão OLS por FII
- Para cada FII com >= 24 meses de dados na janela comum com a macro:
  `R_i,t = αi + β_CDI·CDI_t + β_IPCA·u1_IPCA_t + β_IMAB·u2_IMAB_t + εi,t`
- coeficientes, t-estatísticas, p-valores, R², R²_adj, obs, início, fim, flags de significância (p < 10%)
- Critérios de exclusão registrados:
  - Sem dados no período: 58 FIIs
  - Fundo recente (< 24 meses): 84 FIIs
- Resultado bruto: 235 FIIs com betas extraídos
 
#### Bloco 3.4 — Filtro de outliers (Z-score robusto)
- Problema identificado: BVAR11.SA com β_IMAB = -128.57 (outlier absurdo com n=24)
- Método: Z-score robusto usando mediana e MAD (Median Absolute Deviation)
  - Robusto aos próprios outliers, ao contrário do Z-score padrão (média + std)
- Critério duplo de remoção:
  - Z-score > 10 em qualquer beta: removido independentemente do tamanho da série
  - Z-score > 5 em qualquer beta E série < 48 meses: removido
  - Série >= 48 meses com Z-score moderado: mantido (dado real, não ruído)
- 13 FIIs removidos, incluindo BVAR11.SA, SNEL11.SA, PNRC11.SA, BRIM11.SA
- FLRP11.SA (Floripa Shopping) removido apesar de n=71: β_CDI = 1.27 sem justificativa
  econômica para fundo de tijolo/shopping, diagnosticado como ruído de baixa liquidez
- Exportados:
  - `betas_macroeconomicos.csv` (222 FIIs × 19 colunas)
  - `fiis_excluidos.csv` (142 FIIs com motivo)
  - `betas_outliers_removidos.csv` (13 FIIs com betas fora de escala)
 
---
 
### ETAPA  — Merge Micro + Macro e Construção da Base HAC
 
**Arquivo:** `etapa4_merge.py`
 
#### Bloco 4.1 — Inspeção das bases
- Base micro: 377 FIIs × 12 colunas | índice numérico | chave de junção: `Ticker_YF`
- Base macro: 222 FIIs × 19 colunas | índice: ticker no formato `XXXX11.SA`

 
#### Bloco 4.2 — Merge inner
- Join inner entre micro (377) e macro (222) pelo ticker
- Resultado: 222 FIIs × 30 colunas | zero NaNs
- 155 FIIs da micro sem betas ficaram fora (série histórica insuficiente)
- Exportado: `base_quantamental.csv`
 
#### Bloco 4.3 — Seleção de features para o HAC
- Removidas colunas não-features:
  - Identificadores: `CNPJ_Fundo_Classe`, `Data_Referencia`, `Ticker_B3`
  - Métricas da regressão (não são inputs do modelo): `alpha`, `t_*`, `p_*`, `R2`, `R2_adj`, `sig_*`, `obs`, `inicio`, `fim`
  - Valores absolutos em reais: `Valor_Ativo`, `Patrimonio_Liquido`, `Total_Passivo`
    - Motivo: diferença de 4.000x entre menor e maior fundo dominaria a distância euclidiana
    - Multicolinearidade: Ativo = PL + Passivo (dependência linear perfeita)
 
#### Bloco 4.4 — Cálculo do P/VPA
- `VPA` bruto substituído pelo ratio `P/VPA = Preço_dez2025 / VPA`
- Preço de dezembro/2025 baixado via `yf.download()` para os 222 tickers
- 7 FIIs sem preço disponível: `ATSA11, BLMO11, CJCT11, ERPA11, KEVE11, STRX11, TRNT11`
  - Decisão: removidos (dado estruturalmente ausente — fundos em liquidação ou sem liquidez)
  - Alternativa descartada: imputar mediana mascararia problema real
- P/VPA resultante: mediana = 0.82 | min = 0.05 | max = 5.75
 
#### Bloco 4.5 — Base final para o HAC
- Shape: 215 FIIs × 8 features | zero NaNs
- Features:
  - `DY_Mes` — Dividend Yield mensal (política de distribuição)
  - `LTV` — Loan-to-Value (alavancagem financeira)
  - `Percentual_Vacancia` — risco operacional da carteira física
  - `Percentual_Inadimplencia` — risco de crédito
  - `beta_CDI` — sensibilidade à política monetária
  - `beta_IPCA` — sensibilidade ao choque puro de inflação
  - `beta_IMAB` — sensibilidade ao choque puro de juro real longo
  - `P_VPA` — prêmio/desconto de mercado em relação ao valor patrimonial
- Exportado: `base_hac.csv`
 
---
 
---
# Dia 13/04/2026
### ETAPA  — Hierarchical Agglomerative Clustering (HAC)
 
**Arquivo:** `etapa5_hac.py`
 
#### Bloco 5.1 — Remoção de outliers de P/VPA
- Identificados 2 FIIs com P/VPA extremo que distorciam o clustering:
  - `SJAU11.SA`: P/VPA = 5.75 | DY = 0 | sem vacância
  - `PRSN11.SA`: P/VPA = 3.41 | DY = 0 | sem vacância
- Ambos com DY zero — fundos em estruturação ou com anomalia de precificação
- Decisão: removidos antes do HAC
- Base final para o HAC: 213 FIIs
 
#### Bloco 5.2 — Padronização Z-score
- Aplicado `StandardScaler` sobre as 8 features
- Resultado verificado: média = 0.000 | std = 1.002
- Necessário para equalizar o peso de cada variável na distância euclidiana
 
#### Bloco 5.3 — Linkage de Ward
- Calculada matriz de distância euclidiana entre todos os pares de FIIs
- Aplicado linkage de Ward: funde os dois grupos cuja junção minimiza o aumento da variância interna
- Resultado: 212 fusões | última altura = 19.2642
 
#### Bloco 5.4 — Seleção do número de clusters (k)
- Testados k de 2 a 12 usando três critérios simultâneos:
  - **WCV (Within-Cluster Variance):** menor = clusters mais compactos internamente
  - **Silhouette Score:** maior = pontos mais próximos do seu cluster e distantes dos outros
  - **Davies-Bouldin Score:** menor = clusters mais compactos e separados entre si
- Resultados:
 
| k | WCV | Silhouette | Davies-Bouldin |
|---|---|---|---|
| 2 | 27.69 | 0.4253 | 2.0988 |
| 3 | 37.20 | 0.3987 | 1.5800 |
| 4 | 40.57 | 0.3906 | **1.2287** |
| 5 | 50.05 | 0.3256 | 1.3749 |
 
- Silhouette sugeria k=2, Davies-Bouldin k=12 — divergência causada por grupos extremos pequenos que distorcem métricas globais
- **Decisão: k=4** — melhor equilíbrio entre métricas e interpretabilidade econômica
 
#### Bloco 5.5 — Resultado do HAC com k=4
- Distribuição revelou estrutura assimétrica esperada:
  - Cluster 1: 190 FIIs — grupo mainstream
  - Cluster 2: 3 FIIs — inadimplência 80% (Crédito Distressed)
  - Cluster 3: 7 FIIs — LTV 53% (Alavancagem Extrema)
  - Cluster 4: 13 FIIs — vacância 50% (Imóvel Degradado)
- Os 3 grupos extremos são tão distintos que o Ward os separa antes de diferenciar o mainstream
- Exportado: `clusters_fiis.csv`
 
#### Bloco 5.6 — Subclustering do grupo mainstream
- 190 FIIs do Cluster 1 submetidos a novo HAC internamente
- Padronização própria do subgrupo (Z-score interno)
- Testados k de 2 a 8; Davies-Bouldin sugeriu k=7
- **Decisão: k=7** — sete subclusters com identidades econômicas distintas:
 
| Subcluster | N | Feature dominante | Arquétipo |
|---|---|---|---|
| 1 | 12 | Vacância 18.7% | Tijolo com Vacância |
| 2 | 8 | Inadimplência 9.7% | Papel Crédito Moderado |
| 3 | 21 | LTV 18.6% | Alavancado Moderado |
| 4 | 7 | DY 2.7% + P/VPA 1.15 | Income Premium |
| 5 | 125 | Tudo na média | Core Conservador |
| 6 | 2 | beta_IPCA 0.081 + beta_CDI negativo | CRI IPCA+ |
| 7 | 15 | beta_CDI -0.061 | Duration Longo |
 
#### Bloco 5.7 — Validação da coesão interna
- Calculado desvio padrão médio interno de cada arquétipo na escala original
- Resultado confirmou que o Core Conservador (125 FIIs) é o cluster **mais coeso** da base (std = 0.034)
- Conclusão: os 125 FIIs são genuinamente similares entre si e é resultado empírico sobre a estrutura do mercado, não artefato do algoritmo
 
| Arquétipo | N | std interno |
|---|---|---|
| Core Conservador | 125 | 0.034 |
| Tijolo com Vacância | 12 | 0.039 |
| Alavancado Moderado | 21 | 0.042 |
| Papel Crédito Moderado | 8 | 0.051 |
| Duration Longo | 15 | 0.077 |
| Alavancagem Extrema | 7 | 0.083 |
| CRI IPCA+ | 2 | 0.090 |
| Income Premium | 7 | 0.092 |
| Imóvel Degradado | 13 | 0.119 |
| Crédito Distressed | 3 | 0.189 |
 
#### Bloco 5.8 — Consolidação final dos arquétipos
- Combinados os 3 clusters extremos do HAC principal com os 7 subclusters internos
- Resultado: **10 arquétipos** com identidade econômica clara
- Exportados:
  - `clusters_fiis_final.csv` (213 FIIs com cluster, subcluster e arquétipo)
  - `perfil_arquetipos_final.png` — heatmap dos 10 arquétipos
  - `perfil_subclusters.png` — heatmap dos 7 subclusters internos
  - `dendrograma.png` — dendrograma completo do HAC principal
  - `criterios_corte.png` — gráfico WCV / Silhouette / Davies-Bouldin

