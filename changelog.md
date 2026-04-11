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

####11/04/2026
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

### ETAPA 2 — Ortogonalização das Variáveis Macroeconômicas

**Arquivo:** `etapa2_ortogonalizacao.py`

#### Bloco 2.1 — Carregamento e validação
- Leitura do `dados_macro_tratados.csv` com validação das 3 colunas esperadas
- Exibição de estatísticas descritivas e contagem de NaNs

#### Bloco 2.2 — Ortogonalização via OLS (Gram-Schmidt econométrico)
- Problema: CDI, IPCA e IMA-B são colineares — não podem entrar juntos na regressão de betas
- Solução: ortogonalização sequencial em 2 passos via OLS
  - **Passo 1:** `IPCA_Mensal ~ CDI_Mensal` → resíduo `u1_IPCA` (choque puro de inflação)
  - **Passo 2:** `IMAB_ret ~ CDI_Mensal + IPCA_Mensal` → resíduo `u2_IMAB` (choque puro de juro real)
  - CDI_Mensal permanece inalterado como vetor-âncora
- Resultado: vetores (CDI_Mensal, u1_IPCA, u2_IMAB) estatisticamente independentes

#### Bloco 2.3 — Validação da ortogonalidade
- Teste de correlação de Pearson entre todos os pares de vetores
- Correlações resultantes: r = 0.000000 em todos os pares (p = 1.0)
- Status: aprovado

#### Bloco 2.4 — Visualização
- Painel 2×2: séries originais normalizadas, vetores ortogonalizados, heatmaps de correlação antes/depois
- Exportado: `diagnostico_ortogonalizacao.png`

#### Bloco 2.5 — Exportação
- Exportado: `macro_ortogonalizada.csv` (71 meses × 3 colunas)

