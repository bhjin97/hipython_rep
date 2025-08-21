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
album_img = Image.open('./data/sample.jpg')

############################# 랜덤 데이터 생성 ############################
rng = np.random.default_rng(42)

# -------------------------------
# 1) 기간/시간 축
# -------------------------------
dates = pd.date_range("2025-07-23", periods=30, freq="D")  # 최근 30일
hours = np.arange(24)

# -------------------------------
# 2) 시간대별 기본 사용 패턴(분 단위의 '기대값' 스케치)
#    - 새벽 극저, 아침-출근 약간 상승, 점심 하락, 저녁 피크
# -------------------------------
base_profile = np.array([
    1, 1, 1, 1,         # 00-03
    2, 3, 5,            # 04-06
    8, 10,              # 07-08
    12, 10,             # 09-10
    7,  6,              # 11-12 (점심 하락)
    7,  8,  9,          # 13-15
    10, 12,             # 16-17
    15, 20, 18, 14,     # 18-21 (저녁 피크 20시)
    10, 6               # 22-23
], dtype=float)

# sanity: 길이 24여야 함
assert len(base_profile) == 24

# -------------------------------
# 3) 요일 효과
#    - 평일: 기본
#    - 주말: 낮(10-17시) 0.8x, 저녁(18-23시) 1.1x
# -------------------------------
def weekend_multiplier(hour):
    if 10 <= hour <= 17:
        return 0.8
    if 18 <= hour <= 23:
        return 1.1
    return 1.0

# -------------------------------
# 4) 일자별 컨디션/변동 (로그정규로 스케일링)
# -------------------------------
daily_scale = {d: rng.lognormal(mean=0.0, sigma=0.35) for d in dates}

# -------------------------------
# 5) 데이터 합성
#    - 기대값 * (요일/주말 보정) * 일자 스케일 + 감마 노이즈
#    - 일부 시간대는 완전 미사용(0분)로 드랍아웃
# -------------------------------
rows = []
for d in dates:
    is_weekend = d.weekday() >= 5  # 5=토, 6=일
    for h in hours:
        mu = base_profile[h]

        # 주말 보정
        if is_weekend:
            mu *= weekend_multiplier(h)

        # 일자 스케일링
        mu *= daily_scale[d]

        # 감마 노이즈(양의 연속값, 분 단위로 자연스럽게 튐)
        # shape-k, scale-theta (기대값 = k*theta). 여기선 평균 근처로 약간 흔들리게 설정
        noise = rng.gamma(shape=2.0, scale=mu / max(mu, 1) * 0.6) if mu > 0 else 0.0

        minutes = mu + noise

        # 드랍아웃(해당 시간대 완전 미사용): 밤/이른새벽은 확률 높게
        dropout_p = 0.25 if h in [0,1,2,3,4] else (0.10 if 10 <= h <= 17 else 0.15)
        if rng.random() < dropout_p:
            minutes = 0.0

        # 물리적 상한/하한(한 시간에 0~60분)
        minutes = int(np.clip(minutes, 0, 60))

        rows.append([d.date(), int(h), minutes])

df = pd.DataFrame(rows, columns=["date", "hour", "minutes"])

# -------------------------------
# 6) 현실감 점검(선택): 일/주간 합계 통계
# -------------------------------
# print(df.groupby('date')['minutes'].sum().describe())
# print(df.groupby('hour')['minutes'].mean().round(1))

#################### 감정분포 데이터 ###################
np.random.seed(11)
emotions = ["기쁨", "슬픔", "분노", "불안", "놀람", "평온"]
scores = np.random.randint(3, 10, size=len(emotions))
df_radar = pd.DataFrame({
    "emotion": emotions,
    "score": scores
})
######################################################################


# tab 함수 만들기
def main_tab():
    st.header('Tab Menu')
    tab1, tab2, tab3 = st.tabs(['이용시간','감정 분포','스크린 타임 설정'])
    with tab1:
        st.subheader('이용시간')
        st.markdown("**시간대별 사용 히트맵**")
        pivot = df.pivot_table(index="date", columns="hour", values="minutes", aggfunc="sum", fill_value=0)
        fig_heat = px.imshow(
            pivot,
            labels=dict(x="시간", y="날짜", color="분"),
            aspect="auto",
            color_continuous_scale="Purples",
        )
        fig_heat.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=300)
        st.plotly_chart(fig_heat, use_container_width=True)

    with tab2:
        st.subheader('감정 분포')
        fig_radar = px.line_polar(df_radar, r="score", theta="emotion", line_close=True)
        fig_radar.update_traces(fill='toself')
        fig_radar.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=340)
        st.plotly_chart(fig_radar, use_container_width=True)
        
    # 3번째 탭 : 체크박스 (활성화여부), 슬라이더 (업데이트 주기sec)
    with tab3:
        st.subheader('Screen Time')
        ch_v = st.checkbox("사용시간 설정")
        st.slider("사용시간", 1,23,2, disabled= not ch_v)

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
        '페이지 선택', 
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
    # 탭 함수임
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
    st.subheader('Chat - 아래의 서비스를 이용하세요!')
    # user_input = st.text_input('채팅을 입력하세요')
    # if st.button('전송하기', icon='📤'):
        # st.write(" 당신의 입력:", user_input)
    NGROK_URL = "https://5217387dab82.ngrok-free.app"
    st.components.v1.iframe(src=NGROK_URL, height=760, scrolling=True)
        

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
        st.text('마케팅 및 맟춤서비스 알람 수신을 동의하셨습니다')
        