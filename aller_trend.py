# -*- coding: utf-8 -*-
import os
from urllib.parse import quote_plus
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────────────────────────────────────────
# 기본 설정
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Aller · 리뷰 트렌드 (사용자 친화형)", page_icon="📈", layout="wide")
st.markdown("## 📈 전 카테고리 리뷰 트렌드 · 주차 비교 / 핫 제품 / 쏠림 지수(지니)")

# 카테고리 표준화
ALLOWED_CATEGORIES = ["스킨/토너", "에센스/세럼/앰플", "크림", "선크림"]
CATEGORY_MAP = {
    "스킨 / 토너": "스킨/토너", "스킨·토너": "스킨/토너",
    "에센스/ 세럼/앰플": "에센스/세럼/앰플", "에센스/세럼/ 앰플": "에센스/세럼/앰플",
    "선 케어/선크림": "선크림", "선케어/선크림": "선크림", "선크림/선케어": "선크림",
}

# DB 설정
DB_DIALECT = os.getenv("DB_DIALECT", "mysql+pymysql")
DB_HOST    = os.getenv("DB_HOST", "211.51.163.232")
DB_PORT    = os.getenv("DB_PORT", "19306")
DB_USER    = os.getenv("DB_USER", "lgup1")
DB_PASS    = os.getenv("DB_PASSWORD", "lgup1P@ssw0rd")
DB_NAME    = os.getenv("DB_NAME", "lgup1")
DB_URL     = f"{DB_DIALECT}://{DB_USER}:{quote_plus(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

TABLE_PRODUCT = "product_data"
TABLE_HISTORY = "product_review_history_tmp"
engine = create_engine(DB_URL, pool_recycle=3600)


# ─────────────────────────────────────────────────────────────────────────────
# 유틸 함수
# ─────────────────────────────────────────────────────────────────────────────
def norm_cat(v):
    if pd.isna(v): return v
    return " ".join(str(v).strip().replace("\\", "/").split())

def labelize(x): 
    return "베이스" if x == "BASE" else str(x)

def gini_coefficient(arr: np.ndarray) -> float:
    x = np.asarray(arr, dtype=float)
    if x.size == 0 or np.all(x == 0): 
        return 0.0
    x = np.sort(x)
    n  = x.size
    cumx = np.cumsum(x)
    # 1 + 1/n - 2 * (sum(cumx) / (n * cumx[-1]))
    return float(1.0 + 1.0/n - 2.0*(cumx.sum()/(n*cumx[-1])))

def contribution_ratio(deltas: np.ndarray, top_ratio: float) -> float:
    """
    상위 top_ratio(0~1)의 제품이 만든 증가 비중(0~1)
    """
    vec = np.asarray(deltas, dtype=float)
    vec = vec[vec > 0]  # 증가만
    if vec.size == 0: 
        return 0.0
    vec = np.sort(vec)[::-1]
    k   = max(1, int(np.ceil(len(vec) * top_ratio)))
    top = vec[:k].sum()
    return float(top / vec.sum())

def grade_from_gini(g: float) -> tuple[str, str]:
    """지니 등급(라벨, 색상)"""
    if g <= 0.30: 
        return ("낮음", "🟢")
    if g <= 0.50: 
        return ("보통", "🟡")
    return ("높음", "🔴")

@st.cache_data(ttl=300)
def load_all():
    with engine.connect() as conn:
        df_prod = pd.read_sql(text(f"""
            SELECT hash_id, product_name, brand, image_url, product_url,
                   category AS category, CAST(review_count AS SIGNED) AS review_base
            FROM {TABLE_PRODUCT}
        """), conn)
        df_hist = pd.read_sql(text(f"""
            SELECT hash_id, DATE(period_start) AS week_date,
                   CAST(review_count AS SIGNED) AS review_count
            FROM {TABLE_HISTORY}
        """), conn)
    return df_prod, df_hist

def ids_with_label(label, hist, prod):
    if label == "BASE": 
        return set(prod["hash_id"])
    wk = pd.to_datetime(label).date()
    return set(hist.loc[hist["week_date"] == wk, "hash_id"])

def get_counts(label, hist, prod):
    if label == "BASE":
        return prod[["hash_id", "review_base"]].rename(columns={"review_base":"value"}).copy()
    wk = pd.to_datetime(label).date()
    tmp = hist[hist["week_date"] == wk][["hash_id", "review_count"]]
    return tmp.rename(columns={"review_count":"value"}).copy()

