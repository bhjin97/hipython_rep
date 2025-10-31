# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import streamlit as st
from urllib.parse import quote_plus

try:
    from sqlalchemy import create_engine, text
except Exception:
    create_engine = None
    text = None

# ─────────────────────────────────────────────
# Streamlit 기본 설정
# ─────────────────────────────────────────────
st.set_page_config(page_title="Aller 주간 트렌드", page_icon="📈", layout="wide")
st.markdown("### 📈 사용자 대시보드 · 주간 트렌드(카테고리/제품)")

# ─────────────────────────────────────────────
# DB 접속(비밀번호 URL 인코딩)
# ─────────────────────────────────────────────
DB_USER = "lgup1"
DB_PASS = "lgup1P@ssw0rd"  # '@' 인코딩 주의
DB_HOST = "211.51.163.232"
DB_PORT = 19306
DB_NAME = "lgup1"

def make_url(u, p, h, port, db):
    return f"mysql+pymysql://{u}:{quote_plus(p)}@{h}:{port}/{db}?charset=utf8mb4"

DB_URL = make_url(DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME)

PRODUCT_TABLE = "product_data"
REVIEW_TABLE = "product_review_history_tmp"

# 카테고리 제한 목록
VALID_CATEGORIES = ["스킨/토너", "에센스/세럼/앰플", "크림", "선크림"]

# 컬럼 매핑
COLMAP_PRODUCT = {
    "pid": "product_id",
    "hash_id": "hash_id",
    "brand": "brand",
    "product_name": "product_name",
    "category": "category",
    "price_krw": "price_krw",
    "review_count": "review_count",  # baseline
    "image_url": "image_url",        # 옵션
    "product_url": "product_url",    # 옵션
}
COLMAP_REVIEW = {
    "hash_id": "hash_id",
    "period_start": "week_start",
    "review_count": "review_count_snap",  # 누적 스냅샷
}

# 기본설정
MIN_RECENT_CNT = 5
MIN_TWO_WEEKS = 10
WEEKS_DEFAULT = 4

PLACEHOLDER_IMG = "https://dummyimage.com/320x320/eeeeee/aaaaaa.png&text=No+Image"

# ─────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────
def to_int_safe(x):
    if pd.isna(x):
        return 0
    if isinstance(x, (int, np.integer)):
        return int(x)
    s = str(x).replace(",", "").strip()
    try:
        return int(float(s))
    except:
        return 0

def add_deltas(df: pd.DataFrame, key_cols: list, value_col: str) -> pd.DataFrame:
    d = df.sort_values(key_cols + ["week_start"]).copy()
    d["cnt_w_1"] = d.groupby(key_cols)[value_col].shift(1)
    d["cnt_w_2"] = d.groupby(key_cols)[value_col].shift(2)
    d["delta_abs"] = d[value_col] - d["cnt_w_1"].fillna(0)
    d["delta_pct"] = np.where(
        d["cnt_w_1"].fillna(0) == 0, np.nan,
        (d[value_col] - d["cnt_w_1"]) / d["cnt_w_1"]
    )
    growth_now = np.where(d["cnt_w_1"].fillna(0) == 0, np.nan, (d[value_col] - d["cnt_w_1"]) / d["cnt_w_1"])
    growth_prev = np.where(d["cnt_w_2"].fillna(0) == 0, np.nan, (d["cnt_w_1"] - d["cnt_w_2"]) / d["cnt_w_2"])
    d["accel_pct"] = growth_now - growth_prev
    return d

def sigmoid(x):
    try:
        return 1 / (1 + np.exp(-x))
    except Exception:
        return np.nan

def scale_01(s: pd.Series) -> pd.Series:
    if s.min() == s.max():
        return pd.Series(np.zeros_like(s), index=s.index)
    return (s - s.min()) / (s.max() - s.min())

