# 🎲 고객 성별 분류 모델 (Customer Gender Classification Model)

---

## 📌 1. 프로젝트 개요

고객 데이터를 기반으로 **성별을 분류**하는 머신러닝 모델을 개발하고 평가합니다.  
이 모델은 다음과 같은 비즈니스 전략에 활용될 수 있습니다:

- 맞춤형 마케팅 전략 수립  
- 개인화된 서비스 제공  
- 고객 세분화 및 타겟팅 강화  

---

## 🛠️ 2. 사용된 기술 및 라이브러리

| 범주 | 내용 |
|------|------|
| **언어** | Python |
| **데이터 처리** | `pandas` |
| **데이터 분할** | `train_test_split` from `scikit-learn` |
| **데이터 전처리** | `LabelEncoder`, `OneHotEncoder`, `StandardScaler`, `ColumnTransformer` |
| **모델** | `DecisionTreeClassifier`, `LogisticRegression`, `RandomForestClassifier` (`scikit-learn`)<br>`XGBClassifier` (`xgboost`) |
| **모델 평가** | `classification_report`, `accuracy_score`, `confusion_matrix` |
| **튜닝 도구** | `GridSearchCV` |

---

## 📂 3. 데이터셋 설명

### 🔸 `X.csv` (독립 변수)
- 고객 특성(feature) 포함
- `cust_id`는 제거됨
- **수치형 + 범주형** 혼합 데이터 구성

### 🔸 `y.csv` (종속 변수)
- 고객 ID 컬럼 제거 후 타겟

  ⚠️ 데이터 출처: 한국데이터산업진흥원 빅데이터분석기사 실기 공개 예시 문항

---

## 🧪 4. 모델 학습 및 평가 프로세스

### 📌 Step 1. 데이터 로드
- `X.csv`, `y.csv` 로드  
- 파일이 없을 경우 **예제 데이터 자동 생성**

### 📌 Step 2. 데이터 전처리
- `cust_id` 컬럼 제거
- '환불금액'의 결측치 처리 -> 0으로 대체
- `gender` → 숫자로 인코딩 (`LabelEncoder`)
- **ColumnTransformer 사용**  
  - 수치형 → `StandardScaler`  
  - 범주형 → `OneHotEncoder`

### 📌 Step 3. 데이터 분할
- `train_test_split(test_size=0.2, stratify=y)`  
- **Train:Test = 8:2**, 클래스 비율 유지

---

## 🤖 5. 모델 학습 및 평가

### ✔️ 사용 모델
- `DecisionTreeClassifier`
- `LogisticRegression`
- `RandomForestClassifier` → `GridSearchCV`로 **하이퍼파라미터 튜닝**
- `XGBClassifier` → `GridSearchCV`로 **하이퍼파라미터 튜닝**

### 🧾 결과 평가
- `classification_report`
- `accuracy_score`
- `confusion_matrix`

- RandomForestClassifier 모델 최적화: GridSearchCV를 사용하여 RandomForestClassifier 모델의 최적 파라미터를 탐색했습니다.

**최적 파라미터: {'max_depth': 11, 'min_samples_split': 20}   
최고 성능 (정확도): 0.6614**

모든 결과는 **콘솔 출력**을 통해 확인 가능



