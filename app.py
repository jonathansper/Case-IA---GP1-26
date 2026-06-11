import os
import random
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import yfinance as yf
    YFINANCE_OK = True
except ImportError:
    YFINANCE_OK = False

st.set_page_config(page_title="Risco Real de FIIs", page_icon="🏢", layout="wide")

# Isso descobre o caminho da pasta onde o app.py está salvo
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_csv = os.path.join(diretorio_atual, 'clusters_fiis_final.csv')


@st.cache_data
def carregar_dados():
    # Agora ele usa o caminho completo, sem erro!
    df = pd.read_csv(caminho_csv, index_col=0)
    return df


df = carregar_dados()

# ----------------------------------------------------------------------------
# IDENTIDADE VISUAL DOS ARQUÉTIPOS
# Cor fixa por arquétipo, usada em TODOS os gráficos via color_discrete_map.
# A paleta carrega significado de risco: azul calmo no baseline (Core),
# acentos quentes escalando até o vermelho nos grupos de stress, e
# roxos/violetas para as apostas macro (juros/inflação).
# ----------------------------------------------------------------------------
PALETA_ARQUETIPOS = {
    "Core Conservador":       "#4C72B0",  # azul calmo — baseline / risco médio
    "Alavancado Moderado":    "#DD8452",  # âmbar — risco de capital moderado
    "Duration Longo":         "#8172B3",  # roxo — aposta em juros nominais
    "CRI IPCA+":              "#5D3A9B",  # violeta — duration inflacionário
    "Income Premium":         "#CCB974",  # dourado — sustentabilidade do yield
    "Papel Crédito Moderado": "#55A868",  # verde — crédito gerenciável
    "Tijolo com Vacância":    "#E8A33D",  # laranja — risco de ocupação
    "Imóvel Degradado":       "#C44E52",  # vermelho — risco operacional físico
    "Alavancagem Extrema":    "#A23B3B",  # vermelho escuro — refinanciamento
    "Crédito Distressed":     "#6E1E1E",  # marrom-vermelho — inadimplência extrema
}

# Ordem fixa (por tamanho do grupo) para legendas/eixos estáveis em todo o app
ORDEM_ARQUETIPOS = [
    "Core Conservador", "Alavancado Moderado", "Duration Longo",
    "Imóvel Degradado", "Tijolo com Vacância", "Papel Crédito Moderado",
    "Income Premium", "Alavancagem Extrema", "CRI IPCA+", "Crédito Distressed",
]

# ----------------------------------------------------------------------------
# FORMATAÇÃO (padrão brasileiro: vírgula decimal, percentuais legíveis)
# ----------------------------------------------------------------------------
FEATURES = ['DY_Mes', 'LTV', 'Percentual_Vacancia', 'Percentual_Inadimplencia',
            'beta_CDI', 'beta_IPCA', 'beta_IMAB', 'P_VPA']

# Features que são proporções e devem aparecer como %
PERCENTUAIS = ['DY_Mes', 'LTV', 'Percentual_Vacancia', 'Percentual_Inadimplencia']

# Rótulos amigáveis (com a unidade embutida) para tabelas e eixos
ROTULOS = {
    'DY_Mes': 'DY mensal',
    'LTV': 'LTV',
    'Percentual_Vacancia': 'Vacância',
    'Percentual_Inadimplencia': 'Inadimplência',
    'beta_CDI': 'β CDI',
    'beta_IPCA': 'β IPCA',
    'beta_IMAB': 'β IMA-B',
    'P_VPA': 'P/VPA',
}

# Tooltips explicando cada feature (vêm da Tabela 2 do relatório)
AJUDA = {
    'DY_Mes': 'Dividend Yield mensal',
    'LTV': 'Loan-to-Value — nível de alavancagem',
    'Percentual_Vacancia': 'Risco operacional da carteira física',
    'Percentual_Inadimplencia': 'Risco de crédito',
    'beta_CDI': 'Sensibilidade à política monetária',
    'beta_IPCA': 'Sensibilidade ao choque puro de inflação',
    'beta_IMAB': 'Sensibilidade ao choque puro de juro real',
    'P_VPA': 'Prêmio/desconto sobre o valor patrimonial',
}