def hot_score(df: pd.DataFrame, value_col: str, min_recent_cnt: int = MIN_RECENT_CNT, min_two_weeks_sum: int = MIN_TWO_WEEKS) -> pd.DataFrame:
    d = df.copy()
    d["recent_cnt"] = d[value_col]
    d["two_weeks_sum"] = d[value_col].fillna(0) + d["cnt_w_1"].fillna(0)
    valid = (d["recent_cnt"] >= min_recent_cnt) & (d["two_weeks_sum"] >= min_two_weeks_sum)
    d["delta_pct_sig"] = d["delta_pct"].apply(lambda x: sigmoid(x) if pd.notnull(x) else np.nan)
    d["delta_abs_scaled"] = scale_01(d["delta_abs"].fillna(0))
    d["recent_scaled"] = scale_01(d["recent_cnt"].fillna(0))
    is_new = d["cnt_w_1"].fillna(0) == 0
    base_score = 0.5 * d["delta_pct_sig"].fillna(0) + 0.3 * d["delta_abs_scaled"] + 0.2 * d["recent_scaled"]
    new_bonus = np.where(is_new, np.minimum(1.0, d["delta_abs_scaled"] * 1.2), 0.0)
    d["score"] = np.where(valid, np.minimum(1.0, base_score + new_bonus), np.nan)
    return d

# ─────────────────────────────────────────────
# 데이터 로드(+조인/계산)
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=True)
def load_all(db_url: str):
    if create_engine is None:
        raise RuntimeError("SQLAlchemy가 필요합니다. pip install sqlalchemy pymysql")

    eng = create_engine(db_url, pool_pre_ping=True)

    # 제품: 옵션 컬럼(image_url, product_url) 존재 유무에 대비
    products = pd.read_sql(text(f"SELECT * FROM {PRODUCT_TABLE}"), eng)
    need_cols = ["pid","hash_id","brand","product_name","category","price_krw","review_count","image_url","product_url"]
    for c in need_cols:
        if c not in products.columns:
            products[c] = np.nan
    products = products[need_cols]

    reviews = pd.read_sql(text(f"SELECT hash_id, period_start, review_count FROM {REVIEW_TABLE}"), eng)

    # 컬럼 통일/타입
    products = products.rename(columns=COLMAP_PRODUCT)
    reviews = reviews.rename(columns=COLMAP_REVIEW)

    products["product_id"] = products["product_id"].astype(int)
    products["hash_id"] = products["hash_id"].astype(str)
    products["review_count"] = products["review_count"].apply(to_int_safe).astype(int)

    reviews["hash_id"] = reviews["hash_id"].astype(str)
    reviews["week_start"] = pd.to_datetime(reviews["week_start"]).dt.tz_localize(None)
    reviews["review_count_snap"] = reviews["review_count_snap"].apply(to_int_safe).astype(int)

    # 카테고리 제한
    products["category"] = products["category"].where(products["category"].isin(VALID_CATEGORIES), other=np.nan)
    products = products.dropna(subset=["category"])

    # hash_id로 조인
    r = reviews.merge(
        products[["hash_id","product_id","category","brand","product_name","price_krw","review_count","image_url","product_url"]],
        on="hash_id",
        how="inner",
        validate="many_to_one"
    ).sort_values(["product_id","week_start"]).copy()

    # 스냅샷 단조증가 보정
    r["review_count_snap"] = r.groupby("product_id")["review_count_snap"].cummax()

    # baseline = 제품테이블 review_count
    baseline = r["review_count"].fillna(0).astype(int)

    # 전주 스냅샷(첫 주는 baseline)
    r["prev_snap"] = r.groupby("product_id")["review_count_snap"].shift(1)
    r["prev_snap"] = np.where(r["prev_snap"].isna(), baseline, r["prev_snap"])

    # 주간 증가/누적(베이스라인 대비)
    r["weekly_increment"] = (r["review_count_snap"] - r["prev_snap"]).clip(lower=0).astype(int)
    r["cum_delta_from_baseline"] = (r["review_count_snap"] - baseline).clip(lower=0).astype(int)

    max_week = r["week_start"].max() if not r.empty else None
    return products, r, max_week