def compute_filtered_ab(df_prod_cat, df_hist_cat, a_label, b_label):
    """A/B 교집합 → 감소 제거 → IQR 상한 제거까지 일괄 반환"""
    ids_a = ids_with_label(a_label, df_hist_cat, df_prod_cat)
    ids_b = ids_with_label(b_label, df_hist_cat, df_prod_cat)
    valid_ids = ids_a & ids_b
    if not valid_ids:
        return pd.DataFrame(), pd.DataFrame(), set()

    prod = df_prod_cat[df_prod_cat["hash_id"].isin(valid_ids)].copy()
    hist = df_hist_cat[df_hist_cat["hash_id"].isin(valid_ids)].copy()

    a_df = get_counts(a_label, hist, prod).rename(columns={"value":"value_a"})
    b_df = get_counts(b_label, hist, prod).rename(columns={"value":"value_b"})
    ab  = (prod[["hash_id","product_name","brand","image_url","product_url","review_base"]]
           .merge(a_df, on="hash_id", how="inner")
           .merge(b_df, on="hash_id", how="inner"))
    ab["delta_review"] = ab["value_b"] - ab["value_a"]

    pos = ab[ab["delta_review"] > 0].copy()
    if pos.empty:
        return ab, pos, valid_ids

    q1, q3 = pos["delta_review"].quantile([0.25, 0.75])
    upper  = q3 + 1.5 * (q3 - q1)
    pos_iqr = pos[pos["delta_review"] <= upper].copy()
    return ab, pos_iqr, valid_ids


# ─────────────────────────────────────────────────────────────────────────────
# 사용자 친화형: 쏠림 지수 카드
# ─────────────────────────────────────────────────────────────────────────────
def render_concentration_card(deltas: pd.Series, title: str = "🎯 쏠림 지수(지니)") -> None:
    """
    deltas: 증가량 시리즈(양수만 들어오는 것이 이상적이나, 함수 내부에서 양수 필터링)
    """
    vec = deltas.values if isinstance(deltas, pd.Series) else np.asarray(deltas)
    vec = np.asarray(vec, dtype=float)
    vec = vec[vec > 0]  # 증가만

    card = st.container()
    with card:
        st.markdown(f"#### {title}")

        if vec.size == 0:
            st.info("계산할 증가 데이터가 없습니다.")
            return

        gini = gini_coefficient(vec)
        cr20 = contribution_ratio(vec, 0.20)
        cr10 = contribution_ratio(vec, 0.10)
        grade, dot = grade_from_gini(gini)

        # 상단 배지 + 요약
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("쏠림 등급", f"{dot} {grade}", help="지니계수를 등급화한 값")
        with col_b:
            st.metric("상위 20% 기여", f"{cr20*100:,.1f} %")
        with col_c:
            st.metric("상위 10% 기여", f"{cr10*100:,.1f} %")

        # 한 줄 요약
        st.caption(f"소수 제품에 집중된 정도: 지니 {gini:.3f} — 상위 20%가 전체 증가의 {cr20*100:.1f}%를 만듭니다.")

        # 로렌츠 곡선(음영) + 마커(10%, 20%)
        x_sorted = np.sort(vec)               # 오름차순
        cum = np.cumsum(x_sorted)
        lorenz = np.insert(cum/cum[-1], 0, 0) # 0으로 시작
        p = np.linspace(0, 1, len(lorenz))    # 누적 제품 비중

        lor_df = pd.DataFrame({"p": p, "L": lorenz})
        diag_df = pd.DataFrame({"x":[0,1], "y":[0,1]})

        area = alt.Chart(lor_df).mark_area(opacity=0.2).encode(
            x=alt.X("p:Q", axis=alt.Axis(format="%"), title="누적 제품 비중"),
            y=alt.Y("L:Q", axis=alt.Axis(format="%"), title="누적 증가 비중")
        )
        line = alt.Chart(lor_df).mark_line().encode(x="p:Q", y="L:Q")
        diag = alt.Chart(diag_df).mark_line(strokeDash=[4,4]).encode(x="x:Q", y="y:Q")

        # 마커(0.1, 0.2에서의 누적 증가 비중)
        def point_at(frac):
            idx = int(round(frac * (len(lor_df)-1)))
            return float(lor_df.iloc[idx]["L"])
        m10 = point_at(0.10); m20 = point_at(0.20)
        pts_df = pd.DataFrame({"p":[0.10, 0.20], "L":[m10, m20], "label":["10%","20%"]})
        pts = alt.Chart(pts_df).mark_point(size=80).encode(x="p:Q", y="L:Q", tooltip=["label","L"])
        txt = alt.Chart(pts_df).mark_text(dy=-10).encode(x="p:Q", y="L:Q", text="label")

        st.altair_chart((area + line + diag + pts + txt).properties(height=260), use_container_width=True)

        # 파레토 미니바(Top 30)
        pareto = pd.DataFrame({"delta": np.sort(vec)[::-1]})
        pareto = pareto.head(min(30, len(pareto))).reset_index(drop=True)
        pareto["rank"] = pareto.index + 1
        pareto["cum_pct"] = pareto["delta"].cumsum() / pareto["delta"].sum()

        bars = alt.Chart(pareto).mark_bar().encode(
            x=alt.X("rank:O", title="상위 제품 순위"),
            y=alt.Y("delta:Q", title="증가 기여"),
            tooltip=[alt.Tooltip("rank:Q", title="순위"),
                     alt.Tooltip("delta:Q", title="증가", format=",.0f"),
                     alt.Tooltip("cum_pct:Q", title="누적 비중", format=".1%")]
        )
        line2 = alt.Chart(pareto).mark_line(point=True, opacity=0.8).encode(
            x="rank:O",
            y=alt.Y("cum_pct:Q", title="누적 비중", axis=alt.Axis(format="%"))
        )
        st.altair_chart((bars + line2).properties(height=220), use_container_width=True)

        st.caption("※ 그래프에는 공통 규칙(교집합 제품만 · 감소 제외 · IQR 상한) 통과 데이터만 사용됩니다.")


