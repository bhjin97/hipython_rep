# -*- coding: utf-8 -*-
import os
from urllib.parse import quote_plus
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
from sqlalchemy import create_engine, text

# ───────────────── 기본 설정 ─────────────────
st.set_page_config(page_title="Aller · 전 카테고리 리뷰 트렌드", page_icon="📈", layout="wide")
st.markdown("## 📈 전 카테고리 리뷰 트렌드 · 주차 비교 / 핫 제품 / 점유율·기여도")

# ───────── 고정 카테고리 + 표기 보정 ─────────
ALLOWED_CATEGORIES = ["스킨/토너", "에센스/세럼/앰플", "크림", "선크림"]
CATEGORY_MAP = {
    "스킨 / 토너": "스킨/토너", "스킨·토너": "스킨/토너",
    "에센스/ 세럼/앰플": "에센스/세럼/앰플", "에센스/세럼/ 앰플": "에센스/세럼/앰플",
    "선 케어/선크림": "선크림", "선케어/선크림": "선크림", "선크림/선케어": "선크림",
}

# ───────────────── DB ─────────────────
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

# ───────── 유틸 ─────────
def norm_cat(v):
    if pd.isna(v): return v
    return " ".join(str(v).strip().replace("\\", "/").split())

def labelize(x): return "베이스" if x == "BASE" else str(x)

def gini_coefficient(arr):
    x = np.asarray(arr, dtype=float)
    if x.size == 0 or np.all(x == 0): return 0.0
    x = np.sort(x); n = x.size; cumx = np.cumsum(x)
    return 1.0 + 1.0/n - 2.0*(cumx.sum()/(n*cumx[-1]))

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

# 레이블→id 집합/값 프레임
def ids_with_label(label, hist, prod):
    if label == "BASE": return set(prod["hash_id"])
    wk = pd.to_datetime(label).date()
    return set(hist.loc[hist["week_date"] == wk, "hash_id"])

def get_counts(label, hist, prod):
    if label == "BASE":
        return prod[["hash_id","review_base"]].rename(columns={"review_base":"value"}).copy()
    wk = pd.to_datetime(label).date()
    tmp = hist[hist["week_date"] == wk][["hash_id","review_count"]]
    return tmp.rename(columns={"review_count":"value"}).copy()

# A/B 공통 규칙(교집합→감소 제거→IQR 상한 제거)
def compute_filtered_ab(df_prod_cat, df_hist_cat, a_label, b_label):
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
    if pos.empty: return ab, pos, valid_ids

    q1, q3 = pos["delta_review"].quantile([0.25, 0.75])
    upper  = q3 + 1.5 * (q3 - q1)
    pos_iqr = pos[pos["delta_review"] <= upper].copy()
    return ab, pos_iqr, valid_ids

# 안전한 축/사이즈 스케일
def safe_domain(series, mode="auto", clip_q=0.95, is_log=False):
    s = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if s.empty:
        return [0, 1] if not is_log else [1, 10]
    if mode == "auto":
        hi = float(s.quantile(clip_q))
        if is_log:
            lo = max(float(s[s > 0].min()) * 0.9, 1.0)
            hi = max(hi, lo * 1.2)
            return [lo, hi]
        lo = 0.0
        hi = hi if hi > 0 else float(s.max() or 1.0)
        if hi == lo: hi = lo + (abs(lo) * 0.1 + 1.0)
        return [lo, hi]
    lo, hi = mode
    if is_log:
        lo = max(lo, 1.0)
        if hi <= lo: hi = lo * 10
    else:
        if hi <= lo: hi = lo + 1
    return [lo, hi]

def size_scale(series):
    s = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if s.empty: 
        return alt.Scale(range=[60, 300], type="sqrt", clamp=True)
    hi = float(s.quantile(0.95))
    if hi <= 0:
        return alt.Scale(range=[60, 300], type="sqrt", clamp=True)
    return alt.Scale(domain=[0, hi], range=[70, 900], type="sqrt", clamp=True)

# ───────────────── 데이터 로드/정리 ─────────────────
df_prod_all, df_hist_all = load_all()
if df_prod_all.empty or df_hist_all.empty:
    st.warning("데이터가 비어 있습니다. product_data / product_review_history_tmp 테이블을 확인하세요.")
    st.stop()

df_prod_all["category"] = df_prod_all["category"].apply(norm_cat).replace(CATEGORY_MAP)
df_prod_all = df_prod_all[df_prod_all["category"].isin(ALLOWED_CATEGORIES)].copy()

