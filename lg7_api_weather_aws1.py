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
req_url = 'https://apihub.kma.go.kr/api/typ01/cgi-bin/url/nph-aws2_min?stn=0&disp=0&help=1&authKey=OfKWVp0fSi6ylladH_ou4w'

while True:
    response = requests.get( req_url ) # 파일 URL에 GET 요청 보내기
    org_data = response.text

    split_data = org_data.strip().replace('    ',' ').replace('   ',' ').replace('  ',' ').split('\n')
    for line in split_data:
        if line.startswith('#'):
            continue

        print(line)
        line_arr = line.strip().split(' ')
        yyyymmddhhmi = line_arr[0]
        stn = line_arr[1]
        wd1 = line_arr[2]
        ws1 = line_arr[3]
        wds = line_arr[4]
        wss = line_arr[5]
        wd10 = line_arr[6]
        ws10 = line_arr[7]
        ta = line_arr[8]
        re = line_arr[9]
        rn_15m = line_arr[10]
        rn_60m = line_arr[11]
        rn_12h = line_arr[12]
        rn_day = line_arr[13]
        hm = line_arr[14]
        pa = line_arr[15]
        ps = line_arr[16]
        td = line_arr[17]

        tar_cur.execute("select seq_no from tb_weather_aws1 where yyyymmddhhmi = ? and stn = ?", (yyyymmddhhmi, stn))
        exist_list = tar_cur.fetchall()
        if exist_list is not None and exist_list.__len__() > 0:
            print(f'[debug] duplicated : yyyymmddhhmi={yyyymmddhhmi}, stn={stn}')
        else:
            tar_cur.execute(
                "insert into tb_weather_aws1( yyyymmddhhmi, stn, wd1, ws1, wds, wss, wd10, ws10, ta, re, rn_15m, rn_60m, rn_12h, rn_day, hm, pa, ps, td, org_data, update_dt ) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,now())",
                (yyyymmddhhmi, stn, wd1, ws1, wds, wss, wd10, ws10, ta, re, rn_15m, rn_60m, rn_12h, rn_day, hm, pa, ps, td, org_data ))
            conn_tar.commit()
            print('insert into tb_weather_aws1 done')

    sleep(60)
