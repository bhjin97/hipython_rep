import duckdb

duck_con = duckdb.connect("c:/data/duck_smb.db")

duck_con.execute("insert into tb_smb_file SELECT * FROM read_csv('c:/data/smb_data/*.csv');")
duck_con.sql("SELECT addr1, addr2, addr3, cate3_nm, cnt FROM ( SELECT addr1, addr2, addr3, cate3_nm, cnt, RANK() OVER (PARTITION BY addr3 ORDER BY cnt DESC) AS t_rank FROM ( SELECT 시도명 as addr1, 시군구명 as addr2, 행정동명 as addr3, 상권업종소분류명 as cate3_nm, COUNT(상권업종소분류명) AS cnt FROM tb_smb_file GROUP BY addr1, addr2, addr3, cate3_nm ORDER BY cnt DESC ) temp_rank ) temp_rank2 WHERE t_rank=1 ORDER BY cnt DESC;").show()