# 📈 Webull 실시간 주식 데이터 수집 및 저장 시스템

이 프로젝트는 Webull 사이트에서 실시간 주식 데이터를 크롤링하여  
MySQL 데이터베이스에 저장하는 Python 기반 자동화 스크립트입니다.

---

## 🔧 사용 기술

- **언어**: Python 3.10.18 
- **라이브러리**:
  - `requests`, `BeautifulSoup` (크롤링)
  - `pymysql` (MySQL 연동)
  - `re` (텍스트 전처리)

- **데이터베이스**:
  - MySQL (로컬 환경)

---

## 📊 수집 데이터 항목

| 컬럼명         | 설명           |
|----------------|----------------|
| `company_name` | 회사 이름      |
| `current_price`| 현재가         |
| `change_percent` | 변동률 (%)    |
| `high_price`   | 고가           |
| `low_price`    | 저가           |
| `trading_volume` | 거래량       |
| `market_cap`   | 시가총액       |

※ 거래량과 시가총액은 M(백만), B(십억) 단위 문자 제거 후 숫자로 변환되어 저장됩니다.

---

## ✅ 실행 방법 (How to Run)

### 1. 필요한 라이브러리 설치

다음 명령어로 필요한 패키지를 설치하세요:

```bash
pip install requests beautifulsoup4 pillow selenium webdriver-manager pymysql
```

---

### 2. MySQL 데이터베이스 준비

1. MySQL이 설치되어 있어야 합니다.
2. 아래 쿼리로 `Webull_trade`라는 데이터베이스를 생성하세요. (스크립트가 자동 생성하므로 생략 가능)

```sql
CREATE DATABASE Webull_trade CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

---

### 3. Python 스크립트 실행

```bash
python webull_crawler.py
```

> 이 스크립트는 다음 작업을 자동으로 수행합니다:
>
> - Webull 사이트 접속 및 데이터 크롤링 (Selenium 사용)
> - 회사명, 현재가, 변동률, 고가, 저가, 거래량, 시가총액 추출
> - 단위(M/B/K) 변환 및 전처리
> - SQLite DB와 CSV 파일 저장
> - MySQL (`Webull_trade`) DB에 테이블 생성 및 데이터 저장

---

### 4. 결과 확인

- **CSV** 파일: `webull_stocks.csv`  
- **SQLite** 파일: `webull_stocks.db`  
- **MySQL** 테이블: `stocks` (Webull_trade 데이터베이스 내부)

---

### 5. 출력 예시

```
회사: NVIDIA Corporation, 현재가: 130.23, 변동률:15.73, 고가: 135.00, 저가: 128.00, 거래량: 237000000.0, 시가총액: 3.26e+12
저장 완료: NVIDIA Corporation
...
MySQL 저장 완료 
```

---

### 6. 참고 사항

- Selenium이 크롬 드라이버를 자동으로 설치하므로 별도 설정 불필요
- Webull의 페이지 구조가 변경되면 `select()` 경로 수정을 고려해야 함
- `headless` 옵션으로 브라우저를 띄우지 않고 실행 가능
- MySQL 연동 시 사용자 계정 정보와 포트를 상황에 맞게 수정하세요

---

---

## 🛠 주요 기능

- BeautifulSoup으로 Webull 주식 테이블 파싱
- `%`, `+`, `M`, `B` 등의 기호 전처리
- MySQL DB 및 테이블 자동 생성
- 삽입 후 `con.commit()`으로 저장 확정

---

## 📁 예시 출력

```
저장 완료: Abivax S.A.
저장 완료: NVIDIA Corporation
...
MySQL 저장 완료 ✅
```

---

## 📌 참고 사항

- 웹사이트 구조가 바뀌면 크롤링 로직이 작동하지 않을 수 있습니다.
- 현재는 단일 실행 데이터 수집만 포함되어 있으며, 스케줄링은 포함되어 있지 않습니다.

---

## 🧠 향후 확장 아이디어

- 📄 CSV 동시 저장
- ⏰ 주기적 수집을 위한 `schedule` 또는 `cron` 연동
- 📅 날짜별 저장 기능
- 📊 시각화 대시보드 (예: Streamlit)

---

## 🧾 라이선스

MIT License