# ─────────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────────
try:
    products, df_raw, max_week = load_all(DB_URL)
except Exception as e:
    st.error(f"DB 접속/로딩 실패: {e}")
    st.stop()

if df_raw.empty:
    st.warning("리뷰 히스토리 데이터가 없습니다.")
    st.stop()

# 최근 N주 범위
weeks_window = st.sidebar.slider("최근 N주(차트/히트맵 범위)", min_value=1, max_value=20, value=WEEKS_DEFAULT, step=1)
min_week = (pd.to_datetime(max_week) - pd.to_timedelta(weeks_window - 1, unit="W")).normalize()
df = df_raw[df_raw["week_start"] >= min_week].copy()

# 창 내 첫주차 대비(제품 기준)
df_sorted = df.sort_values(["product_id", "week_start"]).copy()
first_snap_in_window = df_sorted.groupby("product_id")["review_count_snap"].transform("first")
df_sorted["cum_delta_from_firstweek"] = (df_sorted["review_count_snap"] - first_snap_in_window).clip(lower=0).astype(int)

# 카테고리 합(제품 합산)
wcate_inc = df.groupby(["week_start","category"], as_index=False)["weekly_increment"].sum(min_count=1)
wcate_cum = df.groupby(["week_start","category"], as_index=False)["cum_delta_from_baseline"].sum(min_count=1)
wcate_first = df_sorted.groupby(["week_start","category"], as_index=False)["cum_delta_from_firstweek"].sum(min_count=1)

wcate_inc_d = add_deltas(wcate_inc.rename(columns={"weekly_increment":"value"}), ["category"], "value").rename(columns={"value":"weekly_increment"})
wcate_cum_d = add_deltas(wcate_cum.rename(columns={"cum_delta_from_baseline":"value"}), ["category"], "value").rename(columns={"value":"cum_delta_from_baseline"})
wcate_first_d = add_deltas(wcate_first.rename(columns={"cum_delta_from_firstweek":"value"}), ["category"], "value").rename(columns={"value":"cum_delta_from_firstweek"})

# ── 카테고리 레벨: 스냅샷 합 vs 베이스라인/첫주차(요구사항 핵심) ──
wcate_week = (
    df.groupby(["week_start", "category"], as_index=False)["review_count_snap"]
      .sum(min_count=1)
      .rename(columns={"review_count_snap": "snap_sum"})
)
cate_baseline = (
    products.groupby("category", as_index=False)["review_count"]
            .sum(min_count=1)
            .rename(columns={"review_count": "baseline_sum"})
)
first_week_by_cate = (
    wcate_week.sort_values(["category", "week_start"])
              .groupby("category", as_index=False)
              .first()[["category", "snap_sum"]]
              .rename(columns={"snap_sum": "firstweek_sum"})
)
wcate_lvl = (
    wcate_week.merge(cate_baseline, on="category", how="left")
              .merge(first_week_by_cate, on="category", how="left")
).sort_values(["category","week_start"])
wcate_lvl["delta_baseline"]  = (wcate_lvl["snap_sum"] - wcate_lvl["baseline_sum"]).clip(lower=0)
wcate_lvl["delta_firstweek"] = (wcate_lvl["snap_sum"] - wcate_lvl["firstweek_sum"]).clip(lower=0)

# 제품 단위 델타(랭킹용)
wprod_inc_d = add_deltas(df.copy(), ["product_id"], "weekly_increment")
wprod_cum_d = add_deltas(df.copy(), ["product_id"], "cum_delta_from_baseline")

