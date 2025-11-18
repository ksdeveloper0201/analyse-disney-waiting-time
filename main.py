import csv
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

interval_minutes = 5  # 通常の待機時間（分）
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

# config
xpath_list = {
    "all_attraction": ".//div[contains(@class, 'listTextArea') and .//h3[contains(@class, 'heading3') and normalize-space(text()) != '']]",
    "select_attraction":f"//div[div[h3[contains(text(), '{search_word}')]]]",
    "attraction_name": './/h3[contains(@class, "heading3")]',
    "waiting_time": ".//div[contains(@class, 'realtimeInformation')]//span[contains(@class, 'time')]"
}

class DisneyWaitTimeScraper:
    def __init__(self, isLand=True):
        self.place = "tdl" if isLand else "tds"

    def _init_csv(self, header: List[str]) -> None:
        """CSVファイルのヘッダーを初期化"""
        # csvファイルの定義
        today = datetime.now().strftime('%Y%m%d')
        self.output_file=f"{today}_all_{self.place}_wait_times.csv"

        file_exists = Path(self.output_file).exists()
        if not file_exists:
            with open(self.output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(header)
            logging.info(f"CSVファイルを作成: {self.output_file}")
    
    def get_element(self, elem: any, xpath: str) -> str:
        try:
            return elem.find_element(By.XPATH, xpath).text   
        except Exception:
            return ""
    
    def fetch_wait_times(self) -> Dict[str, str]:
        """
        待ち時間データを取得
        """
        
        try:
            # 公式HPからスクレイピング
            url = f"https://www.tokyodisneyresort.jp/{self.place}/attraction.html"

            driver = webdriver.Chrome()  # webdriverをChromeのヤツで使います。
            # オプションを設定
            # options = Options()
            # options.add_argument('--headless')        # ヘッドレスモード
            # options.add_argument('--disable-gpu')     # GPU無効化（Windows環境で推奨）
            # options.add_argument('--no-sandbox')      # Linux環境で必要な場合あり
            # options.add_argument('--disable-dev-shm-usage')  # メモリ不足対策
            # driver = webdriver.Chrome(options=options)  # ヘッドレスで起動
            driver.get(url)  # driverがurlのページを開きます
            
            print("全アトラクションのデータ取得処理")
            elems = driver.find_elements(
                By.XPATH, xpath_list["all_attraction"]
            )

            attractions_data = {
                self.get_element(elem, xpath_list["attraction_name"]):
                self.get_element(elem, xpath_list["waiting_time"])
                for elem in elems
            }
            return attractions_data

        except NoSuchElementException:
            logging.error("要素が見つかりませんでした")
            return {}
        except Exception as e:
            logging.error(f"エラーが発生しました: {e}")
            return {}
        finally:
            if driver:
                driver.quit()
    
    def save_to_csv(self, attractions: Dict[str, str]):
        """データをCSVファイルに保存"""
        if not attractions:
            logging.warning("保存するデータがありません")
            return
        
        try:
            print('全アトラクションの処理')
            with open(self.output_file, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                current_time = [datetime.now().strftime('%H:%M')]
                writer.writerow(current_time + list(attractions.values()))
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
                    # データを集約するcsvの作成
                    headers = ["時間"] + list(attractions.keys())
                    self._init_csv(headers)
                    # csvへの書き込み
                    self.save_to_csv(attractions)
                    logging.info(f"次回取得: {interval_minutes}分後")
                else:
                    logging.warning("データが取得できませんでした")
                
                now = datetime.now()
                # 指定時間待機
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

def run_both(interval_minutes=5):
    scraper_land = DisneyWaitTimeScraper(isLand=True)
    scraper_sea = DisneyWaitTimeScraper(isLand=False)

    while True:
        logging.info("ランドのデータ取得中...")
        attractions_land = scraper_land.fetch_wait_times()
        if attractions_land:
            headers = ["時間"] + list(attractions_land.keys())
            scraper_land._init_csv(headers)
            scraper_land.save_to_csv(attractions_land)

        logging.info("シーのデータ取得中...")
        attractions_sea = scraper_sea.fetch_wait_times()
        if attractions_sea:
            headers = ["時間"] + list(attractions_sea.keys())
            scraper_sea._init_csv(headers)
            scraper_sea.save_to_csv(attractions_sea)

        logging.info(f"次回取得: {interval_minutes}分後")
        time.sleep(interval_minutes * 60)

def main():
    # スクレイパーのインスタンス作成
    scraper = DisneyWaitTimeScraper(isLand=True)
    
    # 5分おきに実行
    scraper.run_continuous(interval_minutes=5)
    

if __name__ == "__main__":
    main()