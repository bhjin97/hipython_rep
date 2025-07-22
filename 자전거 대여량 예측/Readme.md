# 1. 프로젝트 개요 | 자전거 대여량 예측 🚲 
<img width="1536" height="1024" alt="bike_pred1" src="https://github.com/user-attachments/assets/7259f01d-c8b4-4970-8e4a-f9c58ed6e790" />

## 📌 프로젝트 명
**자전거 대여량 예측 모델 개발**


## 🎯 목표 (Objective)

시간, 날씨, 요일, 계절 등 다양한 환경 요인을 바탕으로  
**자전거 대여 수요를 정량적으로 예측하는 모델**을 개발한다.  
이 모델은 운영 효율성과 시민 만족도 향상에 기여하는 것을 목표로 한다.


## 🧭 배경 (Background)

- 자전거는 친환경적이며 유연한 도시 교통수단으로 주목받고 있음.
- 하지만 대여 수요는 **시간대, 날씨, 요일, 계절 등에 따라 크게 변화**함.
- 예측 없이 운영할 경우 아래와 같은 문제가 발생:
  - 수요 과잉 → 자전거 부족, 시민 불편
  - 수요 과소 → 자원 낭비, 비효율적 운영
- 따라서, **데이터 기반의 예측 시스템이 필수적**임.


## 💡 활용 목적 (Use Case)

- **출퇴근 시간** 집중 수요에 맞춘 자전거 탄력 운영
- **날씨 변화**에 따른 수요 감소 시 예비 자전거 수 조절
- **주말·공휴일 대비** 자전거 재배치 전략 수립
- **도시 교통 정책 수립** 시 수요 예측 데이터 기반 의사결정 지원


## 📝 요약 문장 (보고서 도입부용)

> 본 프로젝트는 시간, 기상, 캘린더 정보 등을 활용하여  
> **자전거 대여 수요를 예측하는 모델**을 구축하고,  
> 이를 통해 **운영 효율성 향상 및 시민 편의성 증진**을 목표로 한다.  
> 본 모델은 수요 급변 상황에 신속히 대응하며,  
> **자전거 재배치 및 서비스 최적화 전략** 수립에 기여할 수 있다.


---

# 2. 데이터의 이해 | Data Overview 📂 

## 📁 데이터 출처

