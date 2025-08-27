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

out_excel_file = os.path.join(os.getcwd(), "Denmark.xlsx")

try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().strip().splitlines()
except Exception as error:
    error_list.append(str(error))

headers3 = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.retsinformation.dk",
    "Referer": "https://www.retsinformation.dk/eli/lta/2020/133",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}

data = {
    "isRawHtml": False
}
danish_months = {
    "januar": "01", "februar": "02", "marts": "03", "april": "04", "maj": "05", "juni": "06",
    "juli": "07", "august": "08", "september": "09", "oktober": "10", "november": "11", "december": "12"
}
regulation_translation_map = {
    "Lov": "Act",
    "Lovbekendtgørelse": "Consolidated Act",
    "Bekendtgørelse": "Executive Order",
    "Bekendtgørelse (international)": "Executive Order (International)",
    "Cirkulære": "Circular",
    "Vejledning": "Guidance"
}
non_esg_keywords = [
    "ændringsforslag",  # amendment
    "ændring",          # amending
    "at ændre",         # to amend/change
    "bevilling",        # appropriation
    "budget",           # budget
    "ophævet",          # repealed
    "ophævelse",        # repealing
    "tilbagekaldt",     # revoked
    "lufthavn",         # airport
    "flyselskab",       # airline
    "udnævnelse",       # appointment
    "udnævnt",          # appointed
    "patient",          # patient
    "coronavirus",      # coronavirus
    "COVID-19"          # covid-19
]
allowed_regulation_types = {
    "Act",
    "Consolidated Act",
    "Executive Order",
    "Executive Order (International)",
    "Circular",
    "Guidance"
}


def getSoup(url):
    response = requests.get(url,headers=headers3)
    return response



def get_english_text(text):
    translated_text = GoogleTranslator(source='da', target='en').translate(text)
    return translated_text



def get_soup(url, payload,retries=10, delay=3):
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                return response.json()
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



def get_page_content(key_word):
    low_list = ["SortIndicator_10","SortIndicator_30","SortIndicator_60","SortIndicator_220","SortIndicator_140","SortIndicator_150","SortIndicator_180"]

    for sin_low in low_list:
        page_count = 0
        print("🚫 Filter Word :", sin_low)
        while True:
            url = f"https://www.retsinformation.dk/api/extremesearch"
            payload = {
                "pageNumber": page_count,
                "pageSize": 100,
                "tree": {
                    "type": "group",
                    "id": "ab889989-0123-4456-b89a-b16f139daa93",
                    "children1": {
                        "b8b9b9a9-cdef-4012-b456-716f139daa93": {
                            "type": "rule",
                            "properties": {
                                "field": "retsinfoklassifikationId",
                                "operator": "select_equals",
                                "value": ["SortIndicator_10_40"],
                                "valueSrc": ["value"],
                                "valueType": ["select"]
                            },
                            "id": "b8b9b9a9-cdef-4012-b456-716f139daa93"
                        },
                        "aaba9aa8-cdef-4012-b456-716fc3780da3": {
                            "type": "rule",
                            "properties": {
                                "field": "titel",
                                "operator": "starts_with",
                                "value": [f"{key_word}"],
                                "valueSrc": ["value"],
                                "valueType": ["text"]
                            },
                            "id": "aaba9aa8-cdef-4012-b456-716fc3780da3"
                        },
                        "9bba98ba-cdef-4012-b456-716fc37a4f30": {
                            "type": "rule",
                            "properties": {
                                "field": "dokumentTypeId",
                                "operator": "select_equals",
                                "value": [f"{sin_low}"],
                                "valueSrc": ["value"],
                                "valueType": ["treeselect"]
                            },
                            "id": "9bba98ba-cdef-4012-b456-716fc37a4f30"
                        }
                    },
                    "properties": {
                        "conjunction": "AND"
                    }
                },
                "orderDirection": 20,
                "orderBy": 40
            }

            content = get_soup(url, payload)
            document = content["documents"]
            if not document:
                break
            page_count += 1
            read_json(document)


