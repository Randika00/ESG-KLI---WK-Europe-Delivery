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
import base64
results = []
error_list = []
completed_list =[]
completed_sources = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Origin": "https://search.et.gr",
    "Referer": "https://search.et.gr/"
}

out_excel_file = os.path.join(os.getcwd(), "Greece.xlsx")

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

# regulation_translation_map_pl = {
#     "ustawa": "Act",
#     "rozporządzenie": "Ordinance",
#     "zarządzenie": "Ordinance",
#     "umowa międzynarodowa": "International Agreement",
#     "uchwała": "Resolution",
#     "decyzja": "Decision",
#     "dekret": "Decree"
# }
#
# MONTHS_PL = {
#     "stycznia": "01",
#     "lutego": "02",
#     "marca": "03",
#     "kwietnia": "04",
#     "maja": "05",
#     "czerwca": "06",
#     "lipca": "07",
#     "sierpnia": "08",
#     "września": "09",
#     "października": "10",
#     "listopada": "11",
#     "grudnia": "12"
# }
# allowed_regulation_types = {
#     "Act",
#     "Ordinance",
#     "International Agreement",
#     "Resolution",
#     "Decision",
#     "Decree"
# }
non_esg_keywords = [
    "οικειοποίηση",      # appropriation
    "προϋπολογισμός",    # budget
    "καταργήθηκε",       # repealed
    "ανακλήθηκε",        # revoked
    "αεροδρόμιο",        # airport
    "αερογραμμή",        # airline
    "καθορισμένος",      # appointed
    "κορωνοϊός",         # coronavirus / COVID-19
]


def get_english_text(text):
    translated_text = GoogleTranslator(source='el', target='en').translate(text)
    return translated_text


def get_page_content(key_word):
    url = "https://searchetv99.azurewebsites.net/api/search"

    payload = {
        "advancedSearch": f"\"{key_word}\"",
        "selectYear": [],
        "selectIssue": [],
        "documentNumber": "",
        "entity": [],
        "categoryIds": [],
        "datePublished": "",
        "dateReleased": "",
        "legislationCatalogues": "",
        "selectedEntitiesSearchHistory": [],
        "tags": []
    }
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        raw_data = data["data"]
        parsed_data = json.loads(raw_data)

        for idx, record in enumerate(parsed_data, start=1):
            print(f"--- Record {idx} ---")

            # Extract specific fields into variables
            date_of_adoption = record.get("search_IssueDate")  # Date of Adoption
            try:
                # Parse the original date string
                adoption_date_dt = datetime.strptime(date_of_adoption, "%m/%d/%Y %H:%M:%S")
                adoption_date_formatted = adoption_date_dt.strftime("%Y-%m-%d")
            except Exception as e:
                print(f"Failed to parse date: {e}")
                adoption_date_formatted = None


            enforce_date = record.get("search_PublicationDate")
            try:
                # Parse the original date string
                enforce_date_dt = datetime.strptime(enforce_date, "%m/%d/%Y %H:%M:%S")
                enforce_date_formatted = enforce_date_dt.strftime("%Y-%m-%d")
            except Exception as e:
                print(f"Failed to parse date: {e}")
                enforce_date_formatted = None


            document_number = record.get("search_DocumentNumber")
            issue_group_id = record.get("search_IssueGroupID")
            primary_label = record.get("search_PrimaryLabel")
            pages = record.get("search_Pages")
            score = record.get("search_Score")

            try:
                # Convert strings to integers
                issue_group_id_int = int(issue_group_id)
                document_number_int = int(document_number)
                issue_date = datetime.strptime(date_of_adoption, "%m/%d/%Y %H:%M:%S")
                year = issue_date.year
                pdf_link = f"https://ia37rg02wpsa01.blob.core.windows.net/fek/{issue_group_id_int:02d}/{year}/{year}{issue_group_id_int:02d}{document_number_int:05d}.pdf"
            except Exception as e:
                pdf_link = None
                print(f"Failed to generate PDF link: {e}")


            # Decode the title from search_MatchedText
            title = None
            if "search_MatchedText" in record:
                encoded_text = record["search_MatchedText"]
                try:
                    decoded_bytes = base64.b64decode(encoded_text)
                    title = decoded_bytes.decode("utf-8", errors="ignore")
                except Exception as e:
                    print(f"Failed to decode search_MatchedText: {e}")

            # Print to check
            # print("Date of Adoption:", date_of_adoption)
            # print("Enforcement Date:", enforce_date)
            # print("Title:", title)
            # print("Document Number:", document_number)
            # print("Issue Group ID:", issue_group_id)
            print("Primary Label:", primary_label)
            # print("Pages:", pages)
            # print("Score:", score)

            # Prepare row data with English translation
            row_data = {
                "Jurisdiction": "Greece",
                "Original Title": title,
                "English Translation": get_english_text(title) if title else None,
                "Type of Regulation": "Law",
                "Source": pdf_link,
                "Date of adoption": adoption_date_formatted,
                "Entry Into Force Date": enforce_date_formatted
            }
            # print(row_data)
            # print("-" * 60)
            title_lower = title.lower()
            if (title not in completed_list
                    and pdf_link not in completed_sources
                    and not any(keyword in title_lower for keyword in
                                non_esg_keywords) ):
                results.append(row_data)
                print(row_data)
                print("-" * 60)
                completed_list.append(title)
                completed_sources.append(pdf_link)
            else:
                print("the duplicate data or ESg exculded data have this link :", pdf_link, '\n')


    else:
        print("Request failed:", response.status_code)


def main():
    for key_word in keyword_list:
        try:
            print(key_word)
            get_page_content(key_word)
            # df = pd.DataFrame(results)
            # df.to_excel(out_excel_file, index=False)
        except Exception as error:
            error_list.append(str(error))

if __name__ == "__main__":
    main()
