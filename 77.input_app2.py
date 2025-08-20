import streamlit as st

st.header('여기는 헤더')
# checkbox


active = st.checkbox('헤더는 헤더이다')
if active:
    st.text('정답입니다')
    
# 함수, on_change ->checkbox_write
def checkbox_write():
    st.write('잘가')

st.checkbox('안녕', on_change=checkbox_write)
    

# 세션-상태 값에 저장
if 'checkbox_state' not in st.session_state:
    st.session_state.checkbox_state = False

def checkbox_write1():
    st.session_state.checkbox_state = True
 
if st.session_state.checkbox_state:
    st.write('음..')
    
st.checkbox('진짜 눌러', on_change=checkbox_write1)

st.divider()

selected = st.toggle('Turn on the switch!')
if selected:
    st.text("킄")
else:
    st.text("흫")

# selectbox 선택지
menu = st.selectbox(
    ' 점심메뉴 고르기',
    options=['롯데리아', '햄버거', '우동', '찜닭']
)
st.text(f'오늘의 점심메뉴는 : {menu}')
if menu == '롯데리아':
    st.write('우웩 맛없겠다🤮')
else:
    st.write('냐미~😋')
    
# radio
genre = st.radio(
    '무슨 영화를 좋아하세요', ['멜로', '스릴러', '판타지'],
    captions=['봄날은 간다', '곤지암', '웬즈데이']
)
st.text(f'당신이 좋아하는 장르는 {genre}')

# multiselect
menus = st.multiselect('먹고 싶은거 다 골라', ['롯데리아', '햄버거', '우동', '찜닭'],
)
st.text(f'내가 선택한 메뉴는 {menus}')

#slider
score = st.slider('내 점수 선택', 0, 100,1) # 시작, 끝, 초기값
st.text(f'score:{score}')

from datetime import time
st_time, end_time = st.slider(
    'ADSP 공부시간 선택',
    min_value=time(0), max_value=time(23), # 범위 지정
    value=(time(8), time(18)), # 초기 화면의 세팅 값
    format='HH:mm' # 시간 나타내는 포맷
)
st.text(f'ADSP 공부시간 : {st_time} ~ {end_time}')

# text_input
txt1 = st.text_input('영화제목', placeholder='제목 입력하세요')
txt2 = st.text_input('비밀번호', placeholder='비번 입력하세요')
st.text(f'텍스트 입력 결과 : {txt1}, {txt2}')

# 파일 업로더
# 업로드한 파일은 사용자의 세션에 있습니다 -> 화면을 갱신하면 사라짐
# 서버에 저장하려면 별도로 구현
# 데이터베이스에 저장하는 로직도 구현가능
st.file_uploader(
    '파일 선택', type='csv', accept_multiple_files=False
)
if file is not None:
    df = pd.read_csv(file)
    st.write(df)
    
    with open(file.name, 'wb') as out:
        out.write(file.getbuffer())