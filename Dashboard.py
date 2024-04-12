import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout='wide')

def formata_numero(valor, prefix=""):
    texto = ''
    for unidade in ['', 'mil', 'milhões', 'bilhões']:
        if valor < 1000:
            texto = f'{prefix} {valor:.2f} {unidade}'
            break
        valor /= 1000
    return texto


st.title('DASHBOARD DE VENDAS :shopping_trolley:')

url = "https://labdados.com/produtos"

regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao=''

todos_anos = st.sidebar.checkbox('Dados de todos os períodos', value=True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider("Ano", 2020, 2023)

query_string = {'regiao': regiao.lower(), 'ano':ano}

# Chama API
response = requests.get(url, params=query_string)

dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', sorted(dados['Vendedor'].unique()), placeholder='Selecione os vendedores')

if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## Tabelas de Receita
receita_estados = dados.groupby(by='Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on='Local da compra', right_index=True).sort_values(by='Preço', ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='ME'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby(by='Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

## Tabelas de Quantidade de Vendas

#### 1. Construir um gráfico de mapa com a quantidade de vendas por estado.
vendas_estados = dados.groupby(by='Local da compra')[['Preço']].count()
vendas_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(vendas_estados, left_on='Local da compra', right_index=True).sort_values(by='Preço', ascending=False)

##### 2. Construir um gráfico de linhas com a quantidade de vendas mensal.
quantidade_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='ME'))['Preço'].count().reset_index()
quantidade_mensal['Ano'] = quantidade_mensal['Data da Compra'].dt.year
quantidade_mensal['Mes'] = quantidade_mensal['Data da Compra'].dt.month_name()

#### 3. Construir um gráfico de barras com os 5 estados com maior quantidade de vendas.
top5_vendas = vendas_estados.head().copy()

#### 4. Construir um gráfico de barras com a quantidade de vendas por categoria de produto.
vendas_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending = False))

## Tabelas de Vendedores

vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

## Gráficos
fig_mapa_receitas = px.scatter_geo(receita_estados,
                                    lat = 'lat', lon='lon', scope="south america",
                                    size='Preço', template='seaborn',
                                    hover_name='Local da compra',
                                    hover_data={'lat': False, 'lon': False})

fig_receita_mensal = px.line(receita_mensal, x='Mes', y='Preço', markers=True, 
                             range_y=(0, receita_mensal.max()),
                             color='Ano', line_dash='Ano', title='Receita mensal')

fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_receita_estados = px.bar(receita_estados.head(),
                             x = 'Local da compra', 
                             y = 'Preço',
                             text_auto=True,
                             title = 'Top estados (receitas)')

fig_receita_estados.update_layout(yaxis_title='Receita')

fig_receita_categorias = px.bar(receita_categorias,
                             text_auto=True,
                             title = 'Receita por categoria')

fig_receita_categorias.update_layout(yaxis_title='Receita')

## Visualização do Streamlit

aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

with aba1:
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Receita", formata_numero(dados["Preço"].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receitas, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with col2:
        st.metric("Qtde. Vendas", formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)

with aba2:
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Receita", formata_numero(dados["Preço"].sum(), 'R$'))

        fig_mapa_vendas = px.scatter_geo(vendas_estados, 
                            lat = 'lat', 
                            lon= 'lon', 
                            scope = 'south america', 
                            #fitbounds = 'locations', 
                            template='seaborn', 
                            size = 'Preço', 
                            hover_name ='Local da compra', 
                            hover_data = {'lat':False,'lon':False},
                            title = 'Vendas por estado',
                            )
        st.plotly_chart(fig_mapa_vendas, use_container_width=True)

        fig_vendas_mensal = px.line(quantidade_mensal, 
                    x = 'Mes',
                    y='Preço',
                    markers = True, 
                    range_y = (0,quantidade_mensal.max()), 
                    color = 'Ano', 
                    line_dash = 'Ano',
                    title = 'Quantidade de vendas mensal')

        fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas')
        st.plotly_chart(fig_vendas_mensal, use_container_width=True)

    with col2:
        st.metric("Qtde. Vendas", formata_numero(dados.shape[0]))

        fig_vendas_estados = px.bar(top5_vendas.head(),
                                    x ='Local da compra',
                                    y = 'Preço',
                                    text_auto = True,
                                    title = 'Top 5 estados'
        )
        fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')
        st.plotly_chart(fig_vendas_estados, use_container_width=True)


        fig_vendas_categorias = px.bar(vendas_categorias, 
                                        text_auto = True,
                                        title = 'Vendas por categoria')
        fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')
        st.plotly_chart(fig_vendas_categorias, use_container_width=True)

with aba3:
    qtde_vendedores = st.number_input('Qtde de Vendedores', 2, 10, 5)
    
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Receita", formata_numero(dados["Preço"].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtde_vendedores),
                                        x='sum',
                                        y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtde_vendedores).index,
                                        text_auto=True,
                                        title=f'Top {qtde_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)

    with col2:
        st.metric("Qtde. Vendas", formata_numero(dados.shape[0]))
        fig_receita_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtde_vendedores),
                                        x='count',
                                        y=vendedores[['count']].sort_values('count', ascending=False).head(qtde_vendedores).index,
                                        text_auto=True,
                                        title=f'Top {qtde_vendedores} vendedores (qtd. vendas)')
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)



# st.dataframe(dados)