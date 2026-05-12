import streamlit as st
import pandas as pd


# Carregar dados
@st.cache_data
def carregar_dados():
    df = pd.read_csv('clusters_fiis_final.csv', index_col=0)
    return df

df = carregar_dados()

st.title("Risco Real de FIIs")
st.caption("Diversificação por arquétipo, não por setor — modelo HAC quantamental | 213 FIIs")

aba1, aba2, aba3, aba4 = st.tabs(['Visão Macro', 'Explorar FIIs', 'Minha Carteira', 'Validação do Modelo'])

with aba1:
    import plotly.express as px

    # KPI cards
    arquetipos_unicos = df["arquetipo"].nunique()
    total_fiis = len(df)
    maior_grupo = df["arquetipo"].value_counts().iloc[0]
    maior_grupo_nome = df["arquetipo"].value_counts().index[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de FIIs", total_fiis)
    col2.metric("Arquétipos identificados", arquetipos_unicos)
    col3.metric(f"Maior grupo", maior_grupo, maior_grupo_nome)

    st.divider()

    # Distribuição e scatter lado a lado
    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Distribuição dos arquétipos')
        count = df["arquetipo"].value_counts().reset_index()
        count.columns = ['Arquétipo', 'Quantidade']
        graf_barras = px.bar(count, x='Quantidade', y='Arquétipo', orientation = 'h', color = 'Arquétipo', title='Quantidade de FIIs por Arquétipo')
        st.plotly_chart(graf_barras, use_container_width=True)


    with col2:
        st.subheader('Mapa de risco')
        grafico_scatter = px.scatter(df.reset_index(), x='beta_IPCA', y='DY_Mes', color='arquetipo', hover_name = 'index', 
        hover_data = ['LTV', 'Percentual_Vacancia', 'P_VPA'],
        labels = {"beta_IPCA": "β IPCA", "DY_Mes": "DY mensal", "arquetipo": "Arquétipo"},
        title='Risco x Retorno por Arquétipo')
        st.plotly_chart(grafico_scatter, use_container_width=True)

with aba2:
    st.subheader('Explorar FIIs')
    
    ticker = st.text_input('Digite o ticker do FII', placeholder='Ex: HGLG11.SA').upper().strip()

    if ticker:
        if ticker in df.index:
            fii = df.loc[ticker]
            arquetipo = fii["arquetipo"]

            st.success(f'**{ticker}** pertence ao arquétipo **{arquetipo}**')
            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                st.subheader('Features do fundo')
                features = ['DY_Mes', 'LTV', 'Percentual_Vacancia', 'Percentual_Inadimplencia', 'beta_CDI', 'beta_IPCA', 'beta_IMAB', 'P_VPA']
                st.dataframe(fii[features].to_frame(name='Valor').round(4), use_container_width=True)

            with col2:
                st.subheader('Comparação com arquétipo')
                arquetipo_fii = df[df["arquetipo"] == arquetipo].drop(index=ticker)  
                st.dataframe(arquetipo_fii[features].round(4), use_container_width=True)
with aba3:
    st.subheader('Minha Carteira')
    st.write('Em construção')

with aba4:
    st.subheader('Validação do Modelo')
    st.write('Em construção')
