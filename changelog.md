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
