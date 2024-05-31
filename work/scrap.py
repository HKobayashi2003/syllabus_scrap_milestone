from selenium import webdriver
import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException
from mojimoji import zen_to_han
import pandas as pd

faculties = ['基幹','創造','先進','政経','法学','教育','商学','社学','人科','スポーツ','国際教養','文構','文','人通','芸術','日本語','留学','グローバル']

syllabus_data=[]

# Mac
driver = webdriver.Chrome()

#ファイルを開いて、項目名を作成
with open('syllabus_data.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['学部','コース名','開講学期','教員名','曜日時限'])

driver.get('https://www.wsl.waseda.jp/syllabus/JAA101.php')
for name in faculties:
    # 選択式のフォームを取得
    select = Select(driver.find_element(By.NAME, 'p_gakubu'))
     # オプションを選択（以下は3つの選択方法を示しています）
    select.select_by_visible_text(name)  # value属性で選択
    button = driver.find_element(By.NAME, 'btnSubmit')
    button.click()

    i=0

    while True:
        try:
            for i in range(10):
                #各要素ごとにデータを取得。各列ごとに格納。
                #科目名
                course_name_element = driver.find_element(By.XPATH, f'//*[@id="cCommon"]/div/div/div/div/div[1]/div[2]/table/tbody/tr[{i+2}]/td[3]/a')
                course_name = course_name_element.text

                #学期
                semester_name_element = driver.find_element(By.XPATH, f'//*[@id="cCommon"]/div/div/div/div/div[1]/div[2]/table/tbody/tr[{i+2}]/td[6]')
                semester_name = semester_name_element.text

                #教員名
                teacher_name_element = driver.find_element(By.XPATH, f'//*[@id="cCommon"]/div/div/div/div/div[1]/div[2]/table/tbody/tr[{i+2}]/td[4]')
                teacher_name = teacher_name_element.text

                #曜日時限
                week_element = driver.find_element(By.XPATH, f'//*[@id="cCommon"]/div/div/div/div/div[1]/div[2]/table/tbody/tr[{i+2}]/td[7]')
                week_name = week_element.text

                #読み込む
                syllabus_data.append([name,course_name,semester_name,teacher_name,week_name])

            #iの初期化
            i=0

            #次のページへ
            next_path = '//*[@id="cHonbun"]/div[2]/table/tbody/tr/td[3]/div/div/p/a'
            next_button = driver.find_element(By.XPATH, next_path)
            next_button.click()

        except NoSuchElementException:
            print("終了")
            break

    back = driver.find_element(By.CLASS_NAME, 'ch-back')
    back.click()

with open('syllabus_data.csv', 'a', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    for course_data in syllabus_data:
        writer.writerow(course_data)

driver.quit()

def count_csv_rows(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        row_count = sum(1 for row in reader)
    return row_count

file_path = 'syllabus_data.csv' 
row_count = count_csv_rows(file_path)
print("行数:", row_count)

converted_data = []

with open('syllabus_data.csv', 'r', newline='', encoding='utf-8') as file:
    csvreader = csv.reader(file)
    for row in csvreader:
        converted_row = [zen_to_han(cell,kana=False) for cell in row]
        converted_data.append(converted_row)

with open('converted_syllabus_data.csv', 'w', newline='', encoding='utf-8') as file:
    csvwriter = csv.writer(file)
    csvwriter.writerows(converted_data)

def process_schedule1(row: list):
    schedule = str(row[4])
    common_data = row[:4]
    expanded_rows = []

    if ":" in schedule:  # タイプ②の場合
        for time in schedule.split(":"):
            if len(time) < 4:
                continue
            time = time.replace("　", " ")
            time = time.replace("\n", " ")
            new_schedule = time.split(" ")[0]
            expanded_rows.append(list(common_data) + [new_schedule])
    else:  # 通常のスケジュールの場合
        expanded_rows.append(list(row))
    return expanded_rows


def process_schedule2(row: list):
    schedule = str(row[4])
    common_data = row[:4]
    expanded_rows = []
    if "-" in schedule:  # タイプ①の場合
        schedule = schedule.replace(" ", "")
        day, time_range = schedule[0], schedule[1:]
        start, end = map(int, time_range.split("-"))
        for time in range(start, end + 1):
            new_schedule = f"{day}{time}時限"
            expanded_rows.append(list(common_data) + [new_schedule])
    else:  # 通常のスケジュールの場合
        expanded_rows.append(list(row))
    return expanded_rows


def main():
    # CSVファイルを読み込む
    df = pd.read_csv("converted_syllabus_data.csv", header=None)

    # 新しいデータを保持する空のリストを作成
    new_data = []

    # 各行を処理
    for index, row in df.iterrows():
        if index < 3:
            continue
        new_rows = process_schedule1(row)
        new_data.extend(new_rows)

    new_data2 = []
    for row in new_data:
        new_rows = process_schedule2(row)
        new_data2.extend(new_rows)

    # 新しいDataFrameを作成
    new_df = pd.DataFrame(new_data2)

    # 新しいCSVファイルとして保存
    new_df.to_csv("syllabus_output.csv", index=False, header=False)


if __name__ == "__main__":
    main()