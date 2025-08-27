import re
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from datetime import datetime
import pandas as pd
import time
import dateparser

BASE_URL = "https://www.ejustice.just.fgov.be/cgi/"
SEARCH_URL = BASE_URL + "rech_res.pl"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
}

allowed_regulation_types = ["Law", "Decree", "Order", "Notice", "Regulation"]

EXCLUDE_TERMS = [
    "amendement", "appropriation", "abrogé", "révoqué", "aéroport",
    "compagnie aérienne", "rendez-vous", "nommé",
    "budget", "patient", "corona virus", "COVID 19", "COVID-19"
]

completed_list = []
completed_sources = []


translator = GoogleTranslator(source='fr', target='en')

def extract_article_details(article_url):
    full_url = BASE_URL + article_url
    resp = requests.get(full_url, headers=headers)
    soup = BeautifulSoup(resp.content, "html.parser")

    jurisdiction = "Belgium"

    try:
        original_title = soup.select_one(".intro-text").text.strip()
    except:
        original_title = ""

    if any(term.lower() in original_title.lower() for term in EXCLUDE_TERMS):
        return None

    try:
        date_part = original_title.split(".")[0].strip()
        date_of_adoption = dateparser.parse(date_part, languages=['fr']).strftime("%Y-%m-%d")
    except:
        date_of_adoption = ""

    try:
        french_type = original_title.split(". -")[1].split("modifiant")[0].strip().lower()
    except:
        french_type = ""

    if "loi" in french_type:
        type_of_reg = "Law"
    elif "arrêté" in french_type or "arrete" in french_type:
        type_of_reg = "Decree"
    elif "ordonnance" in french_type or "ordre" in french_type:
        type_of_reg = "Order"
    else:
        type_of_reg = french_type.title()

    entry_into_force = ""
    try:
        pdf_links = soup.select("a.links-link")
        for a in pdf_links:
            txt = a.get_text(separator=" ", strip=True).replace("\xa0", " ")
            txt = re.sub(r'\s+', ' ', txt)

            match = re.search(r'(?:du|van)\s+([0-9]{1,2}\s+\w+\s+[0-9]{4})', txt, re.IGNORECASE)
            if match:
                entry_into_force = dateparser.parse(match.group(1), languages=['fr', 'nl']).strftime("%Y-%m-%d")
                break

    except Exception as e:
        entry_into_force = ""
        print("Error extracting entry date:", e)

    try:
        source_link = soup.select_one(".links-link")["href"]
        if not source_link.startswith("http"):
            source_link = BASE_URL + source_link.lstrip("/")
    except:
        source_link = full_url

    try:
        title_en = translator.translate(original_title)
    except:
        title_en = ""

    return {
        "Jurisdiction": jurisdiction,
        "Original Title": original_title,
        "English Translation": title_en,
        "Type of Regulation": type_of_reg,
        "Source": source_link,
        "Date of adoption": date_of_adoption,
        "Entry Into Force Date": entry_into_force,
    }

def search_keyword(keyword, max_articles=None):
    all_results = []
    session = requests.Session()

    payload = {
        "htit": f'"{keyword}"',
        "fr": "f",
        "trier": "promulgation"
    }
    resp = session.post(SEARCH_URL, headers=headers, data=payload)
    soup = BeautifulSoup(resp.content, "html.parser")

    processed_count = 0

    while True:
        list_items = soup.select(".list-item")
        for item in list_items:
            article_link_tag = item.select_one(".list-item--button a")
            if article_link_tag:
                article_url = article_link_tag["href"]
                details = extract_article_details(article_url)
                if details:
                    title = details["Original Title"]
                    title_lower = title.lower()
                    pdf_link = details["Source"]
                    Type_of_regulation = details["Type of Regulation"]

                    if (title not in completed_list
                        and pdf_link not in completed_sources
                        and not any(k in title_lower for k in EXCLUDE_TERMS)
                        and Type_of_regulation in allowed_regulation_types
                    ):
                        all_results.append(details)
                        completed_list.append(title)
                        completed_sources.append(pdf_link)
                        processed_count += 1
                        print(f"[{keyword}] ({processed_count}) Added: {title[:60]}...")

                        if max_articles and processed_count >= max_articles:
                            print(f"Reached max {max_articles} articles for '{keyword}'")
                            return all_results
                    else:
                        print("Duplicate or excluded data skipped:", pdf_link, "\n")

        next_page_tag = soup.select_one("a[title='Page suivante']") or soup.select_one("a.pagination-next")
        if next_page_tag and "href" in next_page_tag.attrs:
            next_page_url = BASE_URL + next_page_tag["href"].lstrip("/")
            resp = session.get(next_page_url, headers=headers)
            soup = BeautifulSoup(resp.content, "html.parser")
            time.sleep(1)
        else:
            break

    print(f"Total articles for '{keyword}': {processed_count}")
    return all_results

if __name__ == "__main__":
    final_data = []

    with open("keyword.txt", "r", encoding="utf-8") as f:
        keywords = [line.strip() for line in f if line.strip()]

    for kw in keywords:
        print(f"Processing keyword: {kw}")
        results = search_keyword(kw)
        final_data.extend(results)
        print(f"Total filtered articles for '{kw}': {len(results)}\n")

    df = pd.DataFrame(final_data)
    df.to_excel("Belgium.xlsx", index=False)
    print(f"Saved {len(final_data)} unique filtered articles to Belgium_filtered.xlsx")



