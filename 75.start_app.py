import streamlit as st
st.title('아 짜증나~')
st.write('바보수현')

st.divider() # 영역 나누기 : 마크다운의 --- 와 같음
name = st.text_input('이름 : ')
if name :
    st.write(f'바보수현님의 대사 : {name}')

import pandas as pd

df = pd.read_csv('./data/ABNB_stock.csv')
print(df)
df