# ─────────────────────────────────────────────────────────────────────────────
# 데이터 로드 & 전처리
# ─────────────────────────────────────────────────────────────────────────────
df_prod_all, df_hist_all = load_all()
if df_prod_all.empty or df_hist_all.empty:
    st.warning("데이터가 비어 있습니다. product_data / product_review_history_tmp 테이블을 확인하세요.")
    st.stop()

df_prod_all["category"] = df_prod_all["category"].apply(norm_cat).replace(CATEGORY_MAP)
df_prod_all = df_prod_all[df_prod_all["category"].isin(ALLOWED_CATEGORIES)].copy()

# 히스토리 표준화 + 제품 조인
df_hist_all = (df_hist_all.groupby(["hash_id","week_date"], as_index=False)["review_count"].max())
df_hist_all = df_hist_all.merge(df_prod_all[["hash_id","category","brand"]], on="hash_id", how="inner")

# 주차/카테고리
all_weeks = sorted(df_hist_all["week_date"].unique())
latest_week = all_weeks[-1] if all_weeks else None
all_categories = [c for c in ALLOWED_CATEGORIES if c in df_prod_all["category"].unique().tolist()]


# ─────────────────────────────────────────────────────────────────────────────
# 상단: 카테고리 점유율(증가 기준) + 한 줄 브리핑
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 🧭 카테고리 점유율 — 증가 리뷰수 기준 (A→B)")

c1, c2, _ = st.columns([1,1,2])
with c1:
    share_a = st.selectbox("A(기준)", ["BASE"] + [str(w) for w in all_weeks], index=0, key="share_a")
with c2:
    default_idx = (["BASE"] + [str(w) for w in all_weeks]).index(str(latest_week)) if latest_week else 0
    share_b = st.selectbox("B(비교)", ["BASE"] + [str(w) for w in all_weeks], index=default_idx, key="share_b")

rows = []
for cat in all_categories:
    prod_c = df_prod_all[df_prod_all["category"] == cat].copy()
    hist_c = df_hist_all[df_hist_all["category"] == cat].copy()
    _, pos_iqr, _ = compute_filtered_ab(prod_c, hist_c, share_a, share_b)
    if not pos_iqr.empty:
        rows.append({"category": cat, "delta_sum": int(pos_iqr["delta_review"].sum())})
share_df = pd.DataFrame(rows).sort_values("delta_sum", ascending=False)

if share_df.empty:
    st.info("표시할 증가 데이터가 없습니다. (선택한 A/B 또는 데이터 상태 확인)")
