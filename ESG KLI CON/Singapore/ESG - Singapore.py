import requests
import pandas as pd
import json
import re
import time
import io
from datetime import datetime
from PyPDF2 import PdfReader
import pdfplumber
import logging
import warnings

# -----------------------------
# Suppress all warnings from pdfplumber and PyPDF2
# -----------------------------
logging.getLogger('pdfplumber').setLevel(logging.ERROR)
logging.getLogger('PyPDF2').setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning, module='pdfplumber')
warnings.filterwarnings("ignore", category=UserWarning, module='PyPDF2')

# -----------------------------
# Read keywords
# -----------------------------
with open("keyword.txt", "r", encoding="utf-8") as f:
    keywords = [line.strip() for line in f if line.strip()]

# -----------------------------
# API details
# -----------------------------
url = "https://1v7dzgzjkk-dsn.algolia.net/1/indexes/*/queries"
headers = {
    "x-algolia-agent": "Algolia for JavaScript (4.20.0); Browser (lite); instantsearch.js (4.60.0); JS Helper (3.15.0)",
    "x-algolia-api-key": "ff6219a3539653aa48773bf03199b95e",
    "x-algolia-application-id": "1V7DZGZJKK",
    "Content-Type": "application/json"
}

all_results = []

# -----------------------------
# Regulation types
# -----------------------------
regulation_types = ["Act", "Bill", "Notice", "Order", "Regulation", "Rule", "Notification"]

def get_regulation_type(title):
    for rtype in regulation_types:
        if re.search(rf"\b{rtype}\b", title, re.IGNORECASE):
            return rtype
    return None

# -----------------------------
# Exclusions
# -----------------------------
exclude_terms = [
    "amendment", "appropriation", "repealed", "revoked",
    "airport", "airline", "appointment", "appointed",
    "budget", "patient", "coronavirus", "covid-19"
]
exclude_pattern = re.compile("|".join(exclude_terms), re.IGNORECASE)

# -----------------------------
# Date extraction patterns
# -----------------------------
date_patterns = [
    r'Commencement\s*:\s*(\d{1,2}\s+(?:January|February|March|April|May|June|'
    r'July|August|September|October|November|December)\s+\d{4})',
    r'come into operation on\s*(\d{1,2}\s+(?:January|February|March|April|May|'
    r'June|July|August|September|October|November|December)\s+\d{4})',
    r'come into force on\s*(\d{1,2}\s+(?:January|February|March|April|May|June|'
    r'July|August|September|October|November|December)\s+\d{4})',
    r'[A-Z]+,\s+([A-Z]+\s+\d{1,2},\s+\d{4})',
    r'Made on\s*(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|'
    r'September|October|November|December)\s+\d{4})',
    r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|'
    r'October|November|December)\s+\d{4})'
]

def extract_entry_into_force_date(pdf_url):
    try:
        response = requests.get(pdf_url, timeout=30)
        if response.status_code != 200:
            return None

        pdf_file = io.BytesIO(response.content)
        text = ""

        # Try pdfplumber first
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages[:3]:  # First 3 pages
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except:
                        continue
        except Exception as e:
            # Fall back to PyPDF2
            try:
                pdf_file.seek(0)  # Reset file pointer
                pdf_reader = PdfReader(pdf_file)
                for page_num in range(min(3, len(pdf_reader.pages))):
                    try:
                        page_text = pdf_reader.pages[page_num].extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except:
                        continue
            except Exception as e2:
                return None

        found_dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if "," in match:  # Handle "JUNE 12, 2020"
                        parts = match.split()
                        month = parts[0]
                        day = parts[1].rstrip(",")
                        year = parts[2]
                        date_str = f"{day} {month} {year}"
                    else:
                        date_str = match
                    date_obj = datetime.strptime(date_str, "%d %B %Y")
                    found_dates.append(date_obj)
                except ValueError:
                    continue

        if not found_dates:
            return None
        return min(found_dates).strftime("%Y-%m-%d")

    except Exception as e:
        return None

# -----------------------------
# Main scraping loop (all pages)
# -----------------------------
total_keywords = len(keywords)
keyword_count = 0