# Dimensão de risco dominante de cada arquétipo (Tabela 8 do relatório)
DIMENSAO_RISCO = {
    "Core Conservador": "Risco médio em todas as dimensões",
    "Alavancado Moderado": "Risco de estrutura de capital",
    "Duration Longo": "Risco de taxa de juros nominais",
    "Imóvel Degradado": "Risco operacional físico",
    "Tijolo com Vacância": "Risco de ocupação",
    "Papel Crédito Moderado": "Risco de crédito gerenciável",
    "Income Premium": "Risco de sustentabilidade do yield",
    "Alavancagem Extrema": "Risco de refinanciamento",
    "CRI IPCA+": "Risco de duration inflacionário",
    "Crédito Distressed": "Risco de inadimplência extrema",
}

# Arquétipos de stress: não tê-los na carteira geralmente é intencional/saudável
ARQUETIPOS_STRESS = {"Crédito Distressed", "Alavancagem Extrema", "Imóvel Degradado"}


def fmt_feature(feature, valor):
    """Formata um valor conforme a natureza da feature, em padrão BR."""
    if pd.isna(valor):
        return "—"
    if feature in PERCENTUAIS:
        return f"{valor * 100:.2f}%".replace(".", ",")
    if feature == "P_VPA":
        return f"{valor:.2f}".replace(".", ",")
    return f"{valor:.4f}".replace(".", ",")  # betas


def tabela_formatada(dados):
    """Recebe um DataFrame (FIIs nas linhas, features nas colunas) e devolve
    uma cópia com tudo formatado em string BR e colunas com rótulos amigáveis."""
    out = dados[FEATURES].copy()
    for f in FEATURES:
        out[f] = out[f].map(lambda v, _f=f: fmt_feature(_f, v))
    return out.rename(columns=ROTULOS)


# ----------------------------------------------------------------------------
# PREÇOS (yfinance) — comparação em base 100 do fundo vs. média do arquétipo
# ----------------------------------------------------------------------------
CAP_PARES = 25          # nº máx. de pares amostrados pra montar o índice do arquétipo
PERIODOS = {'1 mês': '1mo', '3 meses': '3mo', '6 meses': '6mo',
            '1 ano': '1y', '2 anos': '2y', '5 anos': '5y'}


@st.cache_data(ttl=3600, show_spinner=False)
def baixar_fechamento(tickers, periodo):
    """Baixa o fechamento ajustado dos tickers e devolve um DataFrame
    (datas nas linhas, tickers nas colunas). `tickers` é uma tupla (hashável
    pro cache). Cacheado por 1h pra não rebaixar o Yahoo a cada clique."""
    dados = yf.download(list(tickers), period=periodo,
                        progress=False, auto_adjust=True)
    if dados is None or dados.empty:
        return pd.DataFrame()
    close = dados['Close']
    if isinstance(close, pd.Series):           # caso de um único ticker
        close = close.to_frame(name=tickers[0])
    return close.dropna(how='all').sort_index()


def normaliza_base100(df_close):
    """Reescala cada série para começar em 100 no primeiro valor válido."""
    primeiro = df_close.apply(
        lambda c: c.loc[c.first_valid_index()] if c.first_valid_index() is not None else np.nan
    )
    return df_close.divide(primeiro) * 100


st.title("Risco Real de FIIs")
st.caption("Diversificação por arquétipo, não por setor — modelo HAC quantamental | 213 FIIs")

aba1, aba2, aba3, aba4 = st.tabs(['Visão Macro', 'Explorar FIIs', 'Minha Carteira', 'Validação do Modelo'])