else:
    pie = alt.Chart(share_df).mark_arc(innerRadius=60).encode(
        theta=alt.Theta("delta_sum:Q", title="증가 합계"),
        color=alt.Color("category:N", title="카테고리"),
        tooltip=[alt.Tooltip("category:N", title="카테고리"),
                 alt.Tooltip("delta_sum:Q", title="증가 합계", format=",.0f"),
                 alt.Tooltip("percent:Q", title="비중", format=".1%")]
    ).transform_window(total="sum(delta_sum)").transform_calculate(
        percent="datum.delta_sum / datum.total"
    ).properties(height=300)
    st.altair_chart(pie, use_container_width=True)

    # 한 줄 브리핑
    if len(share_df) >= 2:
        top1, top2 = share_df.iloc[0], share_df.iloc[1]
        st.info(f"이번 구간 증가 비중 TOP: **{top1['category']}**(+{top1['delta_sum']:,}) → 다음은 **{top2['category']}**(+{top2['delta_sum']:,}). "
                f"A={labelize(share_a)} → B={labelize(share_b)} 기준, 교집합·감소제외·IQR상한 적용.")
st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# 카테고리 탭
# ─────────────────────────────────────────────────────────────────────────────
tabs = st.tabs([f"🧴 {c}" for c in all_categories])

for tab, cat in zip(tabs, all_categories):
    with tab:
        st.markdown(f"### {cat}")

        df_cat_prod = df_prod_all[df_prod_all["category"]==cat].copy()
        df_cat_hist = df_hist_all[df_hist_all["category"]==cat].copy()
        if df_cat_prod.empty or df_cat_hist.empty:
            st.info("이 카테고리에 데이터가 없습니다.")
            continue

        # A vs B 선택
        c1, c2, _ = st.columns([1,1,2])
        with c1:
            a_label = st.selectbox("A(왼쪽)", ["BASE"] + [str(w) for w in all_weeks], index=0, key=f"a_{cat}")
        with c2:
            default_idx = (["BASE"] + [str(w) for w in all_weeks]).index(str(latest_week)) if latest_week else 0
            b_label = st.selectbox("B(오른쪽)", ["BASE"] + [str(w) for w in all_weeks], index=default_idx, key=f"b_{cat}")

        ab_all, pos_iqr, valid_ids = compute_filtered_ab(df_cat_prod, df_cat_hist, a_label, b_label)
        if not valid_ids:
            st.info("두 구간 교집합 제품이 없습니다.")
            continue

        # 상단 요약(총합 막대)
        a_total = int(pos_iqr["value_a"].sum()) if not pos_iqr.empty else 0
        b_total = int(pos_iqr["value_b"].sum()) if not pos_iqr.empty else 0

        left, right = st.columns([1,2.2], gap="large")
        with left:
            st.metric(f"총 리뷰(A={labelize(a_label)})", f"{a_total:,}")
            st.metric(f"총 리뷰(B={labelize(b_label)})", f"{b_total:,}", delta=f"{(b_total-a_total):+,}")
            st.caption("🔒 공통 규칙: 교집합 제품만 · 감소 제외 · IQR 상한")
        with right:
            totals_df = pd.DataFrame({"label":[labelize(a_label), labelize(b_label)], "sum":[a_total,b_total]})
            st.altair_chart(
                alt.Chart(totals_df).mark_bar().encode(
                    x=alt.X("label:N", sort=[labelize(a_label), labelize(b_label)], title=""),
                    y=alt.Y("sum:Q", title="합계"),
                    tooltip=[alt.Tooltip("label:N", title="구간"), alt.Tooltip("sum:Q", title="합계", format=",.0f")]
                ).properties(height=260),
                use_container_width=True
            )

        st.markdown("----")

        # 🔥 핫 제품 Top4
        st.markdown("#### 🔥 이 주의 핫 제품 (증가폭 Top 4)")
        if pos_iqr.empty:
            st.info("핫 제품 후보가 없습니다.")
        else:
            for _, r in pos_iqr.sort_values("delta_review", ascending=False).head(4).iterrows():
                cimg, cdesc = st.columns([1,4])
                with cimg:
                    if isinstance(r["image_url"], str) and r["image_url"].startswith(("http://","https://")):
                        st.image(r["image_url"], use_column_width=True)
                with cdesc:
                    st.markdown(f"**{r['brand']} · {r['product_name']}**")
                    st.markdown(f"- A({labelize(a_label)}): **{int(r['value_a']):,}**")
                    st.markdown(f"- B({labelize(b_label)}): **{int(r['value_b']):,}**")
                    st.markdown(f"- 증가폭: **+{int(r['delta_review']):,}**")
                    if isinstance(r["product_url"], str) and r["product_url"].startswith(("http://","https://")):
                        st.markdown(f"[상품 페이지]({r['product_url']})")
                st.divider()

        st.markdown("----")

        # 🎯 쏠림 지수(지니) — 사용자 친화형 카드
        render_concentration_card(pos_iqr["delta_review"], title="🎯 쏠림 지수(지니) — 집중도 해석")
