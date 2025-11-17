import requests
import json
import csv
import time
from datetime import datetime
import logging
from pathlib import Path

import requests
import json
from bs4 import BeautifulSoup
from selenium import webdriver  # selenium君からwebdriverをインポート
from selenium.webdriver.common.by import By
from datetime import datetime

# args
search_word = "美女と野獣"
attraction_all = False

# config
xpath_list = {
    "all_attraction": ".//div[contains(@class, 'listTextArea') and .//h3[contains(@class, 'heading3') and normalize-space(text()) != '']]",
    "select_attraction":f"//div[div[h3[contains(text(), '{search_word}')]]]",
    "attraction_name": './/h3[contains(@class, "heading3")]',
    "waiting_time": ".//div[contains(@class, 'realtimeInformation')]//span[contains(@class, 'time')]"
}

# 現在時刻を取得
dt = datetime.now()

# datetime型から文字列に変換
datetime_str = dt.strftime("%Y-%m-%d %H:%M:%S")

driver = webdriver.Chrome()  # webdriverをChromeのヤツで使います。
url = 'https://www.tokyodisneyresort.jp/tdl/attraction.html'

driver.get(url)  # driverがurlのページを開きます

# realtime_info_xpath = ".//div[contains(@class, 'realtimeInformation')]"
# time_xpath = ".//span[contains(@class, 'time')]"
# waiting_time_xpath = ".//div[p[contains(@class, 'waitingtime')]]"
# waiting_xpath = ".//p[contains(@class, 'waitingtime')]"

if attraction_all:
    print("全アトラクションのデータ取得処理")
else:
    # 特定のアトラクションに絞って取得
    elem = driver.find_element(
        By.XPATH, xpath_list["select_attraction"])

    if elem:
        attraction_name = elem.find_element(By.XPATH, xpath_list["attraction_name"])
        waiting_time = elem.find_element(By.XPATH, xpath_list["waiting_time"])

# elems = driver.find_elements(By.XPATH, '')

# すべてのアトラクションの情報を取得
# 要素のテキストを出力
# for elem in elems:
#     if elem.text != '':
#         print("elem text:", elem.text)

# 終了
driver.quit()