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

out_excel_file = os.path.join(os.getcwd(), "Hungary.xlsx")
non_esg_keywords = [
    "módosítás",      # amendment / amending
    "előirányzat",    # appropriation
    "költségvetés",   # budget
    "visszavonás",    # repealed
    "visszavon",      # revoked
    "repülőtér",      # airport
    "légitársaság",   # airline
    "kinevezés",      # appointment
    "kijelölt",       # appointed
    "beteg",          # patient
    "koronavírus",    # coronavirus
    "COVID-19"        # uppercase variant
]
regulation_translation_map_hu = {
    "törvény": "Law",
    "Korm. rendelet": "Decree",
    "törvényerejű rendelet": "Decree-Law",
    "Korm. határozat": "Resolution",
    "határozat": "Decision"
}
try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().strip().splitlines()
except Exception as error:
    error_list.append(str(error))

def get_english_text(text):
    translated_text = GoogleTranslator(source='hu', target='en').translate(text)
    return translated_text

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

def get_page_content(key_word):
    url = f"https://njt.hu/search/%22{key_word}%22:-:-:-:1:-:1:-:-:-:-/1/50"
    print(url)
    first_page_soup = get_soup(url)
    read_page_content(first_page_soup)

    last_page_tag = first_page_soup.find("a",class_="last")["href"]
    last_page_number = last_page_tag.rsplit("/",2)[-2]

    for page_num in range(2,int(last_page_number)+1):
        try:
            url = f"https://njt.hu/search/%22{key_word}%22:-:-:-:1:-:1:-:-:-:-/{page_num}/50"

            first_page_soup = get_soup(url)
            read_page_content(first_page_soup)
        except Exception as error:
            error_list.append(str(error))

def read_page_content(content):
    all_law_tag = content.find("div",attrs={"role":"region"})
    all_law = all_law_tag.find_all("div",class_="resultItemWrapper")

    for sin_law in all_law:
        try:
            # title = sin_law.find("a",attrs={"data-ng-click":True}).get_text()
            # print(sin_law)
            title1_tag = sin_law.find("a",attrs={"data-ng-click":True})
            title1 = title1_tag.get_text(strip=True) if title1_tag else ""
            # print(title)
            regulation_types = [
                "törvény",
                "Korm. rendelet",
                "törvényerejű rendelet",
                "Korm. határozat",
                "határozat"
            ]

            reg_type = None
            for hu_word, en_word in regulation_translation_map_hu.items():
                if hu_word in title1:
                    reg_type = en_word  # English translation
                    break  # take the first match

            if not reg_type:
                print("The regulation_type Not match", '\n')
                continue


            # Title2 → description
            title2_tag = sin_law.find("p")
            title2 = title2_tag.get_text(strip=True) if title2_tag else ""
            title = f"{title1} {title2}"

            # Source → href of firstResult
            link = title1_tag["href"] if title1_tag and title1_tag.has_attr("href") else ""
            if link:
                source =f"https://njt.hu/{link}"
            else:
                source = None


            # Entry force date → span.resultDate
            # date_tag = sin_law.find("span", class_="resultDate")
            # entry_date = date_tag.get_text(strip=True).replace("–", "").strip() if date_tag else ""
            date_tag = sin_law.find("span", class_="resultDate")
            entry_date = ""
            if date_tag:
                raw_date = date_tag.get_text(strip=True).replace("–", "").strip().rstrip(".")
                try:
                    entry_date = datetime.strptime(raw_date, "%Y. %m. %d").strftime("%Y-%m-%d")
                except ValueError:
                    entry_date = raw_date  # fallback if parsing fails


            # Build row_data
            row_data = {
                "Jurisdiction": "Hungary",
                "Original Title": title,
                "English Translation": get_english_text(title),
                "Type of Regulation": reg_type,
                "Source": source,
                "Date of adoption": entry_date,  # not in snippet
                "Entry Into Force Date": entry_date
            }
            title_lower = title.lower()
            if (title not in completed_list
                    and source not in completed_sources
                    and not any(keyword in title_lower for keyword in
                                non_esg_keywords)):
                results.append(row_data)
                print(row_data, '\n')
                completed_list.append(title)
                completed_sources.append(source)
            else:
                print("the duplicate data or ESg exculded data have this link :", source, '\n')
        except Exception as error:
            error_list.append(str(error))

def main():
    for key_word in keyword_list:
        try:
            print(f"\nSearching for: [{key_word}]")
            get_page_content(key_word)
            df = pd.DataFrame(results)
            df.to_excel(out_excel_file, index=False)
        except Exception as error:
            error_list.append(str(error))

if __name__ == "__main__":
    main()