with aba1:
    # KPI cards
    arquetipos_unicos = df["arquetipo"].nunique()
    total_fiis = len(df)
    maior_grupo = df["arquetipo"].value_counts().iloc[0]
    maior_grupo_nome = df["arquetipo"].value_counts().index[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de FIIs", total_fiis)
    col2.metric("Arquétipos de risco", arquetipos_unicos)
    # Corrigido: o 3º argumento de st.metric é o `delta` (vinha mostrando o nome
    # do arquétipo como uma variação verde com setinha, o que era enganoso).
    # Agora o nome é o valor e a concentração vai no tooltip.
    col3.metric(
        "Maior arquétipo",
        maior_grupo_nome,
        help=f"{maior_grupo} FIIs — {maior_grupo / total_fiis:.0%} da base",
    )

    st.divider()

    # Distribuição e scatter lado a lado
    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Distribuição dos arquétipos')
        count = df["arquetipo"].value_counts().reset_index()
        count.columns = ['Arquétipo', 'Quantidade']
        graf_barras = px.bar(
            count, x='Quantidade', y='Arquétipo', orientation='h',
            color='Arquétipo',
            color_discrete_map=PALETA_ARQUETIPOS,
            title='Quantidade de FIIs por Arquétipo',
        )
        graf_barras.update_layout(
            template='plotly_white',
            showlegend=False,                      # eixo y já nomeia os grupos
            yaxis={'categoryorder': 'total ascending'},  # maior grupo no topo
        )
        st.plotly_chart(graf_barras, use_container_width=True)

    with col2:
        st.subheader('Mapa de risco')
        grafico_scatter = px.scatter(
            df.reset_index(), x='beta_IPCA', y='DY_Mes', color='arquetipo',
            color_discrete_map=PALETA_ARQUETIPOS,
            category_orders={'arquetipo': ORDEM_ARQUETIPOS},
            hover_name='index',
            hover_data={'LTV': ':.1%', 'Percentual_Vacancia': ':.1%', 'P_VPA': ':.2f'},
            labels={"beta_IPCA": "β IPCA", "DY_Mes": "DY mensal", "arquetipo": "Arquétipo"},
            title='Risco x Retorno por Arquétipo',
        )
        grafico_scatter.update_layout(template='plotly_white')
        grafico_scatter.update_yaxes(tickformat='.1%')   # DY como percentual
        st.plotly_chart(grafico_scatter, use_container_width=True)

with aba2:
    st.subheader('Explorar FIIs')

    ticker = st.text_input('Digite o ticker do FII', placeholder='Ex: HGLG11.SA').upper().strip()

    if ticker:
        if ticker in df.index:
            fii = df.loc[ticker]
            arquetipo = fii["arquetipo"]
            cor = PALETA_ARQUETIPOS.get(arquetipo, "#4C72B0")

            st.success(f'**{ticker}** pertence ao arquétipo **{arquetipo}**')
            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                st.subheader('Features do fundo')
                tabela_fii = pd.DataFrame(
                    {"Valor": [fmt_feature(f, fii[f]) for f in FEATURES]},
                    index=[ROTULOS[f] for f in FEATURES],
                )
                st.dataframe(tabela_fii, use_container_width=True)

            with col2:
                st.subheader('Comparação com o arquétipo')
                arquetipo_fii = df[df["arquetipo"] == arquetipo].drop(index=ticker)
                if arquetipo_fii.empty:
                    st.info(
                        f'{ticker} é o único fundo do arquétipo **{arquetipo}** na base — '
                        'não há pares para comparar.'
                    )
                else:
                    st.dataframe(tabela_formatada(arquetipo_fii), use_container_width=True)

            # ---- Preço em base 100: fundo vs. média do arquétipo ----
            st.divider()
            st.subheader('Preço x arquétipo (base 100)')
            st.caption(
                'Fundo e média dos pares do arquétipo reescalados para começar em '
                '100. Se a clusterização captura risco de verdade, fundos do mesmo '
                'arquétipo tendem a se mover juntos — então o gráfico vira uma '
                'validação visual do modelo.'
            )

            if not YFINANCE_OK:
                st.info('Para ver os preços, instale a biblioteca: `pip install yfinance`.')
            else:
                periodo_label = st.radio('Período', list(PERIODOS.keys()),
                                         index=3, horizontal=True)
                periodo = PERIODOS[periodo_label]

                pares = df[df['arquetipo'] == arquetipo].index.drop(ticker).tolist()
                if len(pares) > CAP_PARES:
                    pares = random.Random(42).sample(pares, CAP_PARES)
                    nota_amostra = f' (amostra de {CAP_PARES} pares)'
                else:
                    nota_amostra = ''

                with st.spinner('Buscando preços no Yahoo Finance...'):
                    close = baixar_fechamento(tuple([ticker] + pares), periodo)

                if close.empty or ticker not in close.columns:
                    st.warning(
                        f'Não foi possível obter o histórico de preços de {ticker} '
                        'para esse período. Pode ser um fundo pouco líquido ou uma '
                        'instabilidade momentânea do Yahoo Finance.'
                    )
                else:
                    norm = normaliza_base100(close)
                    serie_fundo = norm[ticker]
                    cols_pares = [c for c in norm.columns if c != ticker]

                    plot_df = pd.DataFrame({ticker: serie_fundo})
                    if cols_pares:
                        plot_df[f'Média {arquetipo}{nota_amostra}'] = norm[cols_pares].mean(axis=1)

                    fig_preco = px.line(plot_df, labels={'value': 'Base 100', 'index': '', 'variable': ''})
                    fig_preco.update_layout(
                        template='plotly_white',
                        legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0),
                        margin=dict(l=10, r=10, t=10, b=10),
                    )
                    # fundo em destaque (cor do arquétipo, traço grosso); média mais sóbria
                    fig_preco.update_traces(selector={'name': ticker},
                                            line=dict(color=cor, width=3))
                    for tr in fig_preco.data:
                        if tr.name != ticker:
                            tr.line.color = '#999999'
                            tr.line.dash = 'dot'
                    st.plotly_chart(fig_preco, use_container_width=True)

                    if not cols_pares:
                        st.caption('Arquétipo sem pares com histórico disponível — exibindo só o fundo.')
                    else:
                        ret_fundo = serie_fundo.dropna().iloc[-1] - 100
                        ret_arq = plot_df.iloc[:, 1].dropna().iloc[-1] - 100
                        st.caption(
                            f'No período: **{ticker}** {ret_fundo:+.1f}% · '
                            f'**média do arquétipo** {ret_arq:+.1f}%. '
                            'Preços ajustados por proventos e desdobramentos.'
                        )
        else:
            st.warning(f'Ticker **{ticker}** não encontrado na base. Confira o sufixo (ex: HGLG11.SA).')

