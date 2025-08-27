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

out_excel_file = os.path.join(os.getcwd(), "Poland.xlsx")

try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().strip().splitlines()
except Exception as error:
    error_list.append(str(error))

def get_soup(url, retries=10, delay=3):
    for attempt in range(1, retries + 1):
        try:

            response = requests.get(url, headers=headers)

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

regulation_translation_map_pl = {
    "ustawa": "Act",
    "rozporządzenie": "Ordinance",
    "zarządzenie": "Ordinance",
    "umowa międzynarodowa": "International Agreement",
    "uchwała": "Resolution",
    "decyzja": "Decision",
    "dekret": "Decree"
}

MONTHS_PL = {
    "stycznia": "01",
    "lutego": "02",
    "marca": "03",
    "kwietnia": "04",
    "maja": "05",
    "czerwca": "06",
    "lipca": "07",
    "sierpnia": "08",
    "września": "09",
    "października": "10",
    "listopada": "11",
    "grudnia": "12"
}
allowed_regulation_types = {
    "Act",
    "Ordinance",
    "International Agreement",
    "Resolution",
    "Decision",
    "Decree"
}
non_esg_keywords = [
    "poprawka",      # amendment
    "asygnowanie",   # appropriation
    "uchylony",      # repealed
    "odwołany"       # revoked
]
def extract_entry_force_date(table):
    rows = table.find_all("tr")

    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)

            if label.startswith("Data ogłoszenia"):
                if value.lower() == "brak":
                    return ""
                else:
                    return value  # already in YYYY-MM-DD format
    return ""  # fallback if not found


def get_english_text(text):
    translated_text = GoogleTranslator(source='pl', target='en').translate(text)
    return translated_text

def extract_table_data(table):
    rows = table.find_all("tr")[1:]  # skip header row


    for row in rows:
        cols = row.find_all("td")
        if len(cols) != 3:
            continue

        type_akt = cols[0].get_text(strip=True)
        type_akt_clean = type_akt.lower()
        Type_of_regulation = regulation_translation_map_pl.get(type_akt_clean, type_akt)
        title_tag = cols[1].find("a")
        title = title_tag.get_text(strip=True)
        title_link = title_tag['href']
        title_url = f"https://www.dziennikustaw.gov.pl{title_link}"
        a_soup = get_soup(title_url)
        a_table = a_soup.find("table", style="clear: both;")

        entry_force_date = extract_entry_force_date(a_table)


        file_tag = cols[2].find("a")
        file_link = file_tag['href'] if file_tag else ""
        pdf_link = f"https://www.dziennikustaw.gov.pl{file_link}"

        # Extract and format date
        match = re.search(r"z dnia (\d{1,2}) (\w+) (\d{4})", title)
        if match:
            day, month_pl, year = match.groups()
            month = MONTHS_PL.get(month_pl.lower())
            if month:
                adoption_date = f"{year}-{month}-{int(day):02d}"
            else:
                adoption_date = ""
        else:
            adoption_date = ""

        row_data = {
            "Jurisdiction":"Poland",
            "Original Title": title,
            "English Translation": get_english_text(title),
            "Type of Regulation": Type_of_regulation,
            # "Tytuł Link": title_link,
            "Source": pdf_link,
            "Date of adoption": adoption_date,
            "Entry Into Force Date":entry_force_date
        }

        title_lower = title.lower()
        if (title not in completed_list
                and pdf_link not in completed_sources
                and not any(keyword in title_lower for keyword in
                            non_esg_keywords) and Type_of_regulation in allowed_regulation_types
        ):
            results.append(row_data)
            print(row_data)
            completed_list.append(title)
            completed_sources.append(pdf_link)
        else:
            print("the duplicate data or ESg exculded data have this link :", title_link, '\n')



    return results

def get_page_content(key_word):
    url = f"https://www.dziennikustaw.gov.pl/szukaj?pSize=0&pNumber=1&diary=0&typact=8&typact=20&typact=6&typact=15&typact=7&typact=22&typact=23&_typact=1&year=0&release=&number=&volume=&publicDateFrom=&publicDateTo=&releaseDateFrom=&releaseDateTo=&_group=1&_subject=1&title={key_word}&text=&sKey=year&sOrder=desc#list"
    # url ="https://www.dziennikustaw.gov.pl/szukaj?pSize=0&pNumber=1&diary=0&typact=23&typact=23&typact=22&typact=22&typact=12&typact=12&typact=14&typact=14&typact=7&typact=7&typact=8&typact=8&typact=15&typact=15&typact=6&typact=6&typact=20&typact=20&typact=11&typact=11&_typact=1&year=0&release=&number=&volume=&publicDateFrom=&publicDateTo=&releaseDateFrom=&releaseDateTo=&_group=1&_subject=1&title=zanieczyszczenie&text=&sKey=year&sOrder=desc#list"
    soup = get_soup(url)
    table = soup.find("table", class_="PapRedGrid", summary="Wyniki wyszukiwania")
    extract_table_data(table)


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