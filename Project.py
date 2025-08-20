from __future__ import annotations
import os
import random
from datetime import datetime, timedelta, date, time
from typing import List

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
from streamlit_folium import st_folium
import folium

# -------------------------------------------------------------
# 페이지 설정
# -------------------------------------------------------------
st.set_page_config(
    page_title="사용자 대시보드",
    page_icon="👤",
    layout="wide",
)

# -------------------------------------------------------------
# 더미 데이터 생성 유틸
# -------------------------------------------------------------
def seed_everything(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)


def make_dummy_usage(days: int = 90) -> pd.DataFrame:
    """일자별 사용 시간(분) + 시간대별 사용 히트맵용 데이터 생성"""
    end = pd.to_datetime(date.today())
    start = end - pd.Timedelta(days=days - 1)
    dates = pd.date_range(start, end, freq="D")
    minutes = np.clip(np.random.normal(loc=45, scale=25, size=len(dates)).astype(int), 0, 180)
    df_daily = pd.DataFrame({"date": dates.date, "minutes": minutes})

    # 시간대별(0~23시) 사용량 히트맵용 – 평일/주말 패턴 다르게
    rows = []
    for d, m in zip(dates, minutes):
        # 하루 총 사용 분을 무작위 시간대에 분배
        remain = m
        while remain > 0:
            h = np.random.choice(range(24), p=_hour_prob())
            chunk = np.random.randint(1, min(10, remain + 1))
            rows.append({"date": d.date(), "hour": h, "minutes": chunk})
            remain -= chunk
    df_heat = pd.DataFrame(rows)
    return df_daily, df_heat


def _hour_prob() -> np.ndarray:
    """시간대 분포(저녁/야간 가중치)"""
    base = np.array([
        0.02, 0.01, 0.01, 0.01, 0.01,  # 0~4
        0.02, 0.02, 0.03, 0.03, 0.04,  # 5~9
        0.05, 0.05, 0.05, 0.05, 0.05,  # 10~14
        0.05, 0.06, 0.07, 0.08, 0.1,   # 15~19
        0.09, 0.08, 0.06, 0.05         # 20~23
    ])
    return base / base.sum()


def make_dummy_moods(days: int = 30) -> pd.DataFrame:
    """감정 점수(joy/anger/sadness/fear/neutral)와 mood_score(가상의 종합지수)"""
    end = pd.to_datetime(date.today())
    start = end - pd.Timedelta(days=days - 1)
    dates = pd.date_range(start, end, freq="D").date

    records = []
    for d in dates:
        joy = np.clip(np.random.beta(5, 2), 0, 1)
        anger = np.clip(np.random.beta(2, 6), 0, 1)
        sadness = np.clip(np.random.beta(2, 6), 0, 1)
        fear = np.clip(np.random.beta(2, 7), 0, 1)
        neutral = max(0.0, 1.0 - (joy + anger + sadness + fear))
        mood_score = (joy * 2 + neutral) - (anger + sadness + fear)
        records.append({
            "date": d,
            "joy": joy,
            "anger": anger,
            "sadness": sadness,
            "fear": fear,
            "neutral": neutral,
            "mood_score": mood_score,
        })
    return pd.DataFrame(records)


def make_dummy_hospitals(n: int = 25, center=(37.5665, 126.9780)) -> pd.DataFrame:
    """서울 시청 부근 랜덤 병원 좌표 더미"""
    lat0, lon0 = center
    lat = lat0 + np.random.uniform(-0.05, 0.05, size=n)
    lon = lon0 + np.random.uniform(-0.05, 0.05, size=n)
    name = [f"병원 {i+1}" for i in range(n)]
    dept = np.random.choice(["내과", "정형외과", "이비인후과", "소아과", "정신건강의학과"], size=n)
    return pd.DataFrame({"name": name, "lat": lat, "lon": lon, "dept": dept})


def make_dummy_recs(k: int = 6) -> pd.DataFrame:
    titles = [
        "Calm Breeze", "Sunny Day", "Midnight Walk", "Focus Flow", "Morning Dew", "Deep Relax",
        "Soft Light", "Blue Hour", "Warm Coffee",
    ]
    artists = ["Nova", "Luna", "Echo", "Atlas", "Mira", "Sol"]
    imgs = [
        "https://picsum.photos/seed/a/300/300",
        "https://picsum.photos/seed/b/300/300",
        "https://picsum.photos/seed/c/300/300",
        "https://picsum.photos/seed/d/300/300",
        "https://picsum.photos/seed/e/300/300",
        "https://picsum.photos/seed/f/300/300",
    ]
    rows = []
    for i in range(k):
        rows.append({
            "title": random.choice(titles),
            "artist": random.choice(artists),
            "album_img": random.choice(imgs),
            "reason": random.choice(["요즘 기분에 맞는 추천", "집중에 도움", "편안한 분위기"]),
        })
    return pd.DataFrame(rows)


seed_everything(7)

# 세션 상태에 사용자 프로필(더미) 초기화
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "nickname": "형진",
        "avatar_url": "https://avatars.githubusercontent.com/u/9919?s=200&v=4",
        "language": "ko",
        "theme": "light",
        "notify": True,
        "favorites": ["감정 분석", "병원 지도"],
        "location": (37.5665, 126.9780),  # 서울시청
    }

# 더미 데이터 로딩
DF_DAILY, DF_HEAT = make_dummy_usage(days=90)
DF_MOODS = make_dummy_moods(days=30)
DF_HOSP = make_dummy_hospitals(n=25, center=st.session_state.user_profile["location"])
DF_RECS = make_dummy_recs(k=6)

