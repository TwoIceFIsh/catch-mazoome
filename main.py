import json
import platform
from os import listdir

import pyautogui
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading

def load_config(config_path='config.json'):
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config

def catch_articles(webdriver: webdriver.Chrome):
    """
    기사를 크롤링하는 함수
    """
    with open('cookies.json', 'r') as f:
        cookies = f.readline()

    # 크롤링 작업 수행
    response = requests.get("https://apis.naver.com/cafe-web/cafe2/ArticleListV2dot1.json?search.clubid=28497937&search.queryType=lastArticle&search.page=1&search.perPage=20",
                            headers={
                                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/121.0.0.0 Mobile Safari/537.36",
                                "Referer": "https://m.naver.com/"
                            })
    data = response.json()
    articles = data['message']['result']['articleList']
    images = listdir('./img')

    for article in articles:

        # 이미 캡쳐한 게시글은 건너뜀
        if f"{article['articleId']}.png" in images:
            articles.remove(article)
            continue


        payload = f'[스팸알림] {article["menuName"]} - {article["subject"]} - {article["writerNickname"]} \n https://cafe.naver.com/likeusstock/{article["articleId"]} \n 가입인사/댓글1/댓글비활성 \n\n 증적화면 : https://catch.mezoo.me/img/{article["articleId"]}.png'
        if article['menuName'] == "가입인사" and article['enableComment'] == False and article['commentCount'] == 1:
            print(payload)
            webdriver.get(f"https://cafe.naver.com/likeusstock/{article['articleId']}")
            time.sleep(2)
            webdriver.save_screenshot(f"./img/{article['articleId']}.png")
            requests.post("https://m.cafe.naver.com/MemoPost.nhn",
                          headers={
                              "Referer": "https://m.cafe.naver.com/MemoList.nhn?search.clubid=28497937&search.menuid=2",
                              "Cookie":cookies}
                          , data={
                    "memoPost.cafeId": "28497937",
                    "memoPost.menuId": "2",
                    "memoPost.content": payload,
                })
def setup_driver_options():
    chrome_options = Options()
    if platform.system() != 'Windows':
        chrome_options.add_argument("--headless")  # UI 없이 실행
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('window-size=1920,1080')
    chrome_options.add_argument("--disable-dev-shm-usage")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    chrome_options.add_argument('user-agent=' + user_agent)
    chrome_options.add_argument('referer=https://www.naver.com/')
    return chrome_options

def init_driver():
    chrome_options = setup_driver_options()
    chromedriver_path = "./src/chromedriver.exe"
    if platform.system() != 'Windows':
        chromedriver_path = "/usr/src/chrome/chromedriver-linux64/chromedriver"
    webdriver_service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    return driver

def login_and_get_cookies(url, username, password, driver, cookie_save_path='cookies.json'):
    """
    Selenium을 사용하여 웹사이트에 로그인하고 쿠키 정보를 추출하는 함수

    :param url: 로그인할 웹사이트 URL
    :param username: 로그인 아이디
    :param password: 로그인 비밀번호
    :param driver: Selenium WebDriver 객체
    :param cookie_save_path: 쿠키 정보를 저장할 파일 경로
    :return: 쿠키 정보 딕셔너리
    """
    try:
        # 웹사이트 접속
        driver.get("https://m.naver.com/")
        time.sleep(2)
        driver.get(url)

        # 로그인 페이지 로딩 대기
        wait = WebDriverWait(driver, 5)
        time.sleep(5)
        username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#id')))
        username_field.click()

        time.sleep(1)
        for i in username:
            time.sleep(1)
            pyautogui.keyDown(i)

        # 비밀번호 입력 필드 찾기
        password_field = driver.find_element(By.CSS_SELECTOR, '#pw')
        password_field.click()

        for i in password:
            time.sleep(1)
            pyautogui.keyDown(i)

        time.sleep(1)

        # 로그인 버튼 클릭
        submit_button = driver.find_element(By.CSS_SELECTOR, '#submit_btn')
        submit_button.click()
        time.sleep(2)

        # 로그인 후 페이지 접근
        allow_button = driver.find_element(By.CSS_SELECTOR, '#notreg')
        allow_button.click()

        driver.get("https://my.naver.com/")

        # 쿠키 정보 추출
        cookies = driver.get_cookies()
        cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

        # 쿠키 정보 저장
        if cookie_save_path:
            with open(cookie_save_path, 'w', encoding='utf-8') as f:
                f.write(cookie_string)

        print("로그인 및 쿠키 추출 성공!")
        return cookies

    except Exception as e:
        print(f"로그인 또는 쿠키 추출 중 오류 발생: {e}")
        return None


def perform_other_task(driver):
    """
    1분마다 실행할 다른 작업
    """
    while True:
        # 여기에 1분마다 실행할 작업을 추가
        catch_articles(driver)
        print(f"[{time.ctime()}] catch_articles() 함수 실행 완료")
        time.sleep(60)

def main():
    driver = init_driver()


    config = load_config()
    url = 'https://nid.naver.com/nidlogin.login?svctype=262144'
    username = config['username']
    password = config['password']

    # 1시간마다 쿠키를 가져오는 작업을 별도의 쓰레드에서 실행
    def cookie_task():
        while True:
            login_and_get_cookies(url, username, password, driver)
            time.sleep(3600)  # 1시간 대기

    # 쿠키 가져오는 작업을 별도의 쓰레드로 실행
    cookie_thread = threading.Thread(target=cookie_task)
    cookie_thread.start()

    # 1분마다 다른 작업을 실행
    perform_other_task(driver)

if __name__ == "__main__":
    main()