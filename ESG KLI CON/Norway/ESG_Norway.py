import requests
import os
import re
from bs4 import BeautifulSoup
import pandas as pd
import time
import urllib.parse
from datetime import datetime
from deep_translator import GoogleTranslator

def get_soup(url, retries=10, delay=3):
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            else:
                print(f"⚠️ Attempt {attempt}: Received status code {response.status_code}")

            if attempt == retries:
                error_list.append(f"⚠️ Failed to retrieve page: {url} [status code: {response.status_code}]")

            if attempt < retries:
                print(f"🔁 Retrying after {delay} seconds...")
                time.sleep(delay)
        except requests.exceptions.RequestException as error:
            if attempt == retries:
                error_list.append(f"⚠️ Request error while accessing {url}: {error}")

            if attempt < retries:
                print(f"🔁 Retrying after {delay} seconds...")
                time.sleep(delay)

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Priority": "u=0, i",
    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\"",
    "Sec-Ch-Ua-Arch": "\"x86\"",
    "Sec-Ch-Ua-Bitness": "\"64\"",
    "Sec-Ch-Ua-Full-Version": "\"126.0.6478.127\"",
    "Sec-Ch-Ua-Full-Version-List": "\"Not/A)Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"126.0.6478.127\", \"Google Chrome\";v=\"126.0.6478.127\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Model": "\"\"",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Ch-Ua-Platform-Version": "\"15.0.0\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

excluded_list = [
    "endring",
    "å endre",
    "bevilgning",
    "budsjett",
    "opphevet",
    "flyplassen",
    "flyselskap",
    "ansettelse",
    "utnevnt",
    "pasient",
    "coronavirus",
    "COVID-19",
    "delegering"
]

law_count = 1

results = []
error_list = []
completed_list =[]
completed_sources = []
out_excel_file = os.path.join(os.getcwd(), "Norway.xlsx")

try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().strip().splitlines()
except Exception as error:
    error_list.append(str(error))

def process_page_content(content,link):
    page_count = 0
    key_word = re.search(r'q="([^"]+)"', link).group(1)
    site_word = re.search(r'filter=(\w+)', link).group(1)
    while True:
        page_url = f'https://lovdata.no/sok?filter={site_word}&offset={page_count}&q="{key_word}"'
        page_content = get_soup(page_url)
        check_value = page_content.find("div",class_="item globalSearchResult")
        if not check_value:
            break
        process_all_laws(page_content)
        page_count += 20

def process_all_laws(page_content):
    global law_count
    base_url = "https://lovdata.no"
    all_law = page_content.find_all("div", class_="item globalSearchResult")
    for sin in all_law:
        try:
            last_link_tag = sin.find("a")
            last_link = base_url + last_link_tag["href"]
            last_soup = get_soup(last_link)

            source_link = last_link.split("?q")[0]

            title_tag = last_soup.find("td",class_="metaTitleText").find("h1")
            title = title_tag.get_text(strip=True)

            english_title = get_english_text(title)

            reg_type , reg_check = check_law_or_regulation(title)

            excluded_check = is_valid_title(title)

            adoption_date, entry_date = get_dates(last_soup)

            entry = {
                "Jurisdiction": "Norway",
                "Original Title": title,
                "English Translation": english_title,
                "Type of Regulation": reg_type,
                "Source": source_link,
                "Date of adoption": adoption_date,
                "Entry Into Force Date": entry_date,

            }
            if (excluded_check and reg_check and entry["Source"] not in completed_sources and entry["Original Title"] not in completed_list):
                results.append(entry)
                completed_list.append(entry["Original Title"])
                completed_sources.append(entry["Source"])

                print(f"""✅ {law_count}.
      Jurisdiction          : {entry['Jurisdiction']}
      Original Title        : {entry['Original Title']}
      English Translation   : {entry['English Translation']}
      Type of Regulation    : {entry['Type of Regulation']}
      Source                : {entry['Source']}
      Date of Adoption      : {entry['Date of adoption']}
      Entry Into Force Date : {entry['Entry Into Force Date']}
                """)
                law_count += 1

        except Exception as error:
            error_list.append(str(error))

def get_dates(last_soup):
    if last_soup.find("th", string=["Date", "Dato"]):
        doa_tag = last_soup.find("th", string=["Date", "Dato"]).find_next_sibling("td")
        pre_doa = doa_tag.get_text(strip=True)
        match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", pre_doa)
        if match:
            adoption_date = match.group(1)
        else:
            adoption_date = ""
    else:
        adoption_date = ""

    if last_soup.find("th", string=["Entry into force", "Ikrafttredelse"]):
        eif_tag = last_soup.find("th", string=["Entry into force", "Ikrafttredelse"]).find_next_sibling("td")
        pre_eif = eif_tag.get_text(strip=True)
        match = re.search(r'\b(\d{2})\.(\d{2})\.(\d{4})\b', pre_eif)
        if match:
            day, month, year = match.groups()
            entry_date = f"{year}-{month}-{day}"
        else:
            entry_date = ""

    else:
        entry_date = ""

    return adoption_date, entry_date

def is_valid_title(title):
    title_lower = title.lower()
    return not any(word.lower() in title_lower for word in excluded_list)

def get_english_text(text):
    translated_text = GoogleTranslator(source='no', target='en').translate(text)
    return translated_text

def check_law_or_regulation(text):
    text_lower = text.lower()

    if "law" in text_lower:
        return "Law",True
    elif "regulation" in text_lower:
        return "Regulation",True
    elif re.search(r'lov', text, re.IGNORECASE):
        return "Law",True
    elif re.search(r'forskrift', text, re.IGNORECASE):
        return "Regulation",True
    else:
        return None,False

def main():
    for sin_key in keyword_list:
        try:
            nor_key,eng_key = sin_key.split(",")

            nor_key_link = [f'https://lovdata.no/sok?q="{nor_key}"&filter=SENTRALEFORSKRIFTER',
                            f'https://lovdata.no/sok?q="{nor_key}"&filter=SFE',
                            f'https://lovdata.no/sok?q="{nor_key}"&filter=NLE',
                            f'https://lovdata.no/sok?q="{nor_key}"&filter=LOVER']

            eng_key_link = [f'https://lovdata.no/sok?q="{eng_key}"&filter=SENTRALEFORSKRIFTER',
                            f'https://lovdata.no/sok?q="{eng_key}"&filter=SFE',
                            f'https://lovdata.no/sok?q="{eng_key}"&filter=NLE',
                            f'https://lovdata.no/sok?q="{eng_key}"&filter=LOVER']

            for nor_link,eng_link in zip(nor_key_link,eng_key_link):
                for link in [nor_link, eng_link]:
                    page_content = get_soup(link)
                    page_count_tag = page_content.find("span",class_="meta red moveright").get_text(strip=True)
                    law_count_text = re.search(r"documents\s*(\d+)",page_count_tag).group(1)
                    law_count = int(law_count_text)
                    if law_count != 0:
                        process_page_content(page_content,link)
                        break

        except Exception as error:
            error_list.append(str(error))

    df = pd.DataFrame(results)
    df.to_excel(out_excel_file, index=False)

if __name__ == "__main__":
    main()