# 최신 스냅샷/베이스라인(카드뷰 표시용)
latest_info = (
    df.sort_values(["product_id", "week_start"])
      .groupby("product_id")
      .agg(
          latest_week=("week_start", "last"),
          snapshot=("review_count_snap", "last"),
          baseline=("review_count", "first"),
          brand=("brand", "first"),
          product_name=("product_name", "first"),
          category=("category", "first"),
          image_url=("image_url", "first"),
          product_url=("product_url", "first"),
      )
      .reset_index()
)
latest_info["delta_from_baseline"] = (latest_info["snapshot"] - latest_info["baseline"]).clip(lower=0).astype(int)

# ─────────────────────────────────────────────
# 스타일(카드 UI)
# ─────────────────────────────────────────────
CARD_CSS = """
<style>
.card { border: 1px solid #eee; border-radius: 16px; padding: 12px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.06); height: 100%;
  display: flex; flex-direction: column; gap: 8px; background: #fff; }
.badge { display: inline-block; padding: 2px 8px; font-size: 12px; border-radius: 999px;
  background: #f1f5f9; color: #0f172a; margin-right: 6px; border: 1px solid #e2e8f0; }
.brand { font-weight: 600; color: #111827; font-size: 13px; }
.pname { font-weight: 700; color: #0f172a; line-height: 1.3; }
.kv { font-size: 12px; color: #334155; }
.kv b { color: #0f172a; }
.link a { font-size: 12px; text-decoration: none; color: #2563eb; }
.metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 12px; }
.metric { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 8px; text-align: center; }
.metric .val { font-weight: 700; font-size: 14px; color: #0f172a; }
.metric .lab { color: #64748b; font-size: 11px; }
</style>
"""
st.markdown(CARD_CSS, unsafe_allow_html=True)

def render_product_cards(df_cards: pd.DataFrame, cols: int = 4, max_items: int = 12):
    df_cards = df_cards.copy().head(max_items)
    n = len(df_cards)
    if n == 0:
        st.info("표시할 제품이 없습니다.")
        return
    rows = (n + cols - 1) // cols
    for r in range(rows):
        c = st.columns(cols)
        for i in range(cols):
            idx = r*cols + i
            if idx >= n: break
            row = df_cards.iloc[idx]
            img = row.get("image_url") or PLACEHOLDER_IMG
            brand = str(row.get("brand") or "")
            pname = str(row.get("product_name") or "")
            cate = str(row.get("category") or "")
            baseline = int(row.get("baseline") or 0)
            snapshot = int(row.get("snapshot") or 0)
            delta = int(row.get("delta_from_baseline") or 0)
            weekly_inc = int(row.get("weekly_increment") or 0)
            product_url = str(row.get("product_url") or "")

            with c[i]:
                st.image(img, use_container_width=True)
                st.markdown(
                    f"""
<div class="card">
  <div><span class="badge">{cate}</span></div>
  <div class="brand">{brand}</div>
  <div class="pname">{pname}</div>
  <div class="metrics">
    <div class="metric"><div class="val">{baseline}</div><div class="lab">베이스라인</div></div>
    <div class="metric"><div class="val">{snapshot}</div><div class="lab">최신 스냅샷</div></div>
    <div class="metric"><div class="val">{delta}</div><div class="lab">증가(누적)</div></div>
  </div>
  <div class="kv">주간증가: <b>{weekly_inc}</b></div>
  {"<div class='link'><a href='"+product_url+"' target='_blank'>상세보기</a></div>" if product_url and product_url != "nan" else ""}
</div>
                    """,
                    unsafe_allow_html=True
                )

# ─────────────────────────────────────────────
# UI 탭
# ─────────────────────────────────────────────
tab_trend, tab_hot, tab_personal, tab_heatmap = st.tabs(["변화추이(카테고리)", "핫 제품", "내 관심 핫템(데모)", "히트맵"])

