import os.path
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import time
import urllib.parse
from datetime import datetime
import re
from urllib.parse import quote_plus
from urllib.parse import urljoin
from lxml.doctestcompare import strip
from deep_translator import GoogleTranslator


def format_date(date_str):
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
    except:
        return ""

word_list = {
    "Protokoll": "Protocol",
    "Regeln": "Regulation",
    "Verordnung": "Ordinance",
    "Übereinkommen": "Convention",
    "Gesetz": "Law"
}
allowed_types = list(word_list.keys())

article_div = "https://www.recht.bund.de/"

def date_append_list(soup):
    div_element = soup.find("section", class_="searchresult").find_all("div", class_="large-11 large-offset-1 small-12 columns")
    for single_element in div_element:
        article_link, article_title = None, None
        try:
            article_title_div = single_element.find("a")
            if article_title_div:
                article_title = article_title_div.find("strong").text.strip()
                article_links = article_title_div.get('href')
                article_link = urllib.parse.urljoin(article_div, article_links)

                reg_type = ''
                if article_title:
                    for t in allowed_types:
                        if t in article_title:
                            reg_type = t

                    if not reg_type:
                        print(f"Skipping '{article_title}' (not an allowed regulation type).")
                        continue

                reg_type_english = word_list.get(reg_type, reg_type)

                date_tag = single_element.find("h3")
                entry_force_date = ""
                if date_tag:
                    date_text = date_tag.get_text(strip=True)
                    dates = re.findall(r"\d{2}\.\d{2}\.\d{4}", date_text)
                    if dates:
                        entry_force_date = format_date(dates[-1])
                    else:
                        entry_force_date = ""

                day_tag = single_element.find("div", class_="publishDate").find("p")
                date_of_adoption = ""
                if day_tag:
                    day_text = day_tag.get_text(strip=True)
                    match_adopt = re.search(r'Ausfertigungsdatum:\s*(\d{2}\.\d{2}\.\d{4})', day_text)
                    if match_adopt:
                        date_of_adoption = format_date(match_adopt.group(1))
                    else:
                        date_of_adoption = ""

                translated_title = GoogleTranslator(source='de', target='en').translate(article_title)
                time.sleep(1)

                entry = {
                    "Jurisdiction": "Germany",
                    "Original Title": article_title,
                    "English Translation": translated_title,
                    "Type of Regulation": reg_type_english,
                    "Source Link": article_link,
                    "Date of adoption": date_of_adoption,
                    "Entry Into Force Date": entry_force_date,
                }

                if (entry["Source Link"] not in completed_sources and entry["Original Title"] not in completed_list):
                    result_list.append(entry)
                    completed_list.append(entry["Original Title"])
                    completed_sources.append(entry["Source Link"])
                    print(entry)

        except Exception as error:
            message = f"Error link - {article_title}: {str(error)}"
            print(f"{article_title}: {str(error)}")
            error_list.append(message)

result_list = []
error_list = []
duplicate_list = []
completed_list = []
completed_sources = []

base_url = "https://www.gesetze-im-internet.de/"
search_url = "https://www.gesetze-im-internet.de/cgi-bin/htsearch"
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.6',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.gesetze-im-internet.de',
    'Referer': 'https://www.gesetze-im-internet.de/titelsuche.html'
}
session = requests.Session()

out_excel_file = os.path.join(os.getcwd(), "Germany.xlsx")

with open('keywords.txt', 'r', encoding='utf-8') as file:
    keywords = [line.strip() for line in file if line.strip()]

for keyword in keywords:
    print(f"Processing keyword: {keyword}")
    try:
        encoded_url_value = quote_plus(keyword)
        encoded_link = f"https://www.recht.bund.de/SiteGlobals/Forms/Suche/Expertensuche_Formular.html?resourceId=54356&input_=54330&pageLocale=de&templateQueryString={encoded_url_value}&submit=Suchen&lastChangeVdAfter=&lastChangeVdBefore=&lastChangeAdAfter=&lastChangeAdBefore=&bgblnr=&fnanr=&gestanr=&federfuehrung=&federfuehrung.GROUP=1"

        response = session.get(encoded_link, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        if soup.find("nav", class_="navIndex"):
            id_value = soup.find("nav", class_="navIndex").find_all("li")[-2]
            if id_value:
                id_tag = id_value.get_text(strip=True).split("Seite")[-1]

                for id in range(int(id_tag)):
                    try:
                        page_link = f"https://www.recht.bund.de/SiteGlobals/Forms/Suche/Expertensuche_Formular.html?input_=54330&gtp=54300_list%253D{id}&submit=Suchen&resourceId=54356&templateQueryString={encoded_url_value}&federfuehrung.GROUP=1&pageLocale=de"
                        response = session.get(page_link, headers=headers)
                        soup = BeautifulSoup(response.content, 'html.parser')
                        date_append_list(soup)

                    except Exception as e:
                        print(f"Error processing keyword '{keyword}': {str(e)}")

        else:
            response = session.get(encoded_link, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            date_append_list(soup)

    except Exception as e:
        print(f"Error processing keyword '{keyword}': {str(e)}")

df = pd.DataFrame(result_list)
df.to_excel(out_excel_file, index=False)

print(f"Scraping completed with all results.")
