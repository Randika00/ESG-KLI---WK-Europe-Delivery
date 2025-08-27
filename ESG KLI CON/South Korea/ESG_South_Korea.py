import requests
import os
import re
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from urllib.parse import quote_plus
import urllib.parse
from datetime import datetime
from deep_translator import GoogleTranslator

results = []
error_list = []
completed_list =[]
completed_sources = []

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
}
non_esg_keywords = [
    "개정",     # amendment
    "인가",     # appropriation
    "예산",     # budget
    "폐지됨",   # repealed
    "취소됨",   # revoked
    "공항",     # airport
    "공기 호스", # airline
    "약속",     # appointment
    "정해진",   # appointed
]

regulation_translation_map_ko = {
    "법률": "Law",
    "대통령령": "Decree",
    "환경부령": "Ordinance",
    "해양수산부령": "Ordinance",
    "과학기술정보통신부령": "Ordinance",
    "대법원규칙": "Rules"
}

allowed_regulation_types = {
    "Law",
    "Decree",
    "Ordinance",
    "Ordinance",
    "Ordinance",
    "Rules"
}
out_excel_file = os.path.join(os.getcwd(), "South_Korea.xlsx")

try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().strip().splitlines()
except Exception as error:
    error_list.append(str(error))

def get_soup_with_post(url, payload,retries=10, delay=3):
    for attempt in range(1, retries + 1):
        try:

            response = requests.post(url, data=payload, headers=headers)

            if response.status_code == 200:

                return BeautifulSoup(response.content, 'html.parser')
            else:
                print(f"⚠️ Attempt {attempt}: Received status code {response.status_code}")

            if attempt == retries:
                raise Exception(f"⚠️ Failed to retrieve page: {url} [status code: {response.status_code}]")

            if attempt < retries:
                print(f"🔁 Retrying after {delay} seconds...")
                time.sleep(delay)
        except requests.exceptions.RequestException as error:
            if attempt == retries:
                raise Exception(f"⚠️ Request error while accessing {url}: {error}")

            if attempt < retries:
                print(f"🔁 Retrying after {delay} seconds...")
                time.sleep(delay)

def get_page_content(key_word):
    url = 'https://www.law.go.kr/lsScListR.do?menuId=1&subMenuId=15&tabMenuId=81'

    page_number = 1
    while True:
        payload = {
            "q": f"{key_word}",
            "outmax": "150",
            "p18": "0",
            "p19": "1,3",
            "pg": f"{page_number}",
            "fsort": "10,41,21,31",
            "lsType": "null",
            "section": "lawNm",
            "lsiSeq": "0",
            "p9": "2,4"
        }

        main_content = get_soup_with_post(url, payload)
        table_content = main_content.find("table").tbody
        all_legi = table_content.find_all("tr")

        read_all_legislation_content(all_legi)

        page_number += 1

        if len(all_legi) < 150:
            break

def convert_korean_date_to_iso(date_str):

    try:
        # Clean up the string
        date_str = date_str.strip().rstrip('.')
        # Convert to datetime object
        date_obj = datetime.strptime(date_str, '%Y. %m. %d')
        # Return formatted date
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        return None  # or raise error / return original

def get_english_text(text):
    translated_text = GoogleTranslator(source='ko', target='en').translate(text)
    return translated_text

def read_all_legislation_content(legi_content):
    all_law = legi_content

    for sin_law in all_law:
        try:
            metadata = sin_law.find_all("td")
            first_tag = metadata[1].find("a")
            title = first_tag.get_text()
            adop_date = metadata[2].get_text()
            adoption_date = convert_korean_date_to_iso(adop_date)
            reg_type = metadata[3].get_text()
            mapped_reg_type = regulation_translation_map_ko.get(reg_type, reg_type)
            a_src = first_tag["onclick"]

            match = re.search(r"lsViewWideAll\('(\d+)',\s*'(\d+)'", a_src)
            if match:
                number1 = match.group(1)
                number2 = match.group(2)
                source_link = f"https://www.law.go.kr/lsInfoP.do?lsiSeq={number1}&efYd={number2}"

                entry_date = get_entry_date(number1,number2)
                entry_into_force = convert_korean_date_to_iso(entry_date)




            row_data = {
                "Jurisdiction": "South Korea",
                "Original Title": title,
                "English Translation": get_english_text(title),
                "Type of Regulation": mapped_reg_type,
                "Source": source_link,
                "Date of adoption": adoption_date,
                "Entry Into Force Date": entry_into_force
            }


            title_lower = title.lower()
            if (title not in completed_list
                    and source_link not in completed_sources
                    and not any(keyword in title_lower for keyword in non_esg_keywords)
                    and mapped_reg_type in allowed_regulation_types):

                results.append(row_data)
                print(row_data)
                completed_list.append(title)
                completed_sources.append(source_link)
            else:
                print("the duplicate data or ESg exculded data have this link :", source_link, '\n')

        except Exception as error:
            error_list.append(str(error))



def get_entry_date(number1,number2):
    url = 'https://www.law.go.kr/lsInfoR.do'

    payload = {
        "lsiSeq": f"{number1}",
        "efYd": f"{number2}",
    }

    soup = get_soup_with_post(url, payload)
    entry_date = soup.find("div", class_="ct_sub")

    text = entry_date.find('span').get_text(strip=True)


    match = re.search(r'시행\s+(\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.)', text)
    if match:
        entry_force_date = match.group(1).strip()

    else:
        entry_force_date=""

    return entry_force_date



def main():
    for key_word in keyword_list:
        try:
            print(key_word)
            get_page_content(key_word)
            df = pd.DataFrame(results)
            df.to_excel(out_excel_file, index=False)
        except Exception as error:
            error_list.append(str(error))

if __name__ == "__main__":
    main()