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

## ⚙️ 실행 방법

### 1. MySQL에 데이터베이스 생성

```sql
CREATE DATABASE Webull_trade CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

### 2. Python 패키지 설치

```bash
pip install requests beautifulsoup4 pymysql
```

### 3. Python 스크립트 실행

```bash
python webull_crawler.py
```

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
