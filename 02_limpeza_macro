import pandas as pd

df = pd.read_csv('dados_macro_brutos.csv', index_col=0, parse_dates=True)

df.info()
df.describe()
df.isna().sum()

# Index data
df.index = pd.to_datetime(df.index)
df = df.sort_index()

# Frequência mensal
df_mensal = df.resample('ME').mean()

# retornos depois do resample
df_mensal['IMAB_ret'] = df_mensal['IMAB11_Preco'].pct_change()
df_mensal = df_mensal.drop(columns=['IMAB11_Preco'])
df_mensal = df_mensal.dropna()
df_mensal.info()
df_mensal.describe()

df_mensal.to_csv('dados_macro_tratados.csv')