- **출처**: [Kaggle - Bike Sharing Demand](https://www.kaggle.com/competitions/bike-sharing-demand/data)
- **파일 구성**
  - `train.csv`: 학습용 데이터 (datetime 및 count 포함)
  - `test.csv`: 예측 대상 데이터 (count 미포함)
  - `sampleSubmission.csv`: 제출 형식 예시


## 🔑 주요 컬럼 설명

| 변수명       | 설명                                              | 타입       | 예시              |
|--------------|---------------------------------------------------|------------|-------------------|
| `datetime`   | 날짜 및 시간 정보                                 | datetime   | 2011-01-01 00:00  |
| `season`     | 계절 (1:봄, 2:여름, 3:가을, 4:겨울)               | 범주형(int) | 1                 |
| `holiday`    | 공휴일 여부 (1: 공휴일, 0: 평일)                  | 범주형(int) | 0                 |
| `workingday` | 근무일 여부 (1: 근무일, 0: 주말/공휴일)           | 범주형(int) | 1                 |
| `weather`    | 날씨 상태 (1: 맑음, 4: 폭우 등으로 나쁨)          | 범주형(int) | 2                 |
| `temp`       | 실제 기온 (섭씨)                                  | 연속형(float) | 9.84              |
| `atemp`      | 체감 기온 (섭씨)                                  | 연속형(float) | 14.395            |
| `humidity`   | 상대 습도 (%)                                     | 연속형(int) | 81                |
| `windspeed`  | 풍속 (평균 m/s)                                   | 연속형(float) | 0.0               |
| `casual`     | 비회원 대여 수 (train에만 있음)                   | 정수형(int) | 3                 |
| `registered` | 회원 대여 수 (train에만 있음)                     | 정수형(int) | 13                |
| `count`      | 총 대여 수 (예측 타깃, train에만 있음)            | 정수형(int) | 16                |


## 🧮 간단한 통계 정보

- `count` 평균: 약 191
- 최대값: 977 / 최소값: 1
- `windspeed`: 이상치 또는 센서 오류 가능성
- `casual + registered = count` 관계 존재


## 🧠 분석 전 고려 사항

- `datetime`은 **다양한 시간 정보(hour, dayofweek 등)**로 파생 가능
- `registered`, `casual`은 **train에만 존재**하므로 test셋에는 사용 불가 → `count`만 예측 대상
- 일부 변수는 분포가 왜곡되어 있어 **로그 변환** 등의 전처리 고려 필요
- 'count'와 독립변수들 간의 상관관계를 파악

---

# 3. 피처 엔지니어링 | Feature Engineering 🧱

자전거 대여 수요는 단순한 변수 하나로 설명되기 어려운 **복합적인 환경적/시간적 요인**에 의해 결정되므로,  
모델링 전에 **의미 있는 파생 변수 생성과 데이터 정리가 필요**하다.


## 1️⃣ 시간 정보 파생 변수 생성

`datetime` 컬럼에서 다음과 같은 변수를 추출하였다:

| 파생 변수     | 설명                           | 데이터 타입 |
|--------------|--------------------------------|--------------|
| `year`       | 연도 (2011 또는 2012)         | 정수형       |
| `month`      | 월 (1~12)                      | 범주형       |
| `day`        | 일 (1~31)                      | 정수형       |
| `hour`       | 시각 (0~23)                    | 범주형       |
| `weekday`    | 요일 (0: 월요일 ~ 6: 일요일)   | 범주형       |


## 2️⃣ 로그 변환 (타깃 스케일 조정)

- `count` 값의 분포가 왜곡되어 있어 모델 학습 시 불안정
- `log1p(count)`를 사용하여 안정적인 학습 환경 조성

```python
df['log_count'] = np.log1p(df['count'])
```

---

# 4. 탐색적 데이터 분석 | Exploratory Data Analysis (EDA) 🔍 

EDA는 자전거 대여 수요(`count`)에 영향을 미칠 수 있는 다양한 요인을 시각화하고,  
변수 간 관계와 패턴을 이해하여 향후 모델링 전략의 방향을 설정하는 단계이다.



## 1️⃣ 타겟 변수 (`count`)의 분포

- `count`는 전반적으로 **오른쪽으로 치우친 분포(skewed)**를 가짐
- **로그 변환 (`log1p`)이 필요한 이유**:
  - 고대여량에 의한 왜곡 방지
  - 선형 회귀 모델의 가정 만족

> 📊 시각화: `sns.histplot(tr_df['count'], bins=50)`
> 📊 비교: `sns.histplot(np.log1p(tr_df['count']), bins=50)`



## 2️⃣ 시간대별 대여량 분석 (`hour`)

- `datetime`에서 추출한 `hour`별로 대여 수요가 극명하게 나뉨
- **출퇴근 시간(8시, 17~18시)에 수요 급증**
- `workingday`와 결합하면 더욱 뚜렷한 패턴 확인 가능

> 📊 `sns.boxplot(x='hour', y='count', data=tr_df)`
> 📊 `sns.boxplot(x='hour', y='count', hue='workingday', data=tr_df)`



## 3️⃣ 근무일(Working Day)에 따른 수요 패턴

아래 그래프는 **근무일 여부(`workingday`)에 따른 자전거 대여 수(`count`) 분포**를 보여준다.

### 🔍 해석

- **근무일(1)**과 **비근무일(0)** 모두에서 전체적인 대여량 중위수는 비슷함.
- 하지만 근무일에는 **이상치(outlier) 수준의 고대여량이 훨씬 많음**.
- 비근무일에는 중간 대여량은 높지만 **최대값 분포는 더 낮은 편**으로 보임.
- 이는 **근무일에는 특정 시간대(출퇴근 시간)에 수요가 집중되고**,  
  **비근무일에는 일정한 레저/여가 목적의 분산된 수요가 존재**함을 시사.


## 4️⃣ 계절 및 날씨 요인의 영향

- **계절(`season`)별**로 뚜렷한 대여량 차이 존재
- **날씨(`weather`)가 흐릴수록** 대여량 감소
- **온도(`temp`)와 체감온도(`atemp`)는 대체로 양의 상관관계**

> 📊 `sns.boxplot(x='season', y='count', data=tr_df)`
> 📊 `sns.boxplot(x='weather', y='count', data=tr_df)`
> 📈 `sns.scatterplot(x='temp', y='count', data=tr_df)`
> 📈 `sns.scatterplot(x='humidity', y='count', data=tr_df)`



## 5️⃣ 풍속(`windspeed`)의 이상치 확인

- 풍속이 **0인 데이터가 과도하게 많음**  
  → 측정 오류 or 결측 대체값으로 추정 가능
- IQR 기준으로도 이상치 존재

> 📊 `sns.boxplot(y='windspeed', data=tr_df)`
> 🧠 처리 전략은 전처리 파트에서 논의


## 6️⃣ 변수 간 상관 관계 분석

- `temp`, `atemp`, `count`는 **양의 상관관계**
- `humidity`와 `count`는 **약한 음의 상관관계**
- `registered`, `count`는 매우 강한 상관관계 (train 전용)

> 📊 `sns.heatmap(tr_df.corr(), annot=True, cmap='coolwarm')`


## 🧠 EDA 요약 인사이트

- 대여량은 **시간대, 날씨, 요일, 온도**에 크게 영향을 받는다.
- `datetime`에서 파생된 `hour`는 핵심 변수이다.
- 일부 변수는 로그 변환 및 범주형 변환이 필요하다.
- 풍속은 이상치 또는 데이터 오류 가능성이 있어 별도 처리 필요.

---

# 5. 모델링 전략 | Modeling 🎲

자전거 대여량(`count`) 예측은 **회귀(Regression)** 문제로 정의되며,  
비선형적이고 복합적인 수요 패턴을 잘 포착할 수 있는 모델 선택이 중요하다.  
이 프로젝트에서는 단순 회귀부터 트리 기반 모델까지 단계적으로 실험하며 성능을 비교하였다.



## 1️⃣ 문제 정의

- **문제 유형**: 회귀 (Regression)
- **예측 대상**: `count` (로그 변환된 `log_count`를 학습 대상으로 사용)
- **목표**: 시간, 날씨, 요일 등의 정보를 활용하여 `count`를 예측하고,  
  실제값과 예측값의 차이를 최소화하는 것



## 2️⃣ 입력 변수 (Features)

- 모델에 투입된 주요 피처:
  - 시간 관련: `hour`, `dayofweek`, `month`, `year`, `is_weekend`
  - 날씨 관련: `temp`, `atemp`, `humidity`, `windspeed`, `weather`, `season`
  - 캘린더 관련: `holiday`, `workingday`
  - 파생 변수: `hour × workingday`, `weekday × weather` 등

> 범주형 변수는 `get_dummies()`로 인코딩, `log_count`를 타깃으로 학습



## 3️⃣ 모델 후보 및 실험 전략

| 모델명                    | 특징                                         |
|--------------------------|----------------------------------------------|
| 선형 회귀 (Linear Regression)      | 빠르고 해석이 용이하나 비선형 관계 표현에 한계 |
| 랜덤 포레스트 (Random Forest)     | 비선형 관계에 강함, 이상치에 비교적 안정적     |
| XGBoost Regressor         | 예측 성능 우수, 과적합 제어 가능              |

- **데이터 분할**: Train / Validation (기본 8:2 split 사용)
- **하이퍼파라미터 튜닝**: GridSearchCV or RandomSearch (후속 실험에서 적용 가능)


## 4️⃣ 성능 평가 지표

| 지표명     | 설명                                              |
|------------|---------------------------------------------------|
| **R² Score**  | 전체 변동성 대비 모델 설명력 (1에 가까울수록 좋음)     |
| **RMSE** | 로그 변환된 값을 기반으로 계산된 평균 오차의 크기 |


## 🧠 요약

- 다양한 시간·날씨 변수 기반의 회귀 모델링을 통해 수요 패턴을 학습
- 선형 회귀는 기초 성능 비교용, 트리 기반 모델이 성능 측면에서 우수
- 향후 교차 검증, 모델 앙상블, 시계열 특화 모델로 확장 가능


# 6. 모델 학습 및 평가 📈

자전거 대여량(`count`)은 시간, 날씨, 요일 등 다양한 요인과 비선형적인 관계를 갖고 있어,  
여러 회귀 모델을 적용하여 성능을 비교하였습니다.


## 🔄 타깃 변수 전처리

- `count`의 분포가 치우쳐져 있어, **로그 변환**을 통해 모델의 예측 안정성을 확보했습니다.

```python
y_train = np.log1p(train_df['count'])
```


## 🧪 적용한 회귀 모델

| 모델 | 설명 |
|------|------|
| **Linear Regression** | 단순 선형 회귀 |
| **Polynomial Regression** | PolynomialFeatures + LinearRegression |
| **Ridge Regression** | L2 정규화 선형 회귀 |
| **Lasso Regression** | L1 정규화로 변수 선택 효과 |
| **Random Forest** | 비선형 결정 트리 앙상블 |
| **XGBoost** | Gradient Boosting 기반의 회귀 모델 |


## 📋 모델 평가 방식

- 예측값은 로그 복원을 적용: `np.expm1()` 사용
- 평가 지표:
  - **RMSE** (Root Mean Squared Error)
  - **R²** (결정계수)

```python
pred_log = model.predict(X_test)
pred = np.expm1(pred_log)           # 로그 복원
actual = np.expm1(y_test)

rmse = np.sqrt(mean_squared_error(actual, pred))
r2 = r2_score(actual, pred)
```



## 📊 성능 비교 

| 모델 | Degree | RMSE | R² |
|------|--------|------|----|
| Linear | 2 | 128.5 | 0.5 |
| **Polynomial + RandomForest** | 2 |45.805 |**0.951** |
| Polynomial + XGBoost | 2 | 45.37 | 0.938 |

> ✅ 트리 기반 모델(RandomForest, XGBoost)은 비선형성과 변수 간 상호작용을 잘 학습하며 성능이 뛰어났습니다.  



## 🧠 인사이트

- 다항 선형 회귀는 자전거 수요의 복잡한 패턴을 설명하기에 한계가 존재함
- 트리 기반 모델은 비선형성과 다중 조건을 반영해 예측 성능이 우수함
- 로그 변환은 분포 안정화, 이상치 완화에 크게 기여함


