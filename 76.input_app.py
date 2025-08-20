import streamlit as st

############################################ button click
st.button('Reset', type='primary')

def button_write():
    st.write('버튼 클릭함')
        
st.button('activate', on_click=button_write)

clicked = st.button('activate2', type='primary')
if clicked:
    st.write('버튼 클릭됨') # 이건 문구가 밑에 나옴

#####################
st.header('같은 버튼 여러개 만들기')

# activate button 5개
for i in range(5):
    key = i+1
    st.button(f'button{key}', type='primary', key=f'act_btn_{key}')

#####################
st.divider()

st.title('Title')
st.header('header')
st.subheader('subheader')

st.write('wirte문장이다') # 들어온 데이터 형식에 맞게 알아서 보여줌
st.text('킄') # 기본 텍스트
st.markdown(
    '''
    여기는 메인 텍스트입니다.\n
    *:red[Red]* \n
    **bold** \n
    *italic* \n
    '''
)

st.code("""
import pandas as pd
import streamlit as st

def create_dataframe():
    data = {
        '이름': ['철수', '영희'],
        '나이': [30, 28]
    }
    return pd.DataFrame(data)

df = create_dataframe()
st.dataframe(df)
""", language='python')

st.divider()

st.button('Hello')
st.button('Hello', type='primary', icon='⚽')
# 똑같은 아이디를 가진 같은 버튼넣으면 에러남 (듑 에러)
st.button('Hello', type='primary', icon='⚽', key=1)




