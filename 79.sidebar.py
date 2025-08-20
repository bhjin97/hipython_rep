import streamlit as st
from PIL import Image

img = Image.open('./data/sample.jpg')
img1 = Image.open('./data/new_sample.jpg')

st.title(' 스트림 릿 웹페이지 구성하기')

st.sidebar.header("웰컴 메뉴")
selected_menu = st.sidebar.selectbox(
    '메뉴관리', 
    options=['Main', 'Analyze', 'Settings']
)
col1, col2 = st.columns(2)

# tab 메뉴 만들기 
def make_anal_tab():
    st.header(' Add Tab ')
    tab1, tab2, tab3 = st.tabs(['chart','data','settings'])
    with tab1:
        st.subheader('chart map')
        st.bar_chart({'데이터':[1,2,3,4,5]})

    with tab2:
        st.subheader('data map')
        st.bar_chart({'기준': ['a','b','c','d','e'],'값':[1,2,3,4,5]})
        
    # 3번째 탭 : 체크박스 (활성화여부), 슬라이더 (업데이트 주기sec)
    with tab3:
        st.subheader('settings map')
        ch_v = st.checkbox("slider")
        s_v = st.slider("지영`s IQ", 0, 100, 50, disabled= not ch_v)

if selected_menu == 'Main':
    st.subheader('Main page')
    st.write('하이요~')
    with col1:
        st.image(img, width=300, caption='Image from Unsplash')
    with col2:
        st.image(img1, width=300, caption='Image from Unsplash')
        
elif selected_menu == 'Analyze':
    st.subheader('Analyze Report')
    st.write('여긴 분석')
    make_anal_tab() # 분석 보고서 메뉴에서만 보이게
    # 밖으로 빼면 어느 페이지를 가도 보임
else:
    st.subheader('Settings change') 
    st.markdown('''
    ***설정을 바꾼***
    ''')
    
if st.sidebar.button('Select'):
    st.sidebar.write('dasf')
    

# 슬라이드 바 추가
st.sidebar.slider(
    label='킄',
    min_value=0,
    max_value=5,
    value=[2,3]
    
)
st.divider()

# 확장영역 추가
st.header('Expander')
with st.expander('숨긴영역'):
    st.write('여기는 보이지 않습니다. 클릭해야 보인다요')




