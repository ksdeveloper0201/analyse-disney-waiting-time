import requests
import json
import csv
import time
from datetime import datetime
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options # オプションを使うために必要
from selenium.common.exceptions import NoSuchElementException
import time
from datetime import datetime, timedelta

interval_minutes = 5  # 通常の待機時間（分）

now = datetime.now()
start_hour = 9
end_hour = 21


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('disney_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# args
search_word = "美女と野獣"
is_all_attraction = False

# config
xpath_list = {
    "all_attraction": ".//div[contains(@class, 'listTextArea') and .//h3[contains(@class, 'heading3') and normalize-space(text()) != '']]",
    "select_attraction":f"//div[div[h3[contains(text(), '{search_word}')]]]",
    "attraction_name": './/h3[contains(@class, "heading3")]',
    "waiting_time": ".//div[contains(@class, 'realtimeInformation')]//span[contains(@class, 'time')]"
}

class DisneyWaitTimeScraper:
    def __init__(self, output_file='disney_wait_times.csv'):
        self.output_file = output_file
        # CSVファイルの初期化
        self._init_csv()
    
    def _init_csv(self):
        """CSVファイルのヘッダーを初期化"""
        file_exists = Path(self.output_file).exists()
        if not file_exists:
            with open(self.output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['取得日時', 'アトラクション名', '待ち時間(分)', 'ステータス'])
            logging.info(f"CSVファイルを作成: {self.output_file}")
    
    def fetch_wait_times(self):
        """
        待ち時間データを取得
        
        注意: 以下のAPIエンドポイントは例です。
        実際には以下のいずれかの方法でデータを取得してください:
        
        1. 公式アプリのAPIを調査（リバースエンジニアリングは規約違反の可能性あり）
        2. wiki API などのサードパーティサービスを利用
        3. 公式ウェブサイトのHTMLをパース（構造変更に注意）
        """
        
        try:
            # 方法1: wiki API を使用する例
            # 無料で使用できるAPIサービス
            url = 'https://www.tokyodisneyresort.jp/tdl/attraction.html'

            driver = webdriver.Chrome()  # webdriverをChromeのヤツで使います。
            # option = Options()                          # オプションを用意
            # option.add_argument('--headless')           # ヘッドレスモードの設定を付与
            # driver = webdriver.Chrome(options=option)
            driver.get(url)  # driverがurlのページを開きます
            
            if is_all_attraction:
                print("全アトラクションのデータ取得処理")
                return
            else:
                # 特定のアトラクションに絞って取得
                elem = driver.find_element(
                    By.XPATH, xpath_list["select_attraction"])

                if not elem:
                    print('not elem')
                    return

                attraction_name = elem.find_element(By.XPATH, xpath_list["attraction_name"])
                waiting_time = elem.find_element(By.XPATH, xpath_list["waiting_time"])
                data = {
                    'name': attraction_name.text,
                    'waitTime': waiting_time.text
                }

                driver.quit()
                return self._parse_attraction_data(data, is_all_attraction)
            # return self._parse_themeparks_data(data)

            print("要素が見つかりました:", elem.text)
        except NoSuchElementException:
            logging.error("要素が見つかりませんでした")
            return []
        except Exception as e:
            logging.error(f"エラーが発生しました: {e}")
            return []
    
    def _parse_attraction_data(self, data, is_all_attraction):
        """themeparks.wiki APIのデータをパース"""
        attractions = []
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if is_all_attraction:
            print('all attraction parse')
        else:
            attraction = {
                '取得日時': current_time,
                'アトラクション名': data.get('name', 'N/A'),
                '待ち時間': data.get('waitTime', 'N/A'),
            }
            attractions.append(attraction)
        
        return attractions
    
    def save_to_csv(self, attractions):
        """データをCSVファイルに保存"""
        if not attractions:
            logging.warning("保存するデータがありません")
            return
        
        try:
            with open(self.output_file, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                for attr in attractions:
                    writer.writerow([
                        attr['取得日時'],
                        attr['アトラクション名'],
                        attr['待ち時間'],
                    ])
            logging.info(f"{len(attractions)}件のデータを保存しました")
        except Exception as e:
            logging.error(f"CSV保存エラー: {e}")
    
    def run_continuous(self, interval_minutes=5):
        """指定された間隔でデータ取得を継続"""
        logging.info(f"スクレイピング開始（{interval_minutes}分間隔）")
        logging.info("停止するには Ctrl+C を押してください")
        
        try:
            while True:
                logging.info("データ取得中...")
                attractions = self.fetch_wait_times()
                
                if attractions:
                    self.save_to_csv(attractions)
                    logging.info(f"次回取得: {interval_minutes}分後")
                else:
                    logging.warning("データが取得できませんでした")
                
                # 指定時間待機
                # time.sleep(10)
                if start_hour <= now.hour < end_hour:
                    # 9時〜21時の間なら通常の待機
                    time.sleep(interval_minutes * 60)
                else:
                    # それ以外なら次の9時まで待機
                    # 今日の9時を基準にする
                    next_start = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)

                    if now.hour >= end_hour:
                        # 21時以降なら翌日の9時
                        next_start += timedelta(days=1)

                    # 待機秒数を計算
                    wait_seconds = (next_start - now).total_seconds()
                    print(f"次の9時まで {wait_seconds/3600:.2f} 時間待機します")
                    time.sleep(wait_seconds)                
        except KeyboardInterrupt:
            logging.info("\nスクレイピングを停止しました")
        except Exception as e:
            logging.error(f"予期しないエラー: {e}")

def main():
    # スクレイパーのインスタンス作成
    scraper = DisneyWaitTimeScraper(output_file='disney_wait_times.csv')
    
    # 5分おきに実行
    scraper.run_continuous(interval_minutes=5)

if __name__ == "__main__":
    main()