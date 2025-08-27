import os.path
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re
from urllib.parse import urljoin
from deep_translator import GoogleTranslator

def format_date(date_str):
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
    except:
        return ""

word_list = {"Protokoll": "Protocol", "Regeln": "Regulation", "Verordnung": "Ordinance", "Übereinkommen": "Convention", "Gesetz": "Law"}
allowed_types = list(word_list.keys())

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

all_results = []

for keyword in keywords:
    print(f"Processing keyword: {keyword}")
    try:
        data = {
            'config': 'Titel_bmjhome2005',
            'method': 'and',
            'words': keyword,
            'suche': 'Suchen'
        }

        response = session.post(search_url, data=data, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        strong_tags = soup.find_all('strong')

        result_urls = []
        for strong in strong_tags:
            links = strong.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    result_urls.append(full_url)

        if not result_urls:
            print(f"No results found for keyword: {keyword}")
            continue

        for url in result_urls:
            print(f"Processing URL: {url}")
            try:
                res_page = session.get(url, headers=headers)
                res_page.raise_for_status()
                soup_page = BeautifulSoup(res_page.text, 'lxml')

                html_link_tag = soup_page.find('a', string='HTML')
                if not html_link_tag or not html_link_tag.get('href'):
                    print(f"No HTML version link found for {url}")
                    continue

                html_relative_url = html_link_tag['href']
                full_html_url = urljoin(url, html_relative_url)

                html_response = session.get(full_html_url, headers=headers)
                html_response.raise_for_status()
                html_soup = BeautifulSoup(html_response.text, 'lxml')

                h1_tag = html_soup.find('h1')
                if h1_tag:
                    span = h1_tag.find('span', class_='jnlangue')
                    title = span.text.strip() if span else h1_tag.text.strip()
                else:
                    title = ''

                reg_type = ''
                if title:
                    for t in allowed_types:
                        if t in title:
                            reg_type = t
                            break

                    if not reg_type:
                        print(f"Skipping '{title}' (not an allowed regulation type).")
                        continue

                reg_type_english = word_list.get(reg_type, reg_type)

                date_of_adoption = ''
                match_adopt = re.search(r'Ausfertigungsdatum:\s*(\d{2}\.\d{2}\.\d{4})', html_response.text)
                if match_adopt:
                    date_of_adoption = format_date(match_adopt.group(1))
                else:
                    date_of_adoption = ""

                entry_force_date = ''
                match_force = re.search(r'mWv\s*(\d{2}\.\d{2}\.\d{4})', html_response.text)
                if match_force:
                    entry_force_date = format_date(match_force.group(1))
                else:
                    entry_force_date = ""

                translated_title = GoogleTranslator(source='de', target='en').translate(title)
                time.sleep(1)

                metadata = {
                    'Jurisdiction': 'Germany',
                    'Original Title': title,
                    "English Translation": translated_title,
                    'Type of Regulation': reg_type_english,
                    'Source': full_html_url,
                    'Date of Adoption': date_of_adoption,
                    'Entry into Force Date': entry_force_date,
                }

                all_results.append(metadata)
                print(metadata)
                time.sleep(1)

            except Exception as e:
                print(f"Error processing URL {url}: {str(e)}")

    except Exception as e:
        print(f"Error processing keyword '{keyword}': {str(e)}")

df = pd.DataFrame(all_results)
df.to_excel(out_excel_file, index=False)

print(f"Scraping completed with results.")