# ---------- 변화추이(카테고리): 베이스라인/첫주차 기준 ----------
with tab_trend:
    st.subheader("카테고리 리뷰수 변화 — 기준 선택")
    basis = st.radio("표시 기준", ["베이스라인 대비 누적 증가", "첫주차 대비 누적 증가"], horizontal=True)

    available_categories = sorted(wcate_lvl["category"].dropna().unique().tolist())
    if not available_categories:
        st.info("선택한 기간에 카테고리 데이터가 없습니다. 좌측 슬라이더에서 기간을 늘려보세요.")
        st.stop()

    sel_categories = st.multiselect("카테고리 선택", options=available_categories, default=available_categories)
    show_ma = st.checkbox("3주 이동평균선 표시", value=True)

    plot_df = wcate_lvl[wcate_lvl["category"].isin(sel_categories)].copy()
    if basis == "베이스라인 대비 누적 증가":
        ycol, ytitle = "delta_baseline", "베이스라인 대비 누적 증가"
    else:
        ycol, ytitle = "delta_firstweek", "첫주차 대비 누적 증가"

    if plot_df.empty:
        st.warning("표시할 데이터가 없습니다. 기간/카테고리를 조정해 보세요.")
    else:
        import altair as alt
        weeks_n = plot_df["week_start"].nunique()

        if show_ma:
            plot_df["ma3"] = (
                plot_df.sort_values(["category","week_start"])
                       .groupby("category")[ycol]
                       .transform(lambda s: s.rolling(3, min_periods=1).mean())
            )

        line = alt.Chart(plot_df).mark_line().encode(
            x=alt.X("week_start:T", title="주(월요일 시작)"),
            y=alt.Y(f"{ycol}:Q", title=ytitle),
            color=alt.Color("category:N", title="카테고리"),
            tooltip=["week_start:T", "category:N", ycol]
        )
        st.altair_chart(line, use_container_width=True)

        if weeks_n <= 1:
            pts = alt.Chart(plot_df).mark_point(size=80).encode(
                x="week_start:T", y=f"{ycol}:Q", color="category:N"
            )
            st.altair_chart(pts, use_container_width=True)

        if show_ma and weeks_n >= 2:
            ma = alt.Chart(plot_df).mark_line(strokeDash=[3,3]).encode(
                x="week_start:T", y="ma3:Q", color="category:N"
            )
            st.altair_chart(ma, use_container_width=True)

# ---------- 핫 제품(카드/표) ----------
with tab_hot:
    st.subheader("핫 제품")
    latest_week = df["week_start"].max()
    st.caption(f"기준 주: {pd.to_datetime(latest_week).date()} 시작 주")
    sel_cate_for_hot = st.selectbox("카테고리 선택", ["(전체)"] + sorted(products["category"].unique().tolist()))
    basis = st.radio("스코어 기준", ["주간 증가분", "베이스라인 대비 누적 증가"], horizontal=True)
    view_mode = st.radio("보기 형식", ["카드 보기", "표 보기"], horizontal=True)

    cur_inc = wprod_inc_d[wprod_inc_d["week_start"] == latest_week].copy()
    cur_cum = wprod_cum_d[wprod_cum_d["week_start"] == latest_week].copy()
    if sel_cate_for_hot != "(전체)":
        cur_inc = cur_inc[cur_inc["category"] == sel_cate_for_hot]
        cur_cum = cur_cum[cur_cum["category"] == sel_cate_for_hot]

    if basis == "주간 증가분":
        cur = hot_score(cur_inc, "weekly_increment").sort_values("score", ascending=False).head(50)
        cur["기준값"] = cur["weekly_increment"].fillna(0).astype(int)
    else:
        cur = hot_score(cur_cum, "cum_delta_from_baseline").sort_values("score", ascending=False).head(50)
        cur["기준값"] = cur["cum_delta_from_baseline"].fillna(0).astype(int)

    # 지표만 합침(이미지/링크는 cur에 존재)
    cur = cur.merge(
        latest_info[["product_id","baseline","snapshot","delta_from_baseline"]],
        on="product_id", how="left"
    )

    cur["스코어"] = (cur["score"] * 100).round(1)
    cur["주간증가"] = cur["weekly_increment"].fillna(0).astype(int)
    cur["누적증가"] = cur["cum_delta_from_baseline"].fillna(0).astype(int)

    if view_mode == "카드 보기":
        render_product_cards(cur, cols=4, max_items=12)
    else:
        cur = cur.rename(columns={
            "baseline": "제품테이블(베이스라인)",
            "snapshot": "히스토리(최신 스냅샷)",
            "delta_from_baseline": "스냅샷-베이스라인",
        })
        st.dataframe(
            cur[["brand","product_name","category",
                 "제품테이블(베이스라인)","히스토리(최신 스냅샷)","스냅샷-베이스라인",
                 "주간증가","누적증가","기준값","스코어"]],
            use_container_width=True
        )

