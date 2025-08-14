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

# URL과 저장 경로 변수를 지정합니다.
req_url = 'https://apihub.kma.go.kr/api/typ01/url/stn_inf.php?inf=AWS&stn=&tm=202211300900&help=1&authKey=DwUlcUFpRG6FJXFBaTRuPw'

response = requests.get( req_url ) # 파일 URL에 GET 요청 보내기
org_data = response.text

split_data = org_data.strip().replace('Gangjin Gun','Gangjin-Gun').replace(' * ','').replace('     ',' ').replace('    ',' ').replace('   ',' ').replace('  ',' ').split('\n')
for line in split_data:
    if line.startswith('#'):
        continue

    print(line)
    line_arr = line.strip().split(' ')
    STN_ID = line_arr[0]
    LON = line_arr[1]
    LAT = line_arr[2]
    STN_SP = line_arr[3]
    HT = line_arr[4]
    HT_WD = line_arr[5]
    LAU_ID = line_arr[6]
    STN_AD = line_arr[7]
    STN_KO = line_arr[8]
    STN_EN = line_arr[9]
    FCT_ID = line_arr[10]
    LAW_ID = line_arr[11]
    BASIN = line_arr[12]

    tar_cur.execute(
        "insert into tb_weather_tcn( STN_ID, LON, LAT, STN_SP, HT, HT_WD, LAU_ID, STN_AD, STN_KO, STN_EN, FCT_ID, LAW_ID, BASIN, create_dt ) values (?,?,?,?,?,?,?,?,?,?,?,?,?,now())",
        (STN_ID, LON, LAT, STN_SP, HT, HT_WD, LAU_ID, STN_AD, STN_KO, STN_EN, FCT_ID, LAW_ID, BASIN ))
    conn_tar.commit()
    print('insert into tb_weather_tcn done')
