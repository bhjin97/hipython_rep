# %% [markdown]
# # 1. Import Library 

# %%
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
import re
import os
import pymysql
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

# %% [markdown]
# # 2. Driver set

# %%
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# %% [markdown]
# # 3. url set 

# %%
# Webull 페이지 로드
url = 'https://www.webull.com/quote/us/gainers/1m'
driver.get(url)
time.sleep(5)  # JS 로딩 대기

# %% [markdown]
# # 4. Get Data

# %% [markdown]
# ## copy selector

# %%
# name
#app > div.csr78 > div.csr137 > div.csr141.csr145.csr127 > div.table-body > div:nth-child(1) > div:nth-child(2) > div > div.detail.canClick > p.tit.bold

# last price
#app > div.csr78 > div.csr137 > div.csr141.csr145.csr127 > div.table-body > div:nth-child(1) > div:nth-child(5) > span

# change
#app > div.csr78 > div.csr137 > div.csr141.csr145.csr127 > div.table-body > div:nth-child(1) > div:nth-child(4) > div > span

# high & low
#app > div.csr78 > div.csr137 > div.csr141.csr145.csr127 > div.table-body > div:nth-child(1) > div:nth-child(6)
#app > div.csr78 > div.csr137 > div.csr141.csr145.csr127 > div.table-body > div:nth-child(1) > div:nth-child(7)

# Volume
#app > div.csr78 > div.csr137 > div.csr141.csr145.csr127 > div.table-body > div:nth-child(1) > div:nth-child(8) > div > span

# Market cap
#app > div.csr78 > div.csr137 > div.csr141.csr145.csr127 > div.table-body > div:nth-child(1) > div:nth-child(11) > div > span

# %% [markdown]
# ## data check

# %%
# page source
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# Company name
company_tags = soup.select("p.tit.bold")

for tag in company_tags:
    print(tag.text.strip())

driver.quit()


# %%
# Last Price
last_price = soup.select("#app .table-body div:nth-child(5) > span")

for p in last_price:
    print(p.text.strip())

driver.quit()

# %% [markdown]
# ## data preprocessing

# %%
# data preprocessing
def parse(text):
    if text.endswith("B"):
        return float(text[:-1]) * 1_000_000_000
    elif text.endswith("M"):
        return float(text[:-1]) * 1_000_000
    elif text.endswith("K"):
        return float(text[:-1]) * 1_000
    else:
        return float(text)

# %%
# 종목 단위 추출 (행 단위)
rows = soup.select("div.table-body > div.table-row")

for row in rows:
    try:
        name = row.select_one("p.tit.bold").text.strip()
        price = row.select_one("div:nth-child(5) > span").text.strip()
        change = parse(row.select_one("div:nth-child(4) > div > span").text.strip().replace("%", "").replace("+", ""))
        high = row.select_one("div:nth-child(6)").text.strip()
        low = row.select_one("div:nth-child(7)").text.strip()
        volume = parse(row.select_one("div:nth-child(8) > div > span").text.strip())
        market_cap = parse(row.select_one("div:nth-child(11) > div > span").text.strip())
        print(f"회사: {name}, 현재가: {price}, 변동률:{change}, 고가: {high}, 저가: {low}, 거래량: {volume}, 시가총액: {market_cap}")
    
    except AttributeError:
        continue  # 요소가 없는 경우는 건너뜀

# %% [markdown]
# # 5. Save data 

# %% [markdown]
# ## SQLite & CSV

# %%
import csv
# CSV 저장 준비
csv_filename = "webull_stocks.csv"
csv_fields = ["name", "price", "change", "high", "low", "volume", "market_cap"]

with open(csv_filename, "w", newline="", encoding="utf-8-sig") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
    writer.writeheader()

    # SQLite 저장 준비
    conn = sqlite3.connect("webull_stocks.db")
    cursor = conn.cursor()

    # 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            change REAL,
            high REAL,
            low REAL,
            volume REAL,
            market_cap REAL
        )
    """)

    # 데이터 추출
    rows = soup.select("div.table-body > div.table-row")

    for row in rows:
        try:
            name = row.select_one("p.tit.bold").text.strip()
            price = float(row.select_one("div:nth-child(5) > span").text.strip())
            change = parse(row.select_one("div:nth-child(4) > div > span").text.strip().replace("%", "").replace("+", ""))
            high = float(row.select_one("div:nth-child(6)").text.strip())
            low = float(row.select_one("div:nth-child(7)").text.strip())
            volume = parse(row.select_one("div:nth-child(8) > div > span").text.strip())
            market_cap = parse(row.select_one("div:nth-child(11) > div > span").text.strip())
            print(f"회사: {name}, 현재가: {price}, 변동률:{change}, 고가: {high}, 저가: {low}, 거래량: {volume}, 시가총액: {market_cap}")

            # CSV 저장
            writer.writerow({
                "name": name,
                "price": price,
                "change": change,
                "high": high,
                "low": low,
                "volume": volume,
                "market_cap": market_cap
            })

            # SQL 저장
            cursor.execute("""
                INSERT INTO stocks (name, price, change, high, low, volume, market_cap)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, price, change, high, low, volume, market_cap))

            print(f"저장 완료: {name}")

        except AttributeError:
            continue

    conn.commit()
    conn.close()

print(f"\nCSV 저장 완료: {csv_filename}")
print("SQLite DB 저장 완료: webull_stocks.db")


# %% [markdown]
# ## pymySQL

# %%
import pymysql


con = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',
    db='Webull_trade',
    charset='utf8mb4',
)
cursor = con.cursor()

create_db_query = "CREATE DATABASE IF NOT EXISTS Webull_trade CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
cursor.execute(create_db_query)


cursor.execute('''
CREATE TABLE IF NOT EXISTS stocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255),
    current_price FLOAT,
    change_percent FLOAT,
    high_price FLOAT,
    low_price FLOAT,
    trading_volume FLOAT,
    market_cap FLOAT
)
''')


insert_sql = """
    INSERT INTO stocks (
        company_name, current_price, change_percent,
        high_price, low_price, trading_volume, market_cap
    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
"""


for row in rows:
    try:
        company_name = row.select_one("p.tit.bold").text.strip()
        current_price = float(row.select_one("div:nth-child(5) > span").text.strip().replace(",", ""))
        change_percent = float(row.select_one("div:nth-child(4) > div > span").text.strip().replace("%", "").replace("+", ""))
        high_price = float(row.select_one("div:nth-child(6)").text.strip().replace(",", ""))
        low_price = float(row.select_one("div:nth-child(7)").text.strip().replace(",", ""))
        trading_volume = float(parse(row.select_one("div:nth-child(8) > div > span").text.strip()))
        market_cap = float(parse(row.select_one("div:nth-child(11) > div > span").text.strip()))

        cursor.execute(insert_sql, (
            company_name, current_price, change_percent,
            high_price, low_price, trading_volume, market_cap
        ))

        print(f"저장 완료: {company_name}")

    except AttributeError:
        continue
    except Exception as e:
        print(f"[에러 발생] {e}")
        continue

con.commit()
cursor.close()
con.close()
print("MySQL 저장 완료 ")


# %%



