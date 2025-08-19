import json
from time import sleep

import mariadb
import sys
import requests  # requests 모듈 임포트

try:
    conn_tar = mariadb.connect(
        user="lguplus7",
        password="lg7p@ssw0rd~!",
        host="localhost",
        port=3310,
        database="cp_data"
    )
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

tar_cur = conn_tar.cursor()

tar_cur.execute("select seq_no, LON, LAT from tb_weather_tcn where addr1 = '0'")
stn_list = tar_cur.fetchall()

for stn in stn_list:
    seq_no = stn[0]
    LON = stn[1]
    LAT = stn[2]
    # URL과 저장 경로 변수를 지정합니다.
    req_url = f'https://dapi.kakao.com/v2/local/geo/coord2address?x={LON}&y={LAT}'
    print('req_url : ', req_url)
    headers = {'Authorization' : 'KakaoAK 8072fd936d24c09ff71f994e614b1443'}
    response = requests.get( req_url, headers=headers ) # 파일 URL에 GET 요청 보내기
    org_data = response.text
    print(org_data)
    if org_data.startswith('{"meta":{"total_count":0}'):
        print('org_data not ok')
        continue

    json_dic = json.loads(org_data)
    addr1 = json_dic['documents'][0]['address']['region_1depth_name']
    addr2 = json_dic['documents'][0]['address']['region_2depth_name']
    addr3 = json_dic['documents'][0]['address']['region_3depth_name']

    tar_cur.execute("update tb_weather_tcn set addr1=?, addr2=?, addr3=?, org_addr=? where seq_no=?", (addr1, addr2, addr3, org_data, seq_no) )
    conn_tar.commit()
    print('update tb_weather_tcn done')

