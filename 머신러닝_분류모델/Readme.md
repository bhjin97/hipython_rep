# 고객 성별 분류 모델 (Customer Gender Classification Model)

## 1. 프로젝트 개요
이 프로젝트는 고객 데이터를 기반으로 고객의 성별을 분류하는 머신러닝 모델을 개발하고 평가합니다.  
고객 성별 예측은 마케팅 전략 수립, 개인화된 서비스 제공, 고객 세분화 등 다양한 비즈니스 의사 결정에 활용될 수 있습니다.

---

## 2. 사용된 기술 및 라이브러리

- **언어**: Python  
- **데이터 처리**: `pandas`  
- **데이터 분할**: `scikit-learn` `train_test_split`  
- **데이터 전처리**: `LabelEncoder`, `OneHotEncoder`, `StandardScaler`, `ColumnTransformer`  
- **머신러닝 모델**:
  - `DecisionTreeClassifier`
  - `LogisticRegression`
  - `RandomForestClassifier` (`scikit-learn`)
  - `XGBClassifier` (`xgboost`)  
- **모델 평가**: `classification_report`, `accuracy_score`, `confusion_matrix`  
- **하이퍼파라미터 튜닝**: `GridSearchCV`  

---

## 3. 데이터셋 설명

### 🔹 X.csv (독립 변수)
- 고객의 다양한 특성(피처) 포함
- `cust_id` 컬럼은 제거됨
- 수치형 + 범주형 특성 혼합

### 🔹 y.csv (종속 변수)
- 고객 ID 및 `gender` (성별: 'Male', 'Female') 포함
- `LabelEncoder`를 통해 숫자로 변환

> ⚠️ 참고: `creditcard.csv`와 같은 대용량 파일은 `.gitignore`에 포함되어 Git 저장소에 업로드되지 않습니다.

---
## 4. 모델 학습 및 평가 프로세스
데이터 로드

### X.csv, y.csv 로드 또는 예제 데이터 생성

### 전처리

### cust_id 컬럼 제거

### gender → 숫자로 인코딩 (LabelEncoder)

### 범주형: OneHotEncoder

### 데이터 분할

---

## 5. 모델 학습 및 평가

### DecisionTreeClassifier, LogisticRegression, RandomForestClassifier: 학습 및 평가

### XGBClassifier: GridSearchCV를 통해 하이퍼파라미터 튜닝 후 최적 모델로 평가

### 결과 출력

### classification_report, accuracy_score, confusion_matrix 출력

---

## 6. 데이터 
---

## 6. .gitignore 관리
.gitignore는 프로젝트 루트 디렉토리에 위치

예외 처리 예시:

bash
복사
편집
data1/creditcard.csv

