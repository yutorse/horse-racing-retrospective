"""出馬票・レース情報取得モジュール"""

from typing import List, Optional
from datetime import date, timedelta
import requests
from bs4 import BeautifulSoup
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from src.models import Race, Horse


class Scraper:
    """出馬票・レース情報スクレイパー"""
    
    BASE_URL = "https://www.jra.go.jp"
    JRADB_BASE_URL = "https://www.jra.go.jp/JRADB/accessD.html"
    
    def __init__(self, headless: bool = True):
        """
        スクレイパーを初期化
        
        Args:
            headless: ヘッドレスモードで実行するかどうか
        """
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.jra.go.jp/"
        })
        self.headless = headless
        self.driver = None
    
    def _get_driver(self):
        """
        SeleniumのWebDriverを取得
        
        Returns:
            WebDriverインスタンス
        """
        if self.driver is None:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        return self.driver
    
    def _close_driver(self):
        """WebDriverを閉じる"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __del__(self):
        """デストラクタ"""
        self._close_driver()
    
    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        URLからHTMLページを取得してパース
        
        Args:
            url: 取得するURL
            
        Returns:
            BeautifulSoupオブジェクト（失敗時はNone）
        """
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"アクセス拒否 (403): {url}")
                print("JRAサイトがスクレイピングをブロックしている可能性があります")
            else:
                print(f"HTTPエラー ({e.response.status_code}): {url}")
            return None
        except Exception as e:
            print(f"ページ取得エラー ({url}): {e}")
            return None
    
    
    def _parse_horse_name(self, text: str) -> str:
        """
        馬名を抽出（余分な文字を除去）
        
        Args:
            text: 抽出元のテキスト
            
        Returns:
            馬名
        """
        # 余分な空白や改行を除去
        name = re.sub(r'\s+', '', text.strip())
        return name
    
    
    def _navigate_to_menu_page(self, mode: str = 'prediction'):
        """
        TOPページからステップ1（クイックメニュー）をクリックして
        開催日/場選択ページ（ステップ2）へ遷移する
        """
        driver = self._get_driver()
        wait = WebDriverWait(driver, 10)
        
        # 1. TOPページ
        print(f"アクセス中: {self.BASE_URL} (モード: {mode})")
        driver.get(self.BASE_URL)
        time.sleep(1)

        # 2. Step 1: クイックメニュー選択
        link_text_keyword = "出馬" if mode == 'prediction' else "レース結果"
        print(f"ステップ1を実行中: '{link_text_keyword}'リンクを探しています...")
        
        try:
            candidates = driver.find_elements(By.CSS_SELECTOR, "div.inner ul li a")
            target_link = None
            
            # キーワードで探す
            for c in candidates:
                try:
                    if c.is_displayed() and link_text_keyword in c.text:
                        target_link = c
                        break
                except:
                    continue
            
            # 見つからない場合のフォールバック
            if not target_link and len(candidates) >= 1:
                displayed_candidates = [c for c in candidates if c.is_displayed()]
                if displayed_candidates:
                    # prediction (出馬表) は1番目、retrospective (レース結果) は通常3番目
                    idx = 0 if mode == 'prediction' else 2
                    if len(displayed_candidates) > idx:
                        target_link = displayed_candidates[idx]

            if target_link:
                print(f"クリック(1): {target_link.text}")
                target_link.click()
                time.sleep(1)
            else:
                raise Exception(f"'{link_text_keyword}'リンクが見つかりません")
                
        except Exception as e:
            print(f"ステップ1エラー: {e}")
            raise e
            
        return driver
    
    def get_active_races(self, mode: str = 'prediction') -> List[Race]:
        """
        現在アクティブな（タブに表示されている）全てのレース情報を取得
        
        Args:
            mode: 'forecast' (予想) or 'retrospective' (回顧)
            
        Returns:
            レース情報のリスト
        """
        races = []
        print(f"アクティブなレースを取得中... (モード: {mode})")
        
        try:
            # Step 1: メニューページへ遷移
            driver = self._navigate_to_menu_page(mode=mode)
            
            # Step 2: 開催日/場リンク (Meeting Links) の数を取得
            # JRA出馬表もレース結果も基本構造(link_list)は共通
            print("ステップ2を実行中: 開催日/場リンクをカウント...")
            elements = driver.find_elements(By.CSS_SELECTOR, "div#main div.link_list a")
            if not elements:
                # フォールバック (以前のセレクタなど)
                elements = driver.find_elements(By.CSS_SELECTOR, "div.waku a, td.syutsuba a")
            
            meeting_count = len([e for e in elements if e.is_displayed()])
            
            print(f"  {meeting_count}件の開催日/場が見つかりました")
            
            # 各開催日/場ごとループ (インデックスベース)
            for m_idx in range(meeting_count):
                print(f"  開催 {m_idx+1}/{meeting_count} を巡回中...")
                
                try:
                    # 2回目以降、または要素再取得のために再遷移
                    if m_idx > 0:
                        driver = self._navigate_to_menu_page(mode=mode)
                    
                    # 要素を再取得
                    elements = driver.find_elements(By.CSS_SELECTOR, "div#main div.link_list a")
                    if not elements:
                        elements = driver.find_elements(By.CSS_SELECTOR, "div.waku a, td.syutsuba a")
                    
                    valid_elements = [e for e in elements if e.is_displayed()]
                    if m_idx < len(valid_elements):
                        target_link = valid_elements[m_idx]
                    
                    if not target_link:
                        print(f"    警告: インデックス {m_idx} のリンクが見つかりませんスキップします")
                        continue
                        
                    print(f"    クリック: {target_link.text}")
                    target_link.click()
                    time.sleep(1)
                    
                    # Step 3: レース詳細リンクを全て収集
                    wait = WebDriverWait(driver, 10)
                    race_links = []
                    
                    # レース一覧テーブル(table#race_list) または 出馬表セル(td.syutsuba) からリンクを取得
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table#race_list, td.syutsuba")))
                    
                    # 1. table#race_list (結果一覧など)
                    elements = driver.find_elements(By.CSS_SELECTOR, "table#race_list tbody th a")
                    if not elements:
                        # 2. td.syutsuba (出馬表ページ)
                        elements = driver.find_elements(By.CSS_SELECTOR, "td.syutsuba a")
                    
                    race_links = [e.get_attribute('href') for e in elements if e.get_attribute('href')]
                    
                    race_links = list(dict.fromkeys(race_links))
                    print(f"    -> {len(race_links)}件のレースが見つかりました")
                    
                    # 各レースへアクセス
                    for r_idx, race_url in enumerate(race_links):
                        # print(f"      レース {r_idx+1}/{len(race_links)} 処理中")
                        try:
                            driver.get(race_url)
                            time.sleep(1)
                            
                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            
                            # 日付指定なしでパース（ページから抽出させる）
                            dummy_date = date.today() 
                            
                            current_races = self._parse_jra_entry_page(soup, dummy_date, race_url)
                            if not current_races:
                                current_races = self._parse_jradb_page(soup, dummy_date, race_url)
                            
                            if current_races:
                                races.extend(current_races)
                            else:
                                pass # 警告省略
                                
                            time.sleep(0.5)
                        except Exception as e:
                            print(f"      レース処理エラー: {e}")
                            continue
                            
                except Exception as e:
                    print(f"  開催処理エラー: {e}")
                    continue

        except Exception as e:
             print(f"全体エラー: {e}")

        print(f"合計 {len(races)}件のレース情報を取得しました")
        return races

    def _parse_jra_entry_page(self, soup: BeautifulSoup, race_date: date, url: str = "") -> List[Race]:
        """
        JRA出馬表ページをパース（Seleniumまたは通常のHTML）
        """
        races = []
        
        # 実際の開催日をページから抽出
        actual_date = race_date # デフォルト
        try:
            page_text = soup.get_text()
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', page_text)
            if date_match:
                y = int(date_match.group(1))
                m = int(date_match.group(2))
                d = int(date_match.group(3))
                actual_date = date(y, m, d)
                print(f"  ページから日付抽出: {actual_date}")
        except Exception as e:
            print(f"  日付抽出エラー: {e}")
        
        # レース情報を含むテーブルやセクションを探す
        # JRAサイトの構造に応じて調整が必要
        
        # レーステーブルを探す
        race_tables = soup.find_all('table', class_=re.compile(r'race|entry|shutuba', re.I))
        
        if not race_tables:
            # より広範囲にテーブルを探す
            race_tables = soup.find_all('table')
            print(f"テーブル要素を{len(race_tables)}件発見")
        
        # レース情報を含む可能性のあるdivやsectionも探す
        race_sections = soup.find_all(['div', 'section'], class_=re.compile(r'race|entry', re.I))
        
        for section in race_sections:
            # レース名を取得
            race_name_elem = section.find(['h2', 'h3', 'h4', 'span', 'div'], 
                                         string=re.compile(r'R\d+|第\d+R|レース\d+', re.I))
            if not race_name_elem:
                continue
            
            race_name = race_name_elem.get_text(strip=True)

            # レース番号を抽出 (例: "1R" or "第1R")
            race_num = None
            
            # 1. URLから抽出
            if url:
                # CNAMEパターン: pw01sde1006202401041120240104 のような形式
                # 最後の8桁日付(20240104)の直前の2桁(11)がレース番号
                cname_match = re.search(r'CNAME=.*(\d{2})\d{8}$', url)
                if cname_match:
                    race_num = int(cname_match.group(1))
                
                if not race_num:
                    num_match = re.search(r'race_no=(\d+)', url)
                    if num_match:
                        race_num = int(num_match.group(1))

            # 2. HTMLから抽出 (URLで見つからない場合)
            if not race_num and race_name_elem:
                # テキストまたはimgのaltから抽出を試みる
                text_to_search = race_name_elem.get_text(strip=True)
                img = race_name_elem.find('img')
                if img and img.get('alt'):
                    text_to_search += " " + img.get('alt')
                
                num_match = re.search(r'(\d+)R', text_to_search)
                if num_match:
                    race_num = int(num_match.group(1))
            
            print(f"  抽出結果(URL: {url[-30:] if url else 'none'}): レース名='{race_name}', R={race_num}")
            
            # レース情報を抽出
            race_info = self._extract_race_info_from_section(section, race_date)
            
            # 出走馬情報を抽出
            horses = self._extract_horses_from_section(section)
            
            race = Race(
                name=race_info.get('name', race_name),
                date=actual_date,
                venue=race_info.get('venue', '不明'),
                distance=race_info.get('distance', 0),
                grade=race_info.get('grade'),
                condition=race_info.get('condition'),
                race_number=race_num,
                horses=horses
            )
            races.append(race)
        
        # テーブルからも抽出を試みる
        for table in race_tables[:10]:  # 最初の10個のテーブルを確認
            # レース名を含む行を探す
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    text = cell.get_text(strip=True)
                    if re.search(r'R\d+|第\d+R', text):
                        # レース情報を抽出
                        race_info = self._extract_race_info_from_row(row, race_date)
                        if race_info:
                            horses = self._extract_horses_from_table(table)
                            race = Race(
                                name=race_info.get('name', text),
                                date=actual_date,
                                venue=race_info.get('venue', '不明'),
                                distance=race_info.get('distance', 0),
                                grade=race_info.get('grade'),
                                condition=race_info.get('condition'),
                                horses=horses
                            )
                            races.append(race)
                            break
        
        return races
    
    def _extract_race_info_from_section(self, section, race_date: date) -> dict:
        """セクションからレース情報を抽出"""
        info = {}
        
        # レース名
        name_elem = section.find(string=re.compile(r'.+'))
        if name_elem:
            info['name'] = name_elem.strip()
        
        # 距離
        distance_text = section.find(string=re.compile(r'\d+m|\d+メートル'))
        if distance_text:
            distance_match = re.search(r'(\d+)', distance_text)
            if distance_match:
                info['distance'] = int(distance_match.group(1))
        
        return info
    
    def _extract_horses_from_section(self, section) -> List[Horse]:
        """セクションから出走馬情報を抽出"""
        horses = []
        
        # テーブル内の行を探す
        rows = section.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            # 馬名を探す（通常は2列目以降）
            for cell in cells[1:]:
                text = cell.get_text(strip=True)
                # 馬名らしいテキストを探す
                if len(text) > 1 and not re.match(r'^[\d\s\-\.]+$', text):
                    horse = Horse(name=self._parse_horse_name(text))
                    horses.append(horse)
                    break
        
        return horses
    
    def _extract_race_info_from_row(self, row, race_date: date) -> Optional[dict]:
        """行からレース情報を抽出"""
        info = {}
        cells = row.find_all(['td', 'th'])
        
        for cell in cells:
            text = cell.get_text(strip=True)
            # 距離情報
            if 'm' in text or 'メートル' in text:
                distance_match = re.search(r'(\d+)', text)
                if distance_match:
                    info['distance'] = int(distance_match.group(1))
        
        return info if info else None
    
    def _extract_horses_from_table(self, table) -> List[Horse]:
        """テーブルから出走馬情報を抽出 (詳細版)"""
        horses = []
        rows = table.find_all('tr')
        
        for row in rows:
            # 馬名要素を探す (td.horse)
            horse_td = row.find('td', class_='horse')
            if not horse_td:
                continue
            
            # 馬名
            name_elem = horse_td.find('div', class_='name')
            if not name_elem:
                continue
            name = self._parse_horse_name(name_elem.get_text(strip=True))
            if not name:
                continue
            
            # 性齢・斤量・騎手が入っている td.jockey を探す
            jockey_td = row.find('td', class_='jockey')
            gender = None
            age = None
            weight = None
            jockey = None
            
            if jockey_td:
                # 性齢 (p.age)
                age_elem = jockey_td.find('p', class_='age')
                if age_elem:
                    age_text = age_elem.get_text(strip=True)
                    match = re.search(r'([一-龠])(\d+)', age_text)
                    if match:
                        gender = match.group(1)
                        age = match.group(2)
                
                # 斤量 (p.weight)
                weight_elem = jockey_td.find('p', class_='weight')
                if weight_elem:
                    weight = weight_elem.get_text(strip=True)
                
                # 騎手 (a)
                jockey_elem = jockey_td.find('a')
                if jockey_elem:
                    jockey = jockey_elem.get_text(strip=True).strip()

            horse = Horse(
                name=name,
                gender=gender,
                age=age,
                weight=weight,
                jockey=jockey
            )
            horses.append(horse)
        
        return horses
    
    
    def _parse_jradb_page(self, soup: BeautifulSoup, race_date: date, url: str = "") -> List[Race]:
        """
        JRA競馬データベース（結果など）のページをパース
        """
        races = []
        
        # テーブルを探す
        tables = soup.find_all('table')
        if not tables:
            return races
            
        # ハロンタイム（ラップタイム）の抽出
        lap_time = None
        try:
            lap_th = soup.find('th', string=re.compile(r'ハロンタイム'))
            if lap_th:
                lap_td = lap_th.find_next_sibling('td')
                if lap_td:
                    lap_time = lap_td.get_text(strip=True)
                    print(f"  ラップタイム抽出: {lap_time}")
        except Exception as e:
            print(f"  ラップタイム抽出エラー: {e}")

        # 最初のテーブルがレース結果/出走表と仮定
        target_table = tables[0]
        horses = []
        
        rows = target_table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                continue
            
            # ヘッダー行判定
            row_text = row.get_text()
            if "馬名" in row_text:
                continue
            
            # 馬ごとのデータ抽出
            current_horse = None
            
            # レース結果(Result): [着順(0), 枠(1), 馬番(2), 馬名(3), 性齢(4), 負担重量(5), 騎手を(6), タイム(7), 着差(8), コーナー(9), 上がり(10), ..., 馬体重(13)]
            if len(cells) > 10 and re.match(r'^\d+$', cells[0].get_text(strip=True)):
                # 結果ページ
                name_raw = cells[3].get_text(strip=True)
                match = re.match(r'^([^\d\(\[<]+)', name_raw)
                if match:
                    name = match.group(1).strip()
                    name = re.sub(r'[▲△☆★◇]', '', name)
                    
                    # 馬体重の抽出 (クラス指定 td.h_weight)
                    h_weight = None
                    for cell in cells:
                        if 'h_weight' in cell.get('class', []):
                            h_weight = cell.get_text(strip=True)
                            break
                    if not h_weight and len(cells) > 13:
                        h_weight = cells[13].get_text(strip=True)

                    # 性齢 (通常 5列目/index 4)
                    gender_age_raw = cells[4].get_text(strip=True)
                    gender = None
                    age = None
                    if gender_age_raw:
                        ga_match = re.match(r'([一-龠])(\d+)', gender_age_raw)
                        if ga_match:
                            gender = ga_match.group(1)
                            age = ga_match.group(2)

                    # 通過順位 (9列目/index 8または9)
                    # li要素を個別に取得してハイフンで繋ぐ
                    passing_order_cell = cells[9]
                    li_elements = passing_order_cell.find_all('li')
                    if li_elements:
                        passing_order = "-".join([li.get_text(strip=True) for li in li_elements])
                    else:
                        passing_order = passing_order_cell.get_text(strip=True)

                    # 騎手 (7列目/index 6)
                    jockey_cell = cells[6]
                    jockey_elem = jockey_cell.find('a')
                    jockey_name = (jockey_elem.get_text(strip=True) if jockey_elem else jockey_cell.get_text(strip=True)).strip()

                    current_horse = Horse(
                        name=name,
                        position=cells[0].get_text(strip=True),
                        gender=gender,
                        age=age,
                        jockey=jockey_name,
                        weight=cells[5].get_text(strip=True),
                        passing_order=passing_order,
                        last_3f=cells[10].get_text(strip=True),
                        finish_time=cells[7].get_text(strip=True) if len(cells) > 7 else None,
                        horse_weight=h_weight
                    )
            else:
                # 出馬表 (td.horse セレクタ優先)
                horse_td = row.find('td', class_='horse')
                if horse_td:
                    name_elem = horse_td.find('div', class_='name')
                    if name_elem:
                        name = self._parse_horse_name(name_elem.get_text(strip=True))
                        if name:
                            gender = None
                            age = None
                            weight = None
                            
                            jockey_td = row.find('td', class_='jockey')
                            if jockey_td:
                                age_elem = jockey_td.find('p', class_='age')
                                if age_elem:
                                    age_text = age_elem.get_text(strip=True)
                                    ga_match = re.search(r'([一-龠])(\d+)', age_text)
                                    if ga_match:
                                        gender = ga_match.group(1)
                                        age = ga_match.group(2)
                                
                                weight_elem = jockey_td.find('p', class_='weight')
                                if weight_elem:
                                    weight = weight_elem.get_text(strip=True)
                                
                                jockey_elem = jockey_td.find('a')
                                if jockey_elem:
                                    jockey = jockey_elem.get_text(strip=True)
                                    jockey = re.sub(r'[▲△☆★◇]', '', jockey).strip()

                            current_horse = Horse(
                                name=name,
                                gender=gender,
                                age=age,
                                weight=weight,
                                jockey=jockey
                            )
            
            if current_horse:
                horses.append(current_horse)
        
        if horses:
            # レース情報の抽出
            race_name = "レース詳細不明"
            venue = "JRA"
            distance = 0
            track_type = None
            track_condition = None
            
            # レース番号・名称要素の受動的特定
            # navigation barを除去するために、特定のヘッダー領域内を優先的に探す
            race_head = soup.find(class_=re.compile(r'race_header|race_head|race_number|race_data', re.I))
            r_num_elem = (race_head.find(class_=re.compile(r'num', re.I)) if race_head else None) or \
                         soup.find(class_=re.compile(r'race.*num|race_number', re.I))
            r_name_elem = (race_head.find(class_=re.compile(r'name', re.I)) if race_head else None) or \
                          soup.find(class_=re.compile(r'race.*name|race_title', re.I))

            # 実際の開催日をページから抽出
            actual_date = race_date # デフォルト
            try:
                page_text = soup.get_text()
                date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', page_text)
                if date_match:
                    y = int(date_match.group(1))
                    m = int(date_match.group(2))
                    d = int(date_match.group(3))
                    actual_date = date(y, m, d)

                # 競馬場名: 「n回{競馬場名}m日」から抽出 (例: 1回中山1日)
                venue_match = re.search(r'\d+回([一-龠]{2,3})\d+日', page_text)
                if venue_match:
                    venue = venue_match.group(1)
                
                # コース・距離 (div class="course" or div class="cell course")
                course_elem = soup.find(class_="course")
                if course_elem:
                    course_text = course_elem.get_text(strip=True)
                    # 距離の抽出 (カンマを除去)
                    dist_match = re.search(r'([\d,]+)(?=メートル|m)', course_text)
                    if dist_match:
                        distance = int(dist_match.group(1).replace(',', ''))
                    
                    # 詳細情報の抽出 (例: ダート・右)
                    detail_elem = course_elem.find(class_="detail")
                    if detail_elem:
                        track_type = detail_elem.get_text(strip=True).strip('()（）')
                    else:
                        # フォールバック: 芝/ダの判定
                        if '芝' in course_text:
                            track_type = '芝'
                        elif 'ダ' in course_text:
                            track_type = 'ダート'
                
                # 馬場状態 (div class="baba" > li:nth-child(2) > span.txt)
                baba_div = soup.find(class_="baba")
                if baba_div:
                    li_list = baba_div.find_all('li')
                    if len(li_list) >= 2:
                        txt_elem = li_list[1].find(class_="txt")
                        if txt_elem:
                            track_condition = txt_elem.get_text(strip=True)
                    elif len(li_list) == 1:
                        # 1つしかない場合のフォールバック
                        txt_elem = li_list[0].find(class_="txt")
                        if txt_elem:
                            track_condition = txt_elem.get_text(strip=True)
                
            except Exception as e:
                print(f"  レース詳細抽出エラー: {e}")

            # レース番号を抽出
            race_num = None
            
            # 1. URLから抽出
            if url:
                # CNAMEパターン: pw01sde1006202401041120240104 のような形式
                # 最後の8桁日付(20240104)の直前の2桁(11)がレース番号
                cname_match = re.search(r'CNAME=.*(\d{2})\d{8}$', url)
                if cname_match:
                    race_num = int(cname_match.group(1))
                
                if not race_num:
                    num_match = re.search(r'race_no=(\d+)', url)
                    if num_match:
                        race_num = int(num_match.group(1))
            
            # 2. HTMLから抽出 (URLで見つからない場合)
            if not race_num and r_num_elem:
                num_text = r_num_elem.get_text(strip=True)
                img = r_num_elem.find('img')
                if img and img.get('alt'):
                    num_text += " " + img.get('alt')
                
                num_match = re.search(r'(\d+)', num_text)
                if num_match:
                    race_num = int(num_match.group(1))

            # 名称の決定
            if r_name_elem:
                race_name = r_name_elem.get_text(strip=True).replace("JRA", "").strip()
            
            # fallback: div.name や div.cell.name を探す
            if race_name == "レース詳細不明":
                name_div = soup.find(['div', 'span'], class_=re.compile(r'^(cell\s+)?name$', re.I))
                if name_div:
                    race_name = name_div.get_text(strip=True).replace("JRA", "").strip()

            if race_name == "レース詳細不明" and r_num_elem:
                race_name = f"{r_num_elem.get_text(strip=True)}レース"
            
            # 最終 fallback: Titleから取得
            if race_name == "レース詳細不明":
                 title = soup.title.string if soup.title else ""
                 if title:
                     race_name = title.split('|')[0].replace('JRA', '').replace('結果', '').strip()

            print(f"  抽出結果(URL: {url[-30:] if url else 'none'}): レース名='{race_name}', R={race_num}, 会場='{venue}'")

            race = Race(
                name=race_name,
                date=actual_date,
                venue=venue,
                distance=distance,
                race_number=race_num,
                horses=horses,
                lap_time=lap_time,
                track_type=track_type,
                track_condition=track_condition
            )
            races.append(race)
            
        return races
    
    def _parse_race_entries_alternative(self, soup: BeautifulSoup, race_date: date) -> List[Race]:
        """
        代替パース方法（より柔軟な抽出）
        
        Args:
            soup: BeautifulSoupオブジェクト
            race_date: レース開催日
            
        Returns:
            レース情報のリスト
        """
        races = []
        
        # ページ全体からレース情報を探す
        # レース番号やレース名を含む要素を探す
        race_elements = soup.find_all(string=re.compile(r'第\d+R|R\d+'))
        
        for elem in race_elements:
            parent = elem.find_parent(['div', 'section', 'table'])
            if not parent:
                continue
            
            # 簡易的なレース情報を作成
            race_name = elem.strip()
            race = Race(
                name=race_name,
                date=race_date,
                venue="不明",  # URLから取得できない場合は不明
                distance=0,
                horses=[]
            )
            races.append(race)
        
        return races
    
    def get_races_for_week(self, week_start: date) -> List[Race]:
        """
        指定週の全レース情報を取得（回顧用）
        
        Args:
            week_start: 週の開始日
            
        Returns:
            レース情報のリスト
        """
        races = []
        current_date = week_start
        
        # 1週間分のレース情報を取得
        for i in range(7):
            date_to_check = current_date + timedelta(days=i)
            day_races = self.get_race_entries(date_to_check)
            races.extend(day_races)
            
            # レート制限を考慮して少し待機
            time.sleep(0.5)
        
        return races

