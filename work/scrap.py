import csv
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from mojimoji import zen_to_han
import subprocess
from logging import getLogger, handlers, Formatter, DEBUG, ERROR

faculties = ['基幹', '創造', '先進', '政経', '法学', '教育', '商学', '社学', '人科', 'スポーツ', '国際教養', '文構', '文', '人通', '芸術', '日本語', '留学', 'グローバル']


def set_logger():
    # 全体のログ設定
    # ファイルに書き出す。ログが100KB溜まったらバックアップにして新しいファイルを作る。
    root_logger = getLogger()
    root_logger.setLevel(DEBUG)
    rotating_handler = handlers.RotatingFileHandler(
        r'../app.log',
        mode="a",
        maxBytes=100 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    format = Formatter('%(asctime)s : %(levelname)s : %(message)s')
    rotating_handler.setFormatter(format)
    root_logger.addHandler(rotating_handler)

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

def get_current_term():
    now = datetime.datetime.now()
    year = now.year
    if now.month < 4:
        year -= 1
    term = 'spring' if 4 <= now.month <= 9 else 'autumn'
    return year, term

def init_csv_file(year, term):
    with open(f'../data/syllabus_data_{year}_{term}.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['学部', 'コース名', '開講学期', '教員名', '曜日時限'])

def scrape_syllabus_data(driver, dest):
    driver.get('https://www.wsl.waseda.jp/syllabus/JAA101.php')
    with open(dest, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for name in faculties:
            select = Select(driver.find_element(By.NAME, 'p_gakubu'))
            select.select_by_visible_text(name)
            driver.find_element(By.NAME, 'btnSubmit').click()
            log(f"Scraping {name} data.")

            while True:
                try:
                    for i in range(10):
                        course_name = driver.find_element(By.XPATH, f'//*[@id="cCommon"]/div/div/div/div/div[1]/div[2]/table/tbody/tr[{i+2}]/td[3]/a').text
                        semester_name = driver.find_element(By.XPATH, f'//*[@id="cCommon"]/div/div/div/div/div[1]/div[2]/table/tbody/tr[{i+2}]/td[6]').text
                        teacher_name = driver.find_element(By.XPATH, f'//*[@id="cCommon"]/div/div/div/div/div[1]/div[2]/table/tbody/tr[{i+2}]/td[4]').text
                        week_name = driver.find_element(By.XPATH, f'//*[@id="cCommon"]/div/div/div/div/div[1]/div[2]/table/tbody/tr[{i+2}]/td[7]').text

                        writer.writerow([name, course_name, semester_name, teacher_name, week_name])

                    driver.find_element(By.XPATH, '//*[@id="cHonbun"]/div[2]/table/tbody/tr/td[3]/div/div/p/a').click()
                except NoSuchElementException:
                    break

            driver.find_element(By.CLASS_NAME, 'ch-back').click()

def convert_zen_to_han(source_path, output_path):
    converted_data = []
    with open(source_path, 'r', newline='', encoding='utf-8') as file:
        csvreader = csv.reader(file)
        for row in csvreader:
            converted_row = [zen_to_han(cell, kana=False) for cell in row]
            converted_data.append(converted_row)
    with open(output_path, 'w', newline='', encoding='utf-8') as file:
        csvwriter = csv.writer(file)
        csvwriter.writerows(converted_data)

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
        for row in csvreader:
            try:
                han_row = [zen_to_han(cell, kana=False) for cell in row]
                fmt1 = process_schedule1(han_row)
                for sub_row in fmt1:
                    fmt2 = process_schedule2(sub_row)
                    for final_row in fmt2:
                        csvwriter.writerow(final_row)
            except Exception as e:
                log(e, level=ERROR)
                log(row, level=ERROR)

def main():
    log("==========Scraping started==========")
    check_versions()
    year, term = get_current_term()
    dest_dir = '../data'
    name = f'syllabus_data_{year}_{term}.csv'
    raw_dir = f'{dest_dir}/raw_{name}'
    out_dir = f'{dest_dir}/{name}'

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--verbose")

    chrome_service = Service('/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    try:
        scrape_syllabus_data(driver, raw_dir)
    finally:
        driver.quit()

    format_syllabus_data(raw_dir, out_dir)

    log("==========Scraping completed==========")

if __name__ == "__main__":
    main()