df_hist_all = (df_hist_all.groupby(["hash_id","week_date"], as_index=False)["review_count"].max())
df_hist_all = df_hist_all.merge(df_prod_all[["hash_id","category","brand"]], on="hash_id", how="inner")

all_weeks = sorted(df_hist_all["week_date"].unique())
latest_week = all_weeks[-1] if all_weeks else None
all_categories = [c for c in ALLOWED_CATEGORIES if c in df_prod_all["category"].unique().tolist()]

# ───────────────── 전역 옵션 ─────────────────
c1, c2 = st.columns([1,3])
with c1:
    if st.button("🔄 캐시 초기화", key="clear_cache"):
        st.cache_data.clear(); st.rerun()
with c2:
    st.caption("모든 지표는 ‘A/B 교집합 → 감소 제거 → IQR 상한’ 규칙으로 계산됩니다.")

# ───────────────── (A) 카테고리 점유율(증가 기준 파이) ─────────────────
st.markdown("### 🧭 카테고리 점유율 — 증가 리뷰수 기준 (A→B · 공통 규칙)")
s1, s2, _ = st.columns([1,1,2])
with s1:
    share_a = st.selectbox("A(기준)", ["BASE"] + [str(w) for w in all_weeks], index=0, key="cat_share_a")
with s2:
    default_idx = (["BASE"] + [str(w) for w in all_weeks]).index(str(latest_week)) if latest_week else 0
    share_b = st.selectbox("B(비교)", ["BASE"] + [str(w) for w in all_weeks], index=default_idx, key="cat_share_b")

rows = []
for cat in all_categories:
    prod_c = df_prod_all[df_prod_all["category"]==cat].copy()
    hist_c = df_hist_all[df_hist_all["category"]==cat].copy()
    _, pos_iqr, valid_ids = compute_filtered_ab(prod_c, hist_c, share_a, share_b)
    if not pos_iqr.empty and valid_ids:
        rows.append({"category": cat, "delta_sum": int(pos_iqr["delta_review"].sum())})
share_df = pd.DataFrame(rows).sort_values("delta_sum", ascending=False)

if share_df.empty:
    st.info("표시할 증가 데이터가 없습니다. (선택한 A/B 또는 데이터 상태를 확인하세요.)")
else:
    pie = alt.Chart(share_df).mark_arc(innerRadius=60).encode(
        theta=alt.Theta("delta_sum:Q", title="증가 합계"),
        color=alt.Color("category:N", title="카테고리"),
        tooltip=[alt.Tooltip("category:N", title="카테고리"),
                 alt.Tooltip("delta_sum:Q", title="증가 합계", format=",.0f"),
                 alt.Tooltip("percent:Q", title="비중", format=".1%")]
    ).transform_window(total="sum(delta_sum)").transform_calculate(
        percent="datum.delta_sum / datum.total"
    ).properties(height=320)
    st.altair_chart(pie, use_container_width=True)
st.markdown("---")

# ───────────────── 카테고리 탭 ─────────────────
cat_tabs = st.tabs([f"🧴 {c}" for c in all_categories])

