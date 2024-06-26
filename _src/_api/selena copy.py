from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import re
import os
import zipfile
import requests
import chromedriver_autoinstaller


#add internal libary
from . import loggas, configus

#make logpath
logging= loggas.logger

#loading config data
config_path = 'static\config\config.json'
selenium_path = 'static\config\selenium.json'
message_path = configus.load_config(config_path)['message_path']

#=================================================================================================
def get_chrome_ver_from_googlechromelabs(url = "https://googlechromelabs.github.io/chrome-for-testing/#stable"):
    newest_chorme_driver_downloader_url = ""
    r = requests.get(url)
    for i in r.text.split("<tr "):
        seached_all = re.findall('https.*chromedriver-win64.zip',i)
        if len(seached_all) > 0:
            logging.info(seached_all)
            newest_chorme_driver_downloader_url = seached_all[0]
            break
    return newest_chorme_driver_downloader_url

def download_chrome_dirver(file_name = None , url =None ):
    with open(file_name, "wb") as file:
        response = requests.get(url)
        file.write(response.content)
    zip_file = zipfile.ZipFile(file_name)
    zip_file.extractall(path=os.path.dirname(file_name))
    return 0

def get_chrome_driver(selenium_path=selenium_path):
    #road selenium config
    selenium_data = configus.load_config(selenium_path)
    logging.info(selenium_data)
    chorme_driver_downloader = selenium_data['chrome_driver_down_path']
    googlechromelabs = selenium_data['googlechromelabs_github']
    chorme_driver_downloader_url = selenium_data['chorme_driver_downloader_url']
    
    #check insatlled driver version from chromelabs
    newest_chorme_driver_downloader_url = get_chrome_ver_from_googlechromelabs(url= googlechromelabs)

    if newest_chorme_driver_downloader_url == chorme_driver_downloader_url:
        logging.info(f'version is same - {newest_chorme_driver_downloader_url}')
        return 0
    else:
        logging.info(f'version is dfff')
        logging.info(f'current - {chorme_driver_downloader_url}')
        logging.info(f'new one - {newest_chorme_driver_downloader_url}')
        logging.info(f'start to exchange new one')
        download_chrome_dirver(file_name= chorme_driver_downloader, url=newest_chorme_driver_downloader_url)
        selenium_data['chorme_driver_downloader_url'] = newest_chorme_driver_downloader_url
        configus.save_config(selenium_data,selenium_path)
        return 0
#=================================================================================================
# main function
def call_drivier(headless=True):
    #set up chromedriver
    selenium_data = configus.load_config(selenium_path)
    chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]  #크롬드라이버 버전 확인
    options = webdriver.ChromeOptions()
    #options.add_argument('disable-gpu')
    options.add_argument('lang=ko_KR')
    if headless is False:
        logging.info(f'headless is {headless}')
        options.add_argument('headless') # HeadlessChrome 사용시 브라우저를 켜지않고 크롤링할 수 있게 해줌
    else:
        options.add_argument('window-size=1920x1080')

    #options.add_argument('User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36')
    # 헤더에 headless chrome 임을 나타내는 내용을 진짜 컴퓨터처럼 바꿔줌.
    try:
        logging.info('check chromedriver version')
        get_chrome_driver()
        driver = webdriver.Chrome(selenium_data["chromedriver"],options=options)
    except:
        logging.info('loading chromedriver failed')
        return None
    

#=================================================================================================
# this is function of selenium 
def moveToNextTestStep(driver):
    #spand step list to 50
    #this is running when test step is over 50 (not need currently)
    time.sleep(0.5)
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.element_to_be_clickable((By.ID, 'pagination-dropdown-button')))
    driver.find_element("xpath",'//*[@id="pagination-dropdown-button"]').click()
    time.sleep(0.5)
    return 0

def login(driver):
    config_data =configus.load_config(config_path)
    jira_login_url = config_data['jira_login_url']
    jira_id = config_data['id']
    jira_password = config_data['password']
    #start login
    logging.info('start login')
    driver.get(jira_login_url)
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.element_to_be_clickable((By.ID, 'login-form-submit')))
    username=driver.find_element("xpath",'//*[@id="login-form-username"]')
    username.send_keys(jira_id)
    password=driver.find_element("xpath",'//*[@id="login-form-password"]')
    password.send_keys(jira_password)
    time.sleep(0.5)
    driver.find_element("xpath",'//*[@id="login-form-submit"]').click()
    return 0