# ---------- 개인화(데모) ----------
with tab_personal:
    st.subheader("내 관심사 기반 핫템(데모) — 정확일치 필터는 이후 연동")
    latest_week = df["week_start"].max()
    base = wprod_inc_d[wprod_inc_d["week_start"] == latest_week].copy()
    base = hot_score(base, "weekly_increment").sort_values("score", ascending=False).head(30)
    base["스코어"] = (base["score"] * 100).round(1)
    base["주간증가"] = base["weekly_increment"].fillna(0).astype(int)
    base["누적증가"] = base["cum_delta_from_baseline"].fillna(0).astype(int)
    st.dataframe(base[["brand","product_name","category","주간증가","누적증가","스코어"]], use_container_width=True)

# ---------- 히트맵 ----------
with tab_heatmap:
    st.subheader("주차 × 카테고리 히트맵")
    metric_mode = st.selectbox("색상값", ["주간 증가분", "베이스라인 대비 누적 증가", "전주 대비 증가폭(Δ)", "전주 대비 증가율(%)"])
    norm_mode = st.radio("정규화", ["전역 공통 스케일", "행(카테고리)별 z-score"], horizontal=True)

    if metric_mode == "주간 증가분":
        pivot_src = wcate_inc_d.copy(); metric_col = "weekly_increment"
    elif metric_mode == "베이스라인 대비 누적 증가":
        pivot_src = wcate_cum_d.copy(); metric_col = "cum_delta_from_baseline"
    elif metric_mode == "전주 대비 증가폭(Δ)":
        pivot_src = wcate_inc_d.copy(); metric_col = "delta_abs"
    else:
        pivot_src = wcate_inc_d.copy(); metric_col = "delta_pct"

    pivot_src["week_label"] = pivot_src["week_start"].dt.strftime("%Y-%m-%d")
    if metric_col == "delta_pct":
        pivot = pivot_src.pivot_table(index="category", columns="week_label", values=metric_col, aggfunc="mean") * 100.0
    else:
        pivot = pivot_src.pivot_table(index="category", columns="week_label", values=metric_col, aggfunc="sum")

    if norm_mode == "행(카테고리)별 z-score":
        z = pivot.fillna(0).copy()
        mu = z.mean(axis=1); sd = z.std(axis=1).replace(0, np.nan)
        pivot_norm = (z.sub(mu, axis=0)).div(sd, axis=0)
    else:
        v = pivot.values.flatten(); v = v[~np.isnan(v)]
        if len(v) == 0 or np.nanmax(v) == np.nanmin(v):
            pivot_norm = pivot.copy() * 0.0
        else:
            mn, mx = np.nanmin(v), np.nanmax(v); pivot_norm = (pivot - mn) / (mx - mn)

    import altair as alt
    plot_df = pivot_norm.reset_index().melt(id_vars="category", var_name="week", value_name="value")
    base = alt.Chart(plot_df).mark_rect().encode(
        x=alt.X("week:N", sort=sorted(plot_df["week"].unique()), title="주(월요일 시작)"),
        y=alt.Y("category:N", sort=sorted(plot_df["category"].unique()), title="카테고리"),
        color=alt.Color("value:Q", title="정규화값"),
        tooltip=["category:N", "week:N", "value:Q"]
    ).properties(height=500)
    st.altair_chart(base, use_container_width=True)