with aba3:
    st.subheader('Minha Carteira')
    st.write(
        'Monte sua carteira e veja a **diversificação real de risco** — não a '
        'setorial. Dois fundos de setores diferentes podem cair no mesmo '
        'arquétipo e, na prática, carregar o mesmo risco.'
    )

    selecao = st.multiselect(
        'Selecione os FIIs da sua carteira',
        options=sorted(df.index),
        placeholder='Comece a digitar um ticker...',
    )

    if not selecao:
        st.info('Selecione pelo menos um FII acima para analisar a composição de risco da carteira.')
    else:
        carteira = df.loc[selecao]
        n = len(carteira)
        dist = carteira['arquetipo'].value_counts()
        n_arq = dist.size
        maior_nome = dist.index[0]
        maior_qtd = dist.iloc[0]
        concentracao = maior_qtd / n

        # Score de diversificação: entropia da distribuição por arquétipo,
        # normalizada pelo máximo possível (10 arquétipos com peso igual).
        # 0 = tudo num arquétipo só | 100 = espalhado igualmente pelos 10.
        p = dist / n
        entropia = -(p * np.log(p)).sum()
        score = int(round(entropia / np.log(len(PALETA_ARQUETIPOS)) * 100))

        # --- Métricas de cabeçalho ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Fundos na carteira', n)
        c2.metric('Arquétipos distintos', f'{n_arq} de 10',
                  help='Quantas das 10 dimensões de risco do modelo sua carteira toca')
        c3.metric('Concentração no maior', f'{concentracao:.0%}',
                  help=f'{maior_qtd} de {n} fundos são {maior_nome}')
        c4.metric('Score de diversificação', f'{score}/100',
                  help='0 = tudo num arquétipo só | 100 = espalhado igualmente pelos 10')

        # --- Narrativa dinâmica (o "soco" da tese) ---
        if n == 1:
            st.info('Com um único fundo não há o que diversificar. Adicione mais FIIs para ver o perfil de risco da carteira.')
        elif n_arq == 1:
            st.error(
                f'Seus **{n} fundos** estão **todos no mesmo arquétipo '
                f'({maior_nome})**. Em exposição a risco, é praticamente como ter '
                f'um único fundo — a diversificação aqui é uma ilusão.'
            )
        elif concentracao >= 0.5:
            st.warning(
                f'Você tem **{n} fundos** em **{n_arq} arquétipos**, mas '
                f'**{concentracao:.0%}** da carteira está concentrada em '
                f'**{maior_nome}**. A diversificação de risco é menor do que o '
                f'número de fundos sugere.'
            )
        else:
            st.success(
                f'Boa distribuição: **{n} fundos** espalhados por **{n_arq} '
                f'arquétipos**, sem concentração excessiva num único perfil de risco.'
            )

        st.divider()

        col1, col2 = st.columns([1.3, 1])

        with col1:
            st.subheader('Composição por arquétipo')
            comp = dist.reset_index()
            comp.columns = ['Arquétipo', 'Quantidade']
            fig_comp = px.pie(
                comp, names='Arquétipo', values='Quantidade', hole=0.5,
                color='Arquétipo', color_discrete_map=PALETA_ARQUETIPOS,
                category_orders={'Arquétipo': ORDEM_ARQUETIPOS},
            )
            fig_comp.update_traces(textinfo='label+percent', textposition='inside')
            fig_comp.update_layout(template='plotly_white', showlegend=False,
                                   margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_comp, use_container_width=True)

        with col2:
            st.subheader('Score de diversificação')
            fig_score = go.Figure(go.Indicator(
                mode='gauge+number',
                value=score,
                number={'suffix': '/100'},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': '#4C72B0'},
                    'steps': [
                        {'range': [0, 33], 'color': '#F2D7D5'},
                        {'range': [33, 66], 'color': '#FCF3CF'},
                        {'range': [66, 100], 'color': '#D5F5E3'},
                    ],
                },
            ))
            fig_score.update_layout(template='plotly_white', height=260,
                                    margin=dict(l=20, r=20, t=10, b=10))
            st.plotly_chart(fig_score, use_container_width=True)

        # --- Seus fundos agrupados por arquétipo (revela os "substitutos de risco") ---
        with st.expander('Ver seus fundos agrupados por arquétipo (mesmo arquétipo = mesmo risco)'):
            for arq in dist.index:
                tickers_arq = carteira[carteira['arquetipo'] == arq].index.tolist()
                st.markdown(f"**{arq}** ({len(tickers_arq)}): {', '.join(tickers_arq)}")

        st.divider()

        # --- Dimensões de risco não cobertas ---
        st.subheader('Dimensões de risco não cobertas')
        presentes = set(dist.index)
        faltam_compl = [a for a in ORDEM_ARQUETIPOS
                        if a not in presentes and a not in ARQUETIPOS_STRESS]
        faltam_stress = [a for a in ORDEM_ARQUETIPOS
                         if a not in presentes and a in ARQUETIPOS_STRESS]

        if not faltam_compl:
            st.success('Sua carteira já cobre todos os arquétipos diversificadores do modelo.')
        else:
            st.markdown('Arquétipos diversificadores que sua carteira **não** tem hoje:')
            for a in faltam_compl:
                st.markdown(f"- **{a}** — {DIMENSAO_RISCO[a]}")

        if faltam_stress:
            st.caption('Perfis de stress ausentes (normalmente é bom não tê-los): '
                       + ', '.join(faltam_stress) + '.')

        st.caption(
            'Análise educacional baseada nos arquétipos do modelo HAC, considerando '
            'peso igual por fundo. Não é recomendação de investimento.'
        )

