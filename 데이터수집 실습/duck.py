import duckdb
import os
import pandas as pd

# duckdb로 csv파일을 읽으면 에러가 발생하므로 pandas에서 먼저 읽어서 duckdb에 import,
duck_con = duckdb.connect("c:/data/duck_smb.db")
duck_con.execute("CREATE TABLE IF NOT EXISTS tb_smb_file AS SELECT * FROM read_csv('c:/data/smb_data/sejong.csv');")
duck_con.execute("DELETE FROM tb_smb_file;")

csv_path = 'c:/data/smb_data'
file_list = os.listdir( csv_path ) # 경로 내에 파일을 모두 불러옴
csv_file_list = [file for file in file_list if file.endswith('.csv')] # csv 확장자를 가진 파일로 새로운 리스트 생성

for csv_file_name in csv_file_list:
    csv_file_full = f'{csv_path}/{csv_file_name}'
    print(f'csv_file_name = {csv_file_full}')
    csv_df = pd.read_csv( csv_file_full )
    duck_con.execute("insert into tb_smb_file SELECT * FROM csv_df;")

print("csv loading complete")

duck_con.sql("SELECT addr1, addr2, addr3, cate3_nm, cnt FROM ( SELECT addr1, addr2, addr3, cate3_nm, cnt, RANK() OVER (PARTITION BY addr3 ORDER BY cnt DESC) AS t_rank FROM ( SELECT 시도명 as addr1, 시군구명 as addr2, 행정동명 as addr3, 상권업종소분류명 as cate3_nm, COUNT(상권업종소분류명) AS cnt FROM tb_smb_file GROUP BY addr1, addr2, addr3, cate3_nm ORDER BY cnt DESC ) temp_rank ) temp_rank2 WHERE t_rank=1 ORDER BY cnt DESC;").show()