# -------------------------------------------------------------
# UI – 사이드바: 계정 정보 & 설정
# -------------------------------------------------------------
with st.sidebar:
    st.image(st.session_state.user_profile["avatar_url"], width=72)
    st.markdown(f"**{st.session_state.user_profile['nickname']}님**")

    st.write("\n")
    st.subheader("설정")
    theme = st.selectbox("테마", ["light", "dark", "system"], index=["light","dark","system"].index(st.session_state.user_profile["theme"]))
    lang = st.selectbox("언어", ["ko", "en"], index=["ko","en"].index(st.session_state.user_profile["language"]))
    notify = st.toggle("알림 받기", value=st.session_state.user_profile["notify"])

    if st.button("설정 저장", use_container_width=True):
        st.session_state.user_profile.update({"theme": theme, "language": lang, "notify": notify})
        st.success("설정이 저장되었습니다.")

st.title("👤 사용자 대시보드")

# 상단 공통 필터(기간)
col_f1, col_f2, col_f3 = st.columns([1,1,2])
with col_f1:
    days_range = st.selectbox("기간", [7, 14, 30, 60, 90], index=2, help="최근 N일")
with col_f2:
    view_mode = st.radio("보기", ["개요", "상세"], horizontal=True)
with col_f3:
    st.caption("필터를 변경하면 아래 위젯들이 갱신됩니다.")

# 필터 적용
cutoff = pd.to_datetime(date.today()) - pd.Timedelta(days=days_range - 1)
DF_DAILY_F = DF_DAILY[DF_DAILY["date"] >= cutoff.date()].copy()
DF_HEAT_F = DF_HEAT[DF_HEAT["date"] >= cutoff.date()].copy()
DF_MOODS_F = DF_MOODS[DF_MOODS["date"] >= cutoff.date()].copy()

# -------------------------------------------------------------
# 섹션 1) 사용 패턴 – 일별 사용시간(바) + 시간대 히트맵
# -------------------------------------------------------------
st.subheader("📈 사용 패턴")

c1, c2 = st.columns([2, 3])
with c1:
    st.markdown("**날짜별 사용시간(분)**")
    fig_daily = px.bar(DF_DAILY_F, x="date", y="minutes", labels={"date": "날짜", "minutes": "분"})
    fig_daily.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=300)
    st.plotly_chart(fig_daily, use_container_width=True)

with c2:
    st.markdown("**시간대별 사용 히트맵**")
    # pivot: rows=date, cols=hour, values=sum(minutes)
    pivot = DF_HEAT_F.pivot_table(index="date", columns="hour", values="minutes", aggfunc="sum", fill_value=0)
    fig_heat = px.imshow(
        pivot,
        labels=dict(x="시간(시)", y="날짜", color="분"),
        aspect="auto",
        color_continuous_scale="Blues",
    )
    fig_heat.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=300)
    st.plotly_chart(fig_heat, use_container_width=True)

# -------------------------------------------------------------
# 섹션 2) 병원 지도 – folium
# -------------------------------------------------------------
st.subheader("🗺️ 병원 지도")

with st.expander("내 위치/병원 보기", expanded=True):
    user_lat, user_lon = st.session_state.user_profile["location"]
    map_obj = folium.Map(location=[user_lat, user_lon], zoom_start=13, control_scale=True)

    folium.Marker([user_lat, user_lon], popup="내 위치", icon=folium.Icon(color="red", icon="user")).add_to(map_obj)

    # 마커 클러스터(선택)
    try:
        from folium.plugins import MarkerCluster
        mc = MarkerCluster()
        for r in DF_HOSP.itertuples():
            folium.Marker([r.lat, r.lon], popup=f"{r.name} / {r.dept}").add_to(mc)
        mc.add_to(map_obj)
    except Exception:
        for r in DF_HOSP.itertuples():
            folium.Marker([r.lat, r.lon], popup=f"{r.name} / {r.dept}").add_to(map_obj)

    st_folium(map_obj, height=420, returned_objects=[])

# -------------------------------------------------------------
# 섹션 3) 감정 분석 – 레이더 차트 + 기간별 추이
# -------------------------------------------------------------
st.subheader("😊 감정 분석")

col_m1, col_m2 = st.columns([2, 3])
with col_m1:
    st.markdown("**감정 분포(최근 평균)**")
    emotions = ["joy", "anger", "sadness", "fear", "neutral"]
    recent_avg = DF_MOODS_F[emotions].mean().to_dict()
    df_radar = pd.DataFrame({
        "emotion": emotions,
        "score": [recent_avg[e] for e in emotions]
    })
    fig_radar = px.line_polar(df_radar, r="score", theta="emotion", line_close=True)
    fig_radar.update_traces(fill='toself')
    fig_radar.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=340)
    st.plotly_chart(fig_radar, use_container_width=True)

with col_m2:
    st.markdown("**기간별 감정 변화(종합 지수)**")
    fig_line = px.line(DF_MOODS_F, x="date", y="mood_score", labels={"date": "날짜", "mood_score": "지수"})
    fig_line.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=340)
    st.plotly_chart(fig_line, use_container_width=True)

# -------------------------------------------------------------
# 섹션 4) 음악 추천 – 카드 UI
# -------------------------------------------------------------
st.subheader("🎵 음악 추천")

cols = st.columns(3)
for i, r in enumerate(DF_RECS.itertuples(index=False)):
    with cols[i % 3]:
        st.image(r.album_img, use_container_width=True)
        st.markdown(f"**{r.title}** – {r.artist}")
        st.caption(r.reason)
        st.button("재생", key=f"play_{i}")

# -------------------------------------------------------------
# 푸터/정보
# -------------------------------------------------------------
st.divider()
st.caption("v0.1 – 더미 데이터 기반 MVP • 구성: 계정/사용패턴/병원지도/감정/추천")
