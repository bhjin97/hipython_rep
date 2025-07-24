# 🚗 중고차 가격 예측 프로젝트

<img src="https://github.com/bhjin97/hipython_rep/blob/main/%EC%A4%91%EA%B3%A0%EC%B0%A8%20%EA%B0%80%EA%B2%A9%EC%98%88%EC%B8%A1/data/%EC%A4%91%EA%B3%A0%EC%B0%A8%EA%B0%80%EA%B2%A9%EC%98%88%EC%B8%A1.png">

이 프로젝트는 다양한 차량 정보를 기반으로 중고차의 가격을 예측하기 위해 머신러닝 모델을 적용한 분석 사례입니다. 데이터 전처리, 파생 변수 생성, 이상치 처리, 모델링, 평가 등의 전 과정을 포함합니다.

---

## 1. 📦 데이터 개요

- 총 샘플 수: 약 9,970개
- 주요 컬럼: 차량 정보, 상태, 주행거리, 등록일, 마력, 실린더 수 등
- 타겟 변수: `price_in_aed` → 로그 변환한 `price_log` 사용

---

## 2. 🧹 데이터 전처리

### ✅ 결측치 처리

- `horsepower`: 문자열 → 숫자 변환 (`400-500 HP` → 평균값), 'unknown'은 제거 또는 그룹 평균으로 대체
- 'title' : 이미 컬럼에 중복되는 정보 많다고 판단하여 제거
- `no_of_cylinders`: 문자열 → 숫자 변환 → 그룹화 (`3, 4, 5기통 → 4`, `10기통 → 12` 등)
- `year`, `motors_trim` 등은 그룹 평균 또는 삭제 여부 검토 후 처리

### ✅ 이상치 탐지 및 처리

- 로그 변환: `price`, `kilometers`
- 시각화 기반 파악:
  - `body_condition == 3`, `mechanical_condition == 3` 값은 고급 차량에서만 존재 → 편향 유발 가능
  - 특정 월 (`4월`, `5월`, `12월`)에 이상치 집중 → 파생 변수 `is_high_outlier_month` 생성

---

## 3. 🧠 Feature Engineering

### 🔧 파생 변수 생성

- `price_log`: 로그 변환 가격
- `kilometers_log`: 로그 변환 주행 거리
- `km_bin`: 주행거리 구간화 (분포 왜곡 완화)
- `region_price_mean`: 지역별 평균 가격
- `company_model_avg_price`: 브랜드-모델 평균 가격
- `body_type_median_price`: 바디타입별 가격 중앙값
- `mechanical_condition_median_price`: 상태별 가격 중앙값
- `is_recent_year`, `is_high_outlier_month` 등 이진 파생 변수

---

## 4. ✂️ Feature Selection

### 🗃️ 제거된 변수

- 타겟 누설 우려: `price_log_dev`, `year_price_dev`
- 중복 또는 예측에 불필요한 정보: `company`, `model`, `motors_trim`, `date_posted` 등
- 평균 가격으로 이미 반영된 변수 제거


### 🧾 최종 학습용 컬럼 설명


| 컬럼명                      | 설명 |
|----------------------------|------|
| `kilometers`               | 주행거리 (원본 값) |
| `body_condition`           | 차량 외관 상태 |
| `mechanical_condition`     | 차량 기계 상태 |
| `seller_type`              | 판매자 유형 |
| `body_type`                | 차량 바디타입 |
| `transmission_type`        | 변속기 유형 |
| `fuel_type`                | 연료 종류 |
| `steering_side`            | 운전석 위치 |
| `color`                    | 차량 색상 |
| `cyl_grouped`              | 통합된 실린더 수 |
| `hp_group`                 | 통합된 마력 그룹 |
| `is_high_outlier_month`    | 이상치 집중 월 여부 (4, 5, 12월) |
| `is_recent_year`           | 최근 연식 차량 여부 |
| `year_price_dev`           | 차량 연식별 평균 가격과의 차이 |



---

## 5. 🧪 모델링 및 평가

### 🔍 사용한 모델

- `RandomForestRegressor`
- `XGBoostRegressor`

### 📊 성능

| 모델           | RMSE   | R²      |
|----------------|--------|---------|
| Random Forest  | 0.3338 | 0.9154  |
| XGBoost        | 0.3030 | 0.9303  |

### 📊 5-Fold 교차검증 결과 비교 (R² 기준)

| Fold | Random Forest | XGBoost |
|------|----------------|---------|
| 1    | 0.9062         | 0.9219  |
| 2    | 0.9041         | 0.9243  |
| 3    | 0.9121         | 0.9283  |
| 4    | 0.9062         | 0.9209  |
| 5    | 0.9208         | 0.9340  |
| **평균** | **0.9099**     | **0.9259** |

> ✅ **XGBoost가 모든 Fold에서 일관되게 더 높은 R² 점수**를 기록했으며, 평균 성능도 우수함.
> ✅ Random Forest도 전체적으로 안정적인 예측력을 보여주며, 비교적 빠르고 해석 가능한 모델로 활용 가치가 있음.


- 교차검증 (5-Fold) 결과 일관된 성능 확인
- 오버피팅 방지를 위한 라벨링, 로그 변환, 파생 변수 중심 구성

---

## 6. 📈 시각화 요약

- Boxplot: 범주형 변수와 가격 간 관계 파악
- 이상치 시각화: 시계열/색상/상태별 이상치 탐지
- 분포 확인: 브랜드, 지역, 바디타입별 수치 확인

---

## 7. 📝 향후 개선 방향

- 모델 튜닝 및 앙상블 보강
- SHAP 등으로 변수 중요도 해석
- 다양한 스케일링 기법 적용 실험 (RobustScaler, QuantileTransformer 등)

---

## 🔗 사용 라이브러리

`pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `xgboost`

---
