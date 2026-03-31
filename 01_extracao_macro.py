import pandas as pd
import yfinance as yf

def extracao_bcb(codigo_bcb, nome_coluna, data_inicio='01/01/2018'):
    """
    Acessa a API do Banco Central e retorna um DataFrame limpo
    """

    url = f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_bcb}/dados?formato=json&dataInicial={data_inicio}'
    df = pd.read_json(url) # Transforma o JSON em DataFrame
    df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y') # Converte a coluna de data para datetime
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce') # Converte a coluna de valor para numérico

    df = df.set_index('data') # Define a coluna de data como índice

    df.columns = [nome_coluna] # Renomeia a coluna de valor

    return df

# Código do IPCA no SGS: 433 (% ao mês)
ipca_mensal = extracao_bcb(433, 'IPCA_Mensal', '01/01/2020')
print(ipca_mensal.head())

# Código do CDI no SGS: 12 ( % ao dia)
cdi_diario = extracao_bcb(12, 'CDI_Diario', '01/01/2020')
print(cdi_diario.head())

# A série do IMAB está desativada na API do Banco Central, então utilizaremos o yfinance para obter os dados do IMAB via ETF IMAB11, que é um fundo de índice que replica o desempenho do IMAB

imab_dados = yf.download('IMAB11.SA', start='2020-01-01', progress=False)['Close']

imab_df = pd.DataFrame(imab_dados)
imab_df.columns = ['IMAB11_Preco']
imab_df.index = imab_df.index.tz_localize(None) # Remove o fuso horário do índice de data

df_macro = cdi_diario.join(ipca_mensal, how='outer').ffill().dropna() # Junta os DataFrames usando o índice de data e preenchendo os dias sem IPCA com o último valor conhecido
df_macro = df_macro.join(imab_df, how='inner').ffill().dropna() # Agora com IMAB

print(df_macro.head())
print(df_macro.tail())

df_macro.to_csv('dados_macro_brutos.csv', index=True)