import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import time
from deep_translator import GoogleTranslator

BASE_URL = "https://laws.boe.gov.sa"
SEARCH_URL = "https://laws.boe.gov.sa/BoeLaws/Laws/Search/"

with open("keyword.txt", "r", encoding="utf-8") as f:
    keywords = [line.strip() for line in f if line.strip()]

non_esg_keywords = [
    "تعديل", "التخصيص", "ميزانية", "إلغاء", "مطار",
    "شركة طيران", "ميعاد", "مُعيَّن", "مريض", "فيروس كورونا"
]

allowed_regulation_types = ["Royal Decree"]

completed_list = []
completed_sources = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8",
    "Connection": "keep-alive",
}

def format_date_from_span(span_text):
    match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", span_text)
    if match:
        day, month, year = match.groups()
        day = day.zfill(2)
        month = month.zfill(2)
        return f"{year}-{month}-{day}"
    return ""

def detect_regulation_type(title):
    if "مرسوم ملكي" in title:
        return "Royal Decree"
    return ""

results = []

for idx, keyword in enumerate(keywords):
    print(f"\n🔎 Searching for {idx}: {keyword}")
    params = {"Query": keyword, "TitlesOnly": "true", "LanguageId": "1"}
    r = requests.get(SEARCH_URL, params=params, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.select("a.result-keyword-title")
    print(f"  Found {len(links)} result(s) for this keyword.")

    for i, link in enumerate(links, 1):
        title = link.get_text(strip=True)
        title_lower = title.lower()
        pdf_link = BASE_URL + link["href"]

        detail_page = requests.get(pdf_link, headers=headers)
        detail_soup = BeautifulSoup(detail_page.text, "html.parser")

        h4_title = detail_soup.find("h4", class_="center")
        original_title_ar = h4_title.get_text(strip=True) if h4_title else title

        try:
            original_title_en = GoogleTranslator(source='ar', target='en').translate(original_title_ar)
        except:
            original_title_en = ""

        Type_of_regulation = detect_regulation_type(original_title_ar)

        adoption_date = ""
        date_label = detail_soup.find("label", string=re.compile("تاريخ الإصدار"))
        if date_label:
            span = date_label.find_next_sibling("span")
            if span:
                adoption_date = format_date_from_span(span.get_text(strip=True))

        Jurisdiction = "Saudi Arabia"

        row_data = {
            "Jurisdiction": Jurisdiction,
            "Original Title": original_title_ar,
            "English Translation": original_title_en,
            "Type of Regulation": Type_of_regulation,
            "Source": pdf_link,
            "Date of Adoption": adoption_date,
            "Entry into Force Date": ""
        }

        if (title not in completed_list
                and pdf_link not in completed_sources
                and not any(term in title_lower for term in non_esg_keywords)
                and Type_of_regulation in allowed_regulation_types
        ):
            results.append(row_data)
            completed_list.append(title)
            completed_sources.append(pdf_link)

            print(f"\n✅ Added ({i}): {original_title_ar}")
            print(f"Source Link             : {pdf_link}")
            print(f"Original Title (Arabic) : {original_title_ar}")
            print(f"Original Title (English): {original_title_en}")
            print(f"Type of Regulation      : {Type_of_regulation}")
            print(f"Date of Adoption        : {adoption_date}")
            print(f"Jurisdiction            : {Jurisdiction}")
            print("===================================")
        else:
            print(f"⚠️ Skipped duplicate or excluded: {pdf_link}\n")

        time.sleep(0.3)

df = pd.DataFrame(results, columns=[
    "Jurisdiction",
    "Original Title",
    "English Translation",
    "Type of Regulation",
    "Source",
    "Date of Adoption",
    "Entry into Force Date"
])
df.to_excel("Saudi_Arabia.xlsx", index=False)

print(f"\n✅ Saved {len(df)} unique records to Saudi_Laws.xlsx and Saudi_Laws.csv")