def read_json(json_data):
    print("📄 Count of legislation :", len(json_data))
    for sin in json_data:
        try:
            base_url = "https://www.retsinformation.dk"
            low_url = base_url+sin["retsinfoLink"]
            print("🔗 Legislation link :", low_url)

            url = low_url.replace("https://www.retsinformation.dk/", "https://www.retsinformation.dk/api/document/")
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                json_data = response.json()
                for item in json_data:
                    # Initialize variables
                    Jurisdiction = ""
                    Original_Title = ""
                    English_Translation = ""
                    Type_of_Regulation = ""
                    Date_of_adoption = ""
                    Entry_Into_Force_Date = ""

                    Original_Title = item.get("title", "")
                    document_html = item.get("documentHtml", "")
                    metadata = item.get("metadata", [])

                    # Extract metadata fields
                    for entry in metadata:
                        name = entry.get("displayName", "")
                        value = entry.get("displayValue", "")

                        if name == "Dokumenttype":
                            Type_of_Regulation = value

                        elif name == "Dato for underskrift":
                            try:
                                date_obj = datetime.strptime(value, "%d/%m/%Y")
                                Date_of_adoption = date_obj.strftime("%Y-%m-%d")
                            except ValueError:
                                Date_of_adoption = value  # fallback raw

                    # Extract Entry Into Force Date from document_html
                    soup = BeautifulSoup(document_html, "html.parser")

                    # Get full text from soup
                    full_text = soup.get_text(separator=" ", strip=True)
                    keywords = ["Ikrafttræden", "Ikrafttrædelse"]

                    for keyword in keywords:
                        match = re.search(rf"\b{keyword}\b", full_text, flags=re.IGNORECASE)
                        if match:
                            start = match.end()
                            after_keyword_text = full_text[start:]
                            words = after_keyword_text.strip().split()
                            next_30_words = " ".join(words[:30])
                            # print(f"🔍 Found keyword: {keyword}")
                            # print("Next 30 words:", next_30_words)

                            # Search for Danish-style date like '7. juni 2000'
                            date_match = re.search(
                                r"\b(\d{1,2})\.?\s+(januar|februar|marts|april|maj|juni|juli|august|september|oktober|november|december)\s+(\d{4})\b",
                                next_30_words, re.IGNORECASE)
                            if date_match:
                                day = int(date_match.group(1))
                                month_text = date_match.group(2).lower()
                                year = int(date_match.group(3))

                                month = danish_months.get(month_text)
                                if month:
                                    Entry_Into_Force_Date = f"{year:04d}-{month}-{day:02d}"

                            break  # Only process the first found keyword

                    Type_of_Regulation = regulation_translation_map.get(Type_of_Regulation, Type_of_Regulation)
                    row = {
                        "Jurisdiction": "Denmark",
                        "Original Title": Original_Title,
                        "English Translation": get_english_text(Original_Title),
                        "Type of Regulation": Type_of_Regulation,
                        "Source": low_url,
                        "Date of adoption": Date_of_adoption,
                        "Entry Into Force Date": Entry_Into_Force_Date
                    }
                    title_lower = Original_Title.lower()
                    if (Original_Title not in completed_list
                            and low_url not in completed_sources
                            and not any(keyword in title_lower for keyword in
                                        non_esg_keywords) and Type_of_Regulation in allowed_regulation_types
                    ):
                        print("Title:", Original_Title)
                        print("Source:", low_url)
                        print("Type of Regulation:", Type_of_Regulation)
                        print("Date of Adoption:", Date_of_adoption)
                        print("Entry Into Force Date:", Entry_Into_Force_Date,'\n')
                        results.append(row)
                    else:
                        print("the duplicate data or ESg exculded data have this link :",low_url,'\n')
            else:
                print(f"Failed to fetch data. Status code: {response.status_code}")


        except Exception as error:
            error_list.append(f"{error}")


def main():
    for key_word in keyword_list:
        try:
            print('\n',"🔍 Search Keyword :", key_word,'\n')
            get_page_content(key_word)
            df = pd.DataFrame(results)
            df.to_excel(out_excel_file, index=False)
        except Exception as error:
            error_list.append(str(error))

if __name__ == "__main__":
    main()