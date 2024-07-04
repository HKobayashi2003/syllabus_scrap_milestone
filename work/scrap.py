import os
import csv
import datetime
import time
import subprocess
from logging import getLogger, handlers, Formatter, DEBUG, ERROR
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from mojimoji import zen_to_han
from tqdm import tqdm
from bs4 import BeautifulSoup

faculties = ['基幹', '創造', '先進', '政経', '法学', '教育', '商学', '社学', '人科', 'スポーツ', '国際教養', '文構', '文', '人通', '芸術', '日本語', '留学', 'グローバル']


def set_logger():
    # 全体のログ設定
    # ファイルに書き出す。ログが100KB溜まったらバックアップにして新しいファイルを作る。
    logger = getLogger()
    logger.setLevel(DEBUG)
    handler = handlers.RotatingFileHandler(
        './app.log', maxBytes=100 * 1024, backupCount=3, encoding='utf-8'
    )
    formatter = Formatter('%(asctime)s : %(levelname)s : %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    block_logger = getLogger()
    block_logger.setLevel(ERROR)  # DEBUGやINFOなどのレベルのログを無視
    main_logger = getLogger("__main__")
    main_logger.setLevel(DEBUG)

set_logger()

def log(arg, level=DEBUG):
    logger = getLogger(__name__)
    if level == DEBUG:
        logger.debug(arg)
    elif level == ERROR:
        logger.error(arg)

def get_current():
    now = datetime.datetime.now()
    return now.year, now.month

def init_csv_file(year, term):
    with open(f'../data/syllabus_data_{year}_{term}.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['学部', 'コース名', '開講学期', '教員名', '曜日時限'])

def scrape_syllabus_data(driver, dest):
    log("Accessing Waseda's syllabus\n")
    driver.get('https://www.wsl.waseda.jp/syllabus/JAA101.php')
    with open(dest, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for name in tqdm(faculties, desc="Faculty", dynamic_ncols=True):
            log(f'Accessing {name} syllabus')
            select = Select(driver.find_element(By.NAME, 'p_gakubu'))
            select.select_by_visible_text(name)
            driver.execute_script("func_search('JAA103SubCon');")
            driver.execute_script("func_showchg('JAA103SubCon', '1000');")

            log(f"Scraping {name} data.")
            start_time = time.time()
            total_elements = 0
            while True:
                try:
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    rows = soup.select(
                        '#cCommon div div div div div:nth-child(1) div:nth-child(2) table tbody tr')
                    total_elements += len(rows[1:])
                    for row in rows[1:]:
                        cols = row.find_all('td')
                        writer.writerow([
                            name,
                            cols[2].text.strip(),
                            cols[5].text.strip(),
                            cols[3].text.strip(),
                            cols[6].text.strip()
                        ])
                    driver.find_element(
                        By.XPATH, '//*[@id="cHonbun"]/div[2]/table/tbody/tr/td[3]/div/div/p/a').click()
                except NoSuchElementException:
                    break
            log(f'Total Number of Subjects {name}: {total_elements}')
            log(f'Finished in {time.time() - start_time:.6f} seconds\n')
            driver.find_element(By.CLASS_NAME, 'ch-back').click()

def convert_zen_to_han(source_path, output_path):
    with open(source_path, 'r', newline='', encoding='utf-8') as infile, open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        for row in reader:
            writer.writerow([zen_to_han(cell, kana=False) for cell in row])


def process_schedule1(row):
    schedule = str(row[4])
    common_data = row[:4]
    expanded_rows = []

    if ":" in schedule:
        for time in schedule.split(":"):
            if len(time) < 4:
                continue
            time = time.replace("　", " ").replace("\n", " ")
            new_schedule = time.split(" ")[0]
            expanded_rows.append(common_data + [new_schedule])
    else:
        expanded_rows.append(list(row))
    return expanded_rows

def process_schedule2(row):
    schedule = str(row[4])
    common_data = row[:4]
    expanded_rows = []
    if "-" in schedule:
        schedule = schedule.replace(" ", "")
        day, time_range = schedule[0], schedule[1:]
        start, end = map(int, time_range.split("-"))
        for time in range(start, end + 1):
            new_schedule = f"{day}{time}時限"
            expanded_rows.append(common_data + [new_schedule])
    else:
        expanded_rows.append(list(row))
    return expanded_rows

def check_versions():
    try:
        chrome_version = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
        log("Google Chrome version:"+chrome_version.stdout)
    except FileNotFoundError:
        log("Google Chrome is not installed or not found in the PATH.", level=ERROR)

    try:
        chromedriver_version = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True)
        log("Chromedriver version:"+chromedriver_version.stdout)
    except FileNotFoundError:
        log("Chromedriver is not installed or not found in the PATH.", level=ERROR)

def format_syllabus_data(source_path, dest_path):
    with open(source_path, 'r', newline='', encoding='utf-8') as source, open(dest_path, 'w', newline='', encoding='utf-8') as dest:
        csvreader = csv.reader(source)
        csvwriter = csv.writer(dest)
        log("Formatting data.")
        rows = list(csvreader)
        for row in tqdm(rows, desc="Formatting data", leave=False):
            try:
                han_row = [zen_to_han(cell, kana=False) for cell in row]
                fmt1 = process_schedule1(han_row)
                for sub_row in fmt1:
                    fmt2 = process_schedule2(sub_row)
                    for final_row in fmt2:
                        csvwriter.writerow(final_row)
            except Exception as e:
                log(f"Error processing row: {row} - {e}", ERROR)


def main():
    log("==========Scraping started==========")
    start_time = time.time()
    try:
        check_versions()
        year, month = get_current()
        dest_dir = '../data'
        raw_dir = f'{dest_dir}/raw_syllabus_data_{year}_{month}.csv'
        out_dir = f'{dest_dir}/syllabus_data_{year}_{month}.csv'

        os.makedirs(dest_dir, exist_ok=True)

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--verbose")

        driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=chrome_options
        )
    except Exception as e:
        log(f"Error : {e}", ERROR)

    try:
        scrape_syllabus_data(driver, raw_dir)
    finally:
        driver.quit()

    format_syllabus_data(raw_dir, out_dir)
    log(f'Total Execution Time {time.time() - start_time:.6f} seconds')
    log("==========Scraping completed==========")

if __name__ == "__main__":
    main()
