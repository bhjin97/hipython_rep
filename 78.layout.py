import streamlit as st

# layout 요소
# colums 는 요소를 왼쪽에서 오른쪽으로 배치할 수 있다 
col1, col2 = st.columns(2)

with col1:
    st.metric(
        '오늘의 날씨',
        value='35c',
        delta='+3'
    )

with col2:
    st.metric(
        '오늘의 공기질',
        value='좋음',
        delta='-30',
        delta_color='inverse'
    )

##    
st.markdown('---')

data = {
    '이름': ['홍길동', '김길동','박길동'],
    '나이': [10,20,30]
}

import pandas as pd
df = pd.DataFrame(data)
st.text('dataframe')
st.dataframe(df)
st.divider()

st.text('table')
st.table(df)
st.divider()

st.text('json')
st.json(data)

# datafile.csv > load > table 출력 > px.box() > st.plotly_chart()
df1 = pd.read_csv('./data/ABNB_stock.csv')
st.text('ABNB_stock')
st.table(df1.head(5))

import plotly.express as px
color = px.colors.sequential.Plotly3

df1['YearMonth'] = pd.to_datetime(df1['Date']).dt.to_period('M').astype(str)
# json은 period형 인식 못함 -> 문자열 변형
fig = px.box(df1, x= 'YearMonth', y='Volume', color="YearMonth", 
    color_discrete_sequence=color)
st.plotly_chart(fig, key = 1)

import seaborn as sns
import matplotlib.pyplot as plt

# 위젯을 활용한 interactive 그래프 표현
x_options = ['YearMonth','Open', 'Close']
y_options = ['Volume','High', 'Low']

x_option = st.selectbox(
    'Select X-axis',
    index=None, # 초기 선택값 지정 안되게 함
    options=x_options
)

y_option = st.selectbox(
    'Select Y-axis',
    index=None,
    options=y_options
)

if (x_option != None) & (y_option != None):
    fig3 = px.box(
        data_frame=df1, x=x_option, y=y_option,
        color="YearMonth", color_discrete_sequence=color, 
        width=500
        )
    st.plotly_chart(fig3 , key= 2)