for tab, cat in zip(cat_tabs, all_categories):
    with tab:
        st.markdown(f"### {cat}")
        df_cat_prod = df_prod_all[df_prod_all["category"]==cat].copy()
        df_cat_hist = df_hist_all[df_hist_all["category"]==cat].copy()
        if df_cat_prod.empty or df_cat_hist.empty:
            st.info("이 카테고리에 데이터가 없습니다.")
            continue

        t1, t2, t3, t4, t5 = st.tabs(["A vs B 비교", "베이스 vs 주차", "이 주의 핫제품", "브랜드 기여(버블)", "파레토 & 쏠림"])

        # ===== T1: A vs B 비교 =====
        with t1:
            cA, cB, _ = st.columns([1,1,2])
            with cA:
                a_label = st.selectbox("A(왼쪽)", ["BASE"] + [str(w) for w in all_weeks], index=0, key=f"a_{cat}_t1")
            with cB:
                default_idx = (["BASE"] + [str(w) for w in all_weeks]).index(str(latest_week)) if latest_week else 0
                b_label = st.selectbox("B(오른쪽)", ["BASE"] + [str(w) for w in all_weeks], index=default_idx, key=f"b_{cat}_t1")

            a_name, b_name = labelize(a_label), labelize(b_label)
            ab_all, pos_iqr, valid_ids = compute_filtered_ab(df_cat_prod, df_cat_hist, a_label, b_label)
            if valid_ids == set():
                st.info("두 구간 교집합 제품이 없습니다."); st.stop()

            a_total = int(pos_iqr["value_a"].sum()) if not pos_iqr.empty else 0
            b_total = int(pos_iqr["value_b"].sum()) if not pos_iqr.empty else 0

            left, right = st.columns([1,2.2], gap="large")
            with left:
                st.metric(f"총 리뷰(A={a_name})", f"{a_total:,}")
                st.metric(f"총 리뷰(B={b_name})", f"{b_total:,}", delta=f"{(b_total-a_total):+,}")
            with right:
                totals_df = pd.DataFrame({"label":[a_name,b_name], "sum":[a_total,b_total]})
                st.altair_chart(
                    alt.Chart(totals_df).mark_bar().encode(
                        x=alt.X("label:N", sort=[a_name,b_name], title=""),
                        y=alt.Y("sum:Q", title="합계"),
                        tooltip=[alt.Tooltip("label:N", title="구간"),
                                 alt.Tooltip("sum:Q", title="합계", format=",.0f")]
                    ).properties(height=280),
                    use_container_width=True
                )
            st.caption("※ A/B 교집합 → 감소 제거 → IQR 상한 적용 데이터만 합산")

        # ===== T2: 베이스 vs 주차 =====
        with t2:
            sel_weeks = st.multiselect("비교할 주차 선택(미선택 시 전체)", all_weeks,
                                       default=[latest_week] if latest_week else [],
                                       key=f"weeks_{cat}_t2")
            if not sel_weeks: sel_weeks = all_weeks

            rows = []; base_sum_total = 0
            for wk in sel_weeks:
                _, pos_iqr, valid_ids = compute_filtered_ab(df_cat_prod, df_cat_hist, "BASE", str(wk))
                if valid_ids:
                    base_sum_total += int(pos_iqr["value_a"].sum()) if not pos_iqr.empty else 0
                    rows.append({"label": str(wk), "value": int(pos_iqr["value_b"].sum()) if not pos_iqr.empty else 0})

            view = pd.DataFrame(rows)
            view = pd.concat([pd.DataFrame({"label":["베이스"], "value":[base_sum_total]}), view], ignore_index=True)
            view["label"] = view["label"].astype(str)

            st.altair_chart(
                alt.Chart(view).mark_bar().encode(
                    x=alt.X("label:N", title="", sort=list(view["label"])),
                    y=alt.Y("value:Q", title="합계"),
                    tooltip=[alt.Tooltip("label:N"), alt.Tooltip("value:Q", format=",.0f")]
                ).properties(height=280),
                use_container_width=True
            )
            st.caption("※ 각 주차도 A/B 교집합(= BASE∩주차) + 감소/이상치 제거 후 합계")

        # ===== 공통(B=최신) 집합(핫제품/브랜드/파레토) =====
        ab_common, pos_iqr_common, _ = compute_filtered_ab(
            df_cat_prod, df_cat_hist, "BASE", str(latest_week) if latest_week else "BASE"
        )

        # ===== T3: 핫제품 =====
        with t3:
            st.markdown("#### 🔥 이 주의 핫 제품 (BASE → 최신주차, 공통 규칙)")
            if pos_iqr_common.empty:
                st.info("핫 제품 후보가 없습니다.")
            else:
                for _, r in pos_iqr_common.sort_values("delta_review", ascending=False).head(4).iterrows():
                    cI, cT = st.columns([1,4])
                    with cI:
                        if isinstance(r["image_url"], str) and r["image_url"].startswith(("http://","https://")):
                            st.image(r["image_url"], use_column_width=True)
                    with cT:
                        st.markdown(f"**{r['brand']} · {r['product_name']}**")
                        st.markdown(f"- A(베이스): **{int(r['value_a']):,}**")
                        st.markdown(f"- B(최신): **{int(r['value_b']):,}**")
                        st.markdown(f"- 증가폭: **+{int(r['delta_review']):,}**")
                        if isinstance(r["product_url"], str) and r["product_url"].startswith(("http://","https://")):
                            st.markdown(f"[상품 페이지]({r['product_url']})")
                    st.divider()

        # ===== T4: 브랜드 기여(버블) — 스케일/지표 조정 + 안전화 =====
        with t4:
            st.markdown("#### 🧱 브랜드 포지셔닝 — 버블(스케일 자동 보정)")
            if pos_iqr_common.empty:
                st.info("계산할 데이터가 없습니다.")
            else:
                brand_pos = (pos_iqr_common.groupby("brand", as_index=False)
                             .agg(base_sum=("value_a","sum"),
                                  delta_sum=("delta_review","sum"),
                                  current_sum=("value_b","sum"),
                                  n_products=("hash_id","nunique")))
                # 현재 ≥ 베이스 & 모두 양수
                brand_pos = brand_pos[(brand_pos["current_sum"]>=brand_pos["base_sum"])&
                                      (brand_pos["base_sum"]>0)&(brand_pos["delta_sum"]>0)]
                if brand_pos.empty:
                    st.info("표시할 브랜드가 없습니다.")
                else:
                    brand_pos["growth_pct"]  = (brand_pos["delta_sum"]/brand_pos["base_sum"])*100.0
                    brand_pos["delta_per_k"] = brand_pos["delta_sum"]/(brand_pos["base_sum"]/1000.0)

                    topk = st.slider("표시 브랜드 수(Top-K)", 5, 50, 20, 1, key=f"brand_topk_{cat}")
                    plot_df = brand_pos.sort_values("delta_sum", ascending=False).head(topk).copy()

                    y_mode = st.radio("Y축 지표",
                        ["증가 합(B−A)", "현재 합(B)", "증가율(%)", "증가/1k베이스"],
                        horizontal=True, key=f"y_mode_{cat}")
                    scale_mode = st.radio("스케일",
                        ["자동(상위 95% 클립)", "로그", "수동"],
                        horizontal=True, key=f"scale_mode_{cat}")

                    if y_mode == "증가 합(B−A)":
                        y_field, y_title = "delta_sum", "이번 증가 리뷰수 합 (B−A)"
                        size_field, size_title = "current_sum", "현재 리뷰수 합(B)"
                        diag_chart = None
                    elif y_mode == "현재 합(B)":
                        y_field, y_title = "current_sum", "브랜드 현재 리뷰수 합 (B)"
                        size_field, size_title = "delta_sum", "증가 합 (B−A)"
                        x_min, x_max = float(plot_df["base_sum"].min()), float(plot_df["base_sum"].max())
                        diag_chart = alt.Chart(pd.DataFrame({"x":[x_min, x_max]})) \
                            .transform_calculate(y="datum.x") \
                            .mark_line(strokeDash=[4,4]).encode(x="x:Q", y="y:Q")
                    elif y_mode == "증가율(%)":
                        y_field, y_title = "growth_pct", "증가율 (%)"
                        size_field, size_title = "delta_sum", "증가 합 (B−A)"
                        diag_chart = None
                    else:
                        y_field, y_title = "delta_per_k", "증가(건) / 1,000 베이스"
                        size_field, size_title = "current_sum", "현재 리뷰수 합(B)"
                        diag_chart = None

                    is_log = (scale_mode == "로그")

                    if scale_mode == "자동(상위 95% 클립)":
                        x_dom = safe_domain(plot_df["base_sum"], mode="auto", is_log=is_log)
                        y_dom = safe_domain(plot_df[y_field],      mode="auto", is_log=is_log)
                        x_enc = alt.X("base_sum:Q", title="브랜드 베이스 리뷰수 합 (A)",
                                      scale=alt.Scale(domain=x_dom, type=("log" if is_log else "linear")),
                                      axis=alt.Axis(format="~s"))
                        y_enc = alt.Y(f"{y_field}:Q", title=y_title,
                                      scale=alt.Scale(domain=y_dom, type=("log" if is_log else "linear")),
                                      axis=alt.Axis(format="~s"))
                    elif scale_mode == "로그":
                        x_enc = alt.X("base_sum:Q", title="브랜드 베이스 리뷰수 합 (A)",
                                      scale=alt.Scale(type="log"), axis=alt.Axis(format="~s"))
                        y_enc = alt.Y(f"{y_field}:Q", title=y_title,
                                      scale=alt.Scale(type="log"), axis=alt.Axis(format="~s"))
                    else:
                        cx = int(plot_df["base_sum"].max()); cy = float(plot_df[y_field].max())
                        x_max_in = st.number_input("x 최대값(베이스 합 A)", min_value=1, value=max(1, cx), step=100, key=f"xmax_{cat}")
                        y_max_in = st.number_input("y 최대값", min_value=1.0, value=max(1.0, cy), step=100.0, key=f"ymax_{cat}")
                        x_enc = alt.X("base_sum:Q", title="브랜드 베이스 리뷰수 합 (A)",
                                      scale=alt.Scale(domain=[0, x_max_in]),
                                      axis=alt.Axis(format="~s"))
                        y_enc = alt.Y(f"{y_field}:Q", title=y_title,
                                      scale=alt.Scale(domain=[0, y_max_in]),
                                      axis=alt.Axis(format="~s"))

                    size_enc = alt.Size(f"{size_field}:Q", title=size_title, scale=size_scale(plot_df[size_field]))
                    bubble = alt.Chart(plot_df).mark_circle(opacity=0.85, clip=True).encode(
                        x=x_enc, y=y_enc, size=size_enc,
                        color=alt.Color("brand:N", legend=None),
                        tooltip=[
                            "brand",
                            alt.Tooltip("n_products:Q", title="통과 제품 수"),
                            alt.Tooltip("base_sum:Q",    title="베이스 합 A", format=",.0f"),
                            alt.Tooltip("current_sum:Q", title="현재 합 B",   format=",.0f"),
                            alt.Tooltip("delta_sum:Q",   title="증가 합 B−A", format=",.0f"),
                            alt.Tooltip("growth_pct:Q",  title="증가율 %",     format=".1f"),
                            alt.Tooltip("delta_per_k:Q", title="증가/1k베이스", format=".1f"),
                        ]
                    ).properties(height=360)
                    chart = bubble if diag_chart is None else (bubble + diag_chart)
                    st.altair_chart(chart, use_container_width=True)
                    st.caption("※ 스케일: ‘자동’은 상위 95%에서 클립해 롱테일을 눌러줍니다 · ‘로그’는 분포 편차가 큰 카테고리에 유용 · ‘수동’은 축 최대값 직접 지정")

        # ===== T5: 파레토 & 쏠림 =====
        with t5:
            st.markdown("#### 📈 파레토(상위 기여) & 🎯 Gini/Lorenz(쏠림) — 통과 제품 기준")
            if pos_iqr_common.empty:
                st.info("계산할 데이터가 없습니다.")
            else:
                pareto = pos_iqr_common[["product_name","delta_review"]].sort_values("delta_review", ascending=False).reset_index(drop=True)
                pareto["rank"] = np.arange(1, len(pareto)+1)
                total_delta = pareto["delta_review"].sum()
                pareto["cum_delta"] = pareto["delta_review"].cumsum()
                pareto["cum_pct"] = pareto["cum_delta"]/total_delta if total_delta>0 else 0

                bars = alt.Chart(pareto.head(50)).mark_bar().encode(
                    x=alt.X("rank:O", title="제품 순위(증가 기여 ↓)"),
                    y=alt.Y("delta_review:Q", title="증가 기여"),
                    tooltip=[alt.Tooltip("rank:Q", title="순위"),
                             "product_name:N",
                             alt.Tooltip("delta_review:Q", title="증가", format=",.0f"),
                             alt.Tooltip("cum_pct:Q", title="누적 비중", format=".1%")]
                )
                line = alt.Chart(pareto.head(50)).mark_line(point=True).encode(
                    x="rank:O", y=alt.Y("cum_pct:Q", title="누적 비중", axis=alt.Axis(format="%"))
                )
                st.altair_chart((bars + line).properties(height=300), use_container_width=True)

                deltas = pos_iqr_common["delta_review"].values
                gini = gini_coefficient(deltas)
                st.metric("Gini 계수(증가 집중도)", f"{gini:.3f}")

                x_sorted = np.sort(deltas); cum = np.cumsum(x_sorted)
                if len(cum)>0 and cum[-1]>0:
                    lorenz = np.insert(cum/cum[-1], 0, 0)
                    p = np.linspace(0,1,len(lorenz))
                    lor_df = pd.DataFrame({"누적 제품 비중":p, "누적 증가 비중":lorenz})
                    diag = alt.Chart(pd.DataFrame({"x":[0,1],"y":[0,1]})).mark_line(strokeDash=[4,4]).encode(x="x", y="y")
                    st.altair_chart(
                        alt.Chart(lor_df).mark_line().encode(
                            x=alt.X("누적 제품 비중:Q", axis=alt.Axis(format="%")),
                            y=alt.Y("누적 증가 비중:Q", axis=alt.Axis(format="%"))
                        ).properties(height=240) + diag,
                        use_container_width=True
                    )