with aba4:
    st.subheader('Validação do Modelo')
    st.write(
        'Por que confiar nos arquétipos? Aqui estão as evidências: a estrutura em '
        'duas etapas, a escolha do número de grupos e a coesão interna de cada um.'
    )

    # ----- Estrutura em duas etapas -----
    st.markdown('#### Estrutura em duas etapas')
    st.write(
        'O HAC sobre os 213 FIIs com **k=4** isola três grupos extremos '
        '(inadimplência ~80%, LTV ~53%, vacância ~50%) e deixa um bloco '
        '*mainstream* de 190 fundos. Esse bloco é reclusterizado sozinho, com '
        'padronização própria, gerando **7 subgrupos** — totalizando os 10 arquétipos.'
    )

    EXTREMOS = {'Imóvel Degradado', 'Alavancagem Extrema', 'Crédito Distressed'}
    counts = df['arquetipo'].value_counts()
    estrutura = pd.DataFrame({'arquetipo': counts.index, 'n': counts.values})
    estrutura['estagio'] = estrutura['arquetipo'].apply(
        lambda a: 'Extremos isolados (HAC k=4)' if a in EXTREMOS
        else 'Mainstream subclusterizado (k=7)'
    )
    fig_estrutura = px.treemap(
        estrutura, path=['estagio', 'arquetipo'], values='n',
        color='estagio',
        color_discrete_map={
            'Mainstream subclusterizado (k=7)': '#4C72B0',
            'Extremos isolados (HAC k=4)': '#A23B3B',
        },
    )
    fig_estrutura.update_traces(textinfo='label+value')
    fig_estrutura.update_layout(template='plotly_white',
                                margin=dict(l=10, r=10, t=10, b=10), height=380)
    st.plotly_chart(fig_estrutura, use_container_width=True)

    st.divider()

    # ----- Seleção do número de grupos -----
    st.markdown('#### Seleção do número de grupos')

    # Métricas da etapa de modelagem (relatório, Tabelas 3 e 5)
    METRICAS = {
        'HAC principal (escolhido k=4)': (4, pd.DataFrame({
            'k': [2, 3, 4, 5, 6, 7],
            'WCV': [27.69, 37.20, 40.57, 50.05, 56.56, 59.08],
            'Silhouette': [0.4253, 0.3987, 0.3906, 0.3256, 0.3255, 0.1230],
            'Davies-Bouldin': [2.0988, 1.5800, 1.2287, 1.3749, 1.3252, 1.5250],
        })),
        'Subclustering do mainstream (escolhido k=7)': (7, pd.DataFrame({
            'k': [2, 3, 4, 5, 6, 7, 8],
            'WCV': [18.32, 24.65, 25.26, 35.53, 42.36, 47.12, 50.51],
            'Silhouette': [0.3354, 0.2236, 0.2438, 0.2572, 0.2153, 0.2266, 0.2166],
            'Davies-Bouldin': [1.6819, 1.7603, 1.4494, 1.4924, 1.3771, 1.2133, 1.2773],
        })),
    }

    etapa = st.radio('Etapa', list(METRICAS.keys()), horizontal=True)
    k_escolhido, met = METRICAS[etapa]

    def _destaca(row):
        cor = 'background-color: #D5F5E3' if row['k'] == k_escolhido else ''
        return [cor] * len(row)

    st.dataframe(
        met.style.apply(_destaca, axis=1).format(
            {'WCV': '{:.2f}', 'Silhouette': '{:.4f}', 'Davies-Bouldin': '{:.4f}'}
        ),
        hide_index=True, use_container_width=True,
    )

    g1, g2, g3 = st.columns(3)
    for coluna, metrica, nota in [
        (g1, 'WCV', 'cotovelo'),
        (g2, 'Silhouette', 'maior = melhor'),
        (g3, 'Davies-Bouldin', 'menor = melhor'),
    ]:
        fig_m = px.line(met, x='k', y=metrica, markers=True, title=f'{metrica} ({nota})')
        fig_m.add_vline(x=k_escolhido, line_dash='dash', line_color='gray')
        fig_m.update_layout(template='plotly_white', height=260,
                            margin=dict(l=10, r=10, t=40, b=10))
        coluna.plotly_chart(fig_m, use_container_width=True)

    st.info(
        'O Silhouette sozinho apontava **k=2** e o Davies-Bouldin melhorava sem '
        'parar com mais grupos. A divergência é estrutural: os grupos extremos são '
        'tão diferentes do resto que o algoritmo os separa primeiro e distorce '
        'métricas globais. A escolha de k equilibra o cotovelo do WCV, um '
        'Davies-Bouldin razoável e a interpretabilidade econômica.'
    )

    st.divider()

    # ----- Coesão interna -----
    st.markdown('#### Coesão interna dos arquétipos')
    st.write(
        'Para checar se os grupos são reais — e não baldes residuais — medimos o '
        'desvio padrão médio interno de cada arquétipo na escala original. Quanto '
        'menor, mais homogêneo é o grupo.'
    )

    coes = df.groupby('arquetipo')[FEATURES].std().mean(axis=1).sort_values()
    coes_df = coes.reset_index()
    coes_df.columns = ['Arquétipo', 'Desvio interno médio']
    fig_coes = px.bar(
        coes_df, x='Desvio interno médio', y='Arquétipo', orientation='h',
        color='Arquétipo', color_discrete_map=PALETA_ARQUETIPOS,
    )
    fig_coes.update_layout(template='plotly_white', showlegend=False,
                           yaxis={'categoryorder': 'total descending'},
                           margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_coes, use_container_width=True)

    mais_coeso = coes.index[0]
    n_mais_coeso = int((df['arquetipo'] == mais_coeso).sum())
    st.success(
        f'**{mais_coeso}** ({n_mais_coeso} fundos) é o grupo **mais coeso de toda '
        f'a base** — mais homogêneo até que arquétipos de 2 ou 3 fundos. A '
        f'concentração não é artefato do algoritmo: é um achado sobre o mercado.'
    )

    with st.expander('Nota honesta sobre a robustez dos grupos'):
        st.write(
            'Os 3 grupos extremos têm fronteiras nítidas e são muito robustos. Já '
            'os 7 subgrupos do mainstream têm separação mais "macia" (Silhouette '
            '~0,23): ali o modelo corta gradientes de risco, não fronteiras duras. '
            'A taxonomia mistura divisões categóricas e graduais, e os arquétipos '
            'não têm todos o mesmo grau de robustez estatística.'
        )