for keyword in keywords:
    keyword_count += 1
    page = 0
    print(f"\nProcessing keyword {keyword_count}/{total_keywords}: {keyword}")

    while True:  # Loop until no hits returned
        payload = {
            "requests": [
                {
                    "indexName": "prod_ogp_egazettes_index",
                    "params": (
                        "facetFilters=%5B%5B%22category%3AGovernment+Gazette%22%2C"
                        "%22category%3ALegislative+Supplements%22%2C"
                        "%22category%3AOther+Supplements%22%5D%2C"
                        "%5B%22subCategory%3AActs+Supplement%22%2C"
                        "%22subCategory%3ABankruptcy+Act+Notice%22%2C"
                        "%22subCategory%3ABills+Supplement%22%2C"
                        "%22subCategory%3ACompanies+Act+Notice%22%2C"
                        "%22subCategory%3AIndustrial+Relations+Supplement%22%2C"
                        "%22subCategory%3ANotices+under+other+Acts%22%2C"
                        "%22subCategory%3ANotices+under+the+Constitution%22%2C"
                        "%22subCategory%3ARevised+Acts%22%2C"
                        "%22subCategory%3ARevised+Subsidiary+Legislation%22%2C"
                        "%22subCategory%3ASubsidiary+Legislation+Supplement%22%2C"
                        "%22subCategory%3ATrade+Marks+Supplement%22%2C"
                        "%22subCategory%3ATreaties+Supplement%22%5D%5D&"
                        "facets=%5B%22category%22%2C%22publishMonth%22%2C%22publishYear%22%2C%22subCategory%22%5D&"
                        "highlightPostTag=__/ais-highlight__&highlightPreTag=__ais-highlight__&"
                        "maxValuesPerFacet=100&page=" + str(page) + "&query=" + keyword.replace(" ", "+")
                    )
                }
            ]
        }

        max_retries = 3
        retry_delay = 1  # seconds
        data = None
        
        for retry in range(max_retries):
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    break
                else:
                    print(f"  API returned status {response.status_code}, retrying...")
                    time.sleep(retry_delay * (retry + 1))
            except Exception as e:
                print(f"  Request failed: {str(e)}, retrying...")
                time.sleep(retry_delay * (retry + 1))
        else:
            print(f"  Failed to get data for page {page} after {max_retries} attempts")
            break

        if data is None:
            break

        hits = []
        for req in data.get("results", []):
            hits.extend(req.get("hits", []))

        if not hits:
            print(f"  Page {page}: No more results.")
            break

        print(f"  Page {page}: Found {len(hits)} results")

        for hit in hits:
            title = hit.get("title", "")
            pdf_url = hit.get("fileUrl", "")
            publish_date = hit.get("publishDate", "")

            if exclude_pattern.search(title):
                continue

            regulation_type = get_regulation_type(title)
            if not title or not pdf_url or regulation_type is None:
                continue

            entry_into_force_date = extract_entry_into_force_date(pdf_url)
            if not entry_into_force_date:
                continue

            all_results.append({
                "Original Title": title,
                "Source Link": pdf_url,
                "Date of Adoption": publish_date,
                "Entry into Force Date": entry_into_force_date,
                "Type of Regulation": regulation_type
            })

        page += 1
        time.sleep(0.3)

    time.sleep(0.5)

# -----------------------------
# Data cleaning & Excel export
# -----------------------------
if not all_results:
    print("No results found. Exiting.")
    exit()

df = pd.DataFrame(all_results)
print(f"Total results before cleaning: {len(df)}")

# Remove duplicates
df.drop_duplicates(subset=["Source Link"], inplace=True, keep="first")
df.drop_duplicates(subset=["Original Title"], inplace=True, keep="first")

# Exclude unwanted terms again at DataFrame level
df = df[~df["Original Title"].str.contains(exclude_pattern, na=False)]
print(f"Total results after exclusions & deduplication: {len(df)}")

# Format dates
df["Date of Adoption"] = pd.to_datetime(df["Date of Adoption"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")
df["Entry into Force Date"] = pd.to_datetime(df["Entry into Force Date"], errors="coerce").dt.strftime("%Y-%m-%d")

# Final formatting
df.rename(columns={
    "Source Link": "Source",
    "Date of Adoption": "Date of adoption",
    "Entry into Force Date": "Entry Into Force Date"
}, inplace=True)

df["Jurisdiction"] = "Singapore"

df_final = df[[
    "Jurisdiction", "Original Title", "Type of Regulation",
    "Source", "Date of adoption", "Entry Into Force Date"
]]

# Save to Excel
output_file = "Singapore.xlsx"
df_final.to_excel(output_file, index=False)
print(f"\n✅ Cleaned data saved to {output_file}")