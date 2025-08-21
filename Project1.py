import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
from streamlit_folium import st_folium
import folium
from PIL import Image

st.title('심리상담 서비스 츄러스~미!')

img = Image.open('./data/츄러스미.png')
album_img = Image.open('./data/sabrina.jfif')

# tab 함수 만들기
def main_tab():
    st.header('Tab Menu')
    tab1, tab2, tab3 = st.tabs(['이용시간','컨텐츠 이용비율','스크린 타임 설정'])
    with tab1:
        st.subheader('이용시간')
        st.bar_chart({'데이터':[1,2,3,4,5]})

    with tab2:
        st.subheader('컨텐츠 이용비율')
        st.bar_chart({'기준': ['a','b','c','d','e'],'값':[1,2,3,4,5]})
        
    # 3번째 탭 : 체크박스 (활성화여부), 슬라이더 (업데이트 주기sec)
    with tab3:
        st.subheader('Screen Time')
        ch_v = st.checkbox("사용시간 설정")
        st.slider("사용시간", 1,23,2, disabled=ch_v)

st.set_page_config(
    page_title="사용자 대시보드",
    page_icon="👤",
    layout="wide",
)
############################ 사이드 바 ################################
with st.sidebar:
    st.image(img, width=70)
    with st.expander('프로필 요약'):
        st.write('우리 서비스의 마스코트 캐릭터')
    st.header("사이드 메뉴")
    selected_menu = st.selectbox(
        '메뉴관리', 
        options=['메인 페이지', '채팅하기', '나의 컨텐츠', '설정']
    )
    chk_fnt= st.checkbox('폰트 크기 조정')
    st.slider('폰트 크기 조정', 1,10, 5, disabled= not chk_fnt)
    if st.sidebar.button('오늘의 출석!', type='primary',icon='✅'):
        st.sidebar.write('반가워요! 오늘의 출석 완료😆')
 
   
############################ 페이지 변경 ################################ 
### 메인 페이지 (날짜별 이용시간, 감정상태(육각형),  )
if selected_menu == '메인 페이지':
    st.subheader('Main page')
    st.write('하이요~')
    
    # 메인 페이지 상단 구성
    col_f1, col_f2, col_f3 = st.columns([1,1,2])
    with col_f1:
        days_range = st.selectbox('기간', [7, 14, 30, 60, 90], index=1, help='최근 N일')
    with col_f2:
        view_mode = st.radio('보기', ['간단','상세'], horizontal=True)
    with col_f3:
        st.caption("필터를 변경하면 아래 위젯들이 갱신됩니다.")
    main_tab()
### 컨텐츠 화면 구성
elif selected_menu == '나의 컨텐츠':
    st.subheader('My Contents')
    st.write('킄')
    
    col1, col2= st.columns(2)
    with col1:
        st.subheader("🗺️ 병원 지도")
        with st.expander("내 위치/병원 보기", expanded=True):
            user_lat, user_lon = (37.5665, 126.9780)
            map_obj = folium.Map(location=[user_lat, user_lon], zoom_start=13, control_scale=True)
            folium.Marker([user_lat, user_lon], popup="내 위치", icon=folium.Icon(color="red", icon="user")).add_to(map_obj)
            st_folium(map_obj, height=420, returned_objects=[])
    
    with col2:
        st.subheader("🎵 음악 추천")
        st.markdown(''' 
                    ### 노래 제목
                    ''')
        st.image(album_img, width=200)
        st.markdown(''' 
                    아티스트
                    ''')
        st.button("재생", icon='🎵')
        

### 채팅 화면 구성
elif selected_menu == '채팅하기':
    st.subheader('Chat')
    st.write('챗봇 대기중')

### 설정 화면 (글자크기, 다크모드, 마케팅 동의 등)
else:
    st.subheader('Settings') 
    st.markdown('''
    ***설정 변경 메뉴***
    ''')
    tog_thm = st.toggle('화면 테마 변경')
    if tog_thm:
        st.text("다크 모드")
    else:
        st.text("화이트 모드")
        
    tog_alt = st.toggle('알람 설정')
    if tog_alt:
        st.text("알람 끄기")
    else:
        st.text("알람 켜기")
    
    pdata = st.checkbox('개인정보 수집 동의')
    if pdata:
        st.text('감사합니다 회원님의 정보는 안전하게 소중히 보관하겠습니다')
        
    mdata = st.checkbox('마케팅 및 맟춤서비스 알람 동의')
    if mdata:
        st.text('마케팅 및 맟춤서비스 알람 수신을 동의 하셨습니다')
        