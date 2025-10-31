import mariadb

# ===== 설정 =====
TABLE = "tb_weather_tcn"

SRC = dict(host="192.168.14.38", port=3310, user="lguplus7", password="lg7p@ssw0rd~!", database="cp_data")
DST = dict(host="127.0.0.1",    port=3310, user="lguplus7",  password="lg7p@ssw0rd~!", database="cp_data")

BATCH = 2000
# =================

def connect(cfg):
    conn = mariadb.connect(**cfg, autocommit=False)
    cur = conn.cursor()
    cur.execute("SET NAMES utf8mb4")
    cur.execute("SET CHARACTER SET utf8mb4")
    cur.execute("SET character_set_connection = utf8mb4")
    return conn

src = connect(SRC); dst = connect(DST)
s = src.cursor();   d = dst.cursor()

# 스키마가 완전히 같다는 전제: SELECT * 결과를 그대로 REPLACE INTO
s.execute(f"SELECT * FROM {TABLE}")
cols = len(s.description)                       # 컬럼 개수
place = ",".join(["?"] * cols)                  # (?, ?, ...)

sql = f"REPLACE INTO {TABLE} VALUES ({place})"  # PK/UNIQUE 충돌 시 덮어쓰기
buf, moved = [], 0

for row in s:
    buf.append(row)
    if len(buf) >= BATCH:
        d.executemany(sql, buf); dst.commit()
        moved += len(buf); buf.clear()
        print("moved:", moved)

if buf:
    d.executemany(sql, buf); dst.commit()
    moved += len(buf)

print("done, total:", moved)
src.close(); dst.close()
