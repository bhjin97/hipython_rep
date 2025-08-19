from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import mariadb
import sys

try:
    conn = mariadb.connect(
        user="lguplus7",
        password="lg7p@ssw0rd~!",
        host="localhost",
        port=3310,
        database="cp_data"
    )
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)
cur = conn.cursor()

scrap_url_list = []
scrap_url_list.append(['https://news.hada.io/?page=',-1]) # 최신 뉴스 전체

# source_type - 0:네이버뉴스
source_type = '0'

# 중복확인 여부, Y:중복되면 break
duplicate_yn = 'Y'
duplicate_max = 30

# Playwright 실행
with sync_playwright() as p:

    current_list_pos = 0
    current_page = 1

#    browser = p.chromium.launch(headless=True)
    browser = p.firefox.launch(headless=True)
    main_page = browser.new_page()

    while True:
        try:
            time.sleep(5)
            main_page.goto(f'{scrap_url_list[current_list_pos][0]}{current_page}')
        except TimeoutError as te:
            print(f"Error browser: {te}")
            browser.close()
            browser = p.firefox.launch(headless=True)
            main_page = browser.new_page()
            time.sleep(60)
            main_page.goto(f'{scrap_url_list[current_list_pos][0]}{current_page}')

        time.sleep(5)

        print( '[debug] list page : ', main_page.url) # 목록 URL 출력

        content = main_page.content()
        soup = BeautifulSoup(content, "html.parser")
        temp_soup = soup.select_one('article > div')

        news_list = temp_soup.find_all('div', {'class': 'topic_row'})
        if news_list.__len__() == 0:
            print('[debug] no news found...')
            continue # 사실상 retry --> chromium 말고 firefox가 잘됨

        duplicate_cnt=0
        for news in news_list:

            source_url = f'https://news.hada.io/{news.select('div.topicdesc > a')[0].get('href')}'
            print( 'source_url : ', source_url)

            comment_cnt = news.select_one('div.topicinfo > a.u')
            if comment_cnt.text.strip().startswith('댓글 ') > 0:
                comment_cnt = comment_cnt.text.replace('댓글 ','').replace('개', '')
            else:
                comment_cnt = '0'

            cur.execute('select comment_cnt from gn_scrap_ready where source_type = ? and source_url = ? and status = "0"', (source_type, source_url))
            res = cur.fetchall()
            if res.__len__() > 0:
                if res[0] == comment_cnt:
                    print('[debug] DB에 source_url 존재 --> Skip')
                    duplicate_cnt = duplicate_cnt + 1
                    # 한 목록에서 중복 20개 이상인 경우 수집 중단
                    if duplicate_yn == 'Y' and duplicate_cnt >= duplicate_max:
                        print('[debug] duplicate_cnt >= 30 --> break')
                        current_page = scrap_url_list[current_list_pos][1]
                        break # 중복 20개 이상이면 for를 벗어나 다음 섹션으로 이동
                    continue

            insert_sql = "insert into gn_scrap_ready(source_type, source_url, comment_cnt, create_dt) values (?,?,?, now())"
            cur.execute( insert_sql, (source_type, source_url, comment_cnt ) )
            conn.commit()

        if current_page == scrap_url_list[current_list_pos][1]:
            if current_list_pos == (len(scrap_url_list)-1):
                current_list_pos = 0
            else:
                current_list_pos = current_list_pos + 1
            current_page = 1
            print('[debug] next section : ', current_list_pos )
        else:
            # 다음 페이지로 이동
            current_page = current_page + 1
            print('[debug] next page : ', current_page )
            time.sleep(5)

    # 브라우저 종료
    browser.close()
