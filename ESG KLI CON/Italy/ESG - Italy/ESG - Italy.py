import requests
from bs4 import BeautifulSoup
import time
import re
import os.path
from datetime import datetime
from deep_translator import GoogleTranslator
import pandas as pd

with open('keywords.txt', 'r', encoding='utf-8') as f:
    keywords = [line.strip() for line in f if line.strip()]

base_url = "https://www.gazzettaufficiale.it/ricerca/atto/serie_generale/originario?reset=true&normativi=true"
search_url = "https://www.gazzettaufficiale.it/do/ricerca/atto/serie_generale/originario/0"

def get_new_session():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.gazzettaufficiale.it",
        "Referer": base_url
    }
    session.headers.update(headers)
    try:
        session.get(base_url, timeout=10)
    except Exception as e:
        print(f"⚠️ Failed to open base URL: {e}")
    return session

def detect_regulation_type(title):
    title_lower = title.lower()
    if "legge" in title_lower:
        return "Law"
    elif any(term in title_lower for term in [
        "decreto", "decreto-legge", "regio decreto", "regio decreto-legge",
        "decreto legislativo", "decreto del presidente"
    ]):
        return "Decree"
    else:
        return "Unknown"

month_map = {
    "gennaio": "01", "febbraio": "02", "marzo": "03", "aprile": "04", "maggio": "05", "giugno": "06",
    "luglio": "07", "agosto": "08", "settembre": "09", "ottobre": "10", "novembre": "11", "dicembre": "12"
}

def extract_date(article_title):
    match = re.search(r"\b(\d{1,2})\s+([a-z]+)\s+(\d{4})", article_title.lower())
    if match:
        day, month_it, year = match.groups()
        month = month_map.get(month_it)
        if month:
            day = day.zfill(2)
            return f"{year}-{month}-{day}"
    return "Unknown"

def get_response_with_retry(url, headers=None, retries=3, delay=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"⚠️ Retry {attempt + 1}/{retries} failed for {url}: {e}")
            time.sleep(delay)
    print(f"❌ Failed to fetch {url} after {retries} retries.")
    return None

session = get_new_session()
out_excel_file = os.path.join(os.getcwd(), "Italy.xlsx")

result_list = []
error_list = []
duplicate_list = []
completed_list = []
completed_sources = []

article_div = "https://www.gazzettaufficiale.it"

excluded_keywords = [
    "modifiche", "appropriazione", "bilancio", "abrogato",
    "revocato", "aeroporto", "compagnia aerea", "appuntamento",
    "nominato", "paziente", "coronavirus", "covid-19"
]

for idx, keyword in enumerate(keywords):
    print(f"\n🔍 Processing keyword: {keyword}\n{'='*50}")

    if idx % 10 == 0 and idx > 0:
        session = get_new_session()

    payload = {
        "cerca": "Cerca",
        "attiNumerati": "true",
        "tipoRicercaTitolo": "ENTIRE_STRING",
        "titolo": keyword,
        "tipoRicercaTesto": "ALL_WORDS"
    }

    try:
        response = session.post(search_url, data=payload, timeout=15)
        response.encoding = 'utf-8'
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        if "la sessione di ricerca é scaduta" in soup.get_text().lower():
            print("⏳ Session expired — retrying with fresh session...")
            session = get_new_session()
            response = session.post(search_url, data=payload, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

        if "la sessione di ricerca é scaduta" in soup.get_text().lower():
            print("❌ Session expired again — skipping this keyword.")
            continue

        if "nessun risultato" in soup.get_text().lower():
            print("❌ No results found for this keyword.")
            continue

        div_elements = soup.find("div", id="elenco_hp")
        if div_elements:
            results = div_elements.find_all("span", class_="risultato")
            total_count = len(results)
            print(f"📄 Total number of articles found: {total_count}\n")

            for single_element in results:
                article_link, article_title = None, None
                try:
                    article_title_div = single_element.find("a")
                    if article_title_div:
                        article_title = article_title_div.find("span").text.strip()
                        article_link_tag = article_title_div.get('href')
                        article_link = article_div + article_link_tag if article_link_tag else ""

                        regulation_type = detect_regulation_type(article_title)
                        adoption_date = extract_date(article_title)

                        article_response = get_response_with_retry(article_link, headers=session.headers)
                        if article_response and article_response.status_code == 200:
                            article_soup = BeautifulSoup(article_response.text, 'html.parser')

                            next_page_h2 = article_soup.find("div", id="titolo_atto").find("h2", class_="consultazione")
                            Short_Title = ""
                            if next_page_h2:
                                title_a = next_page_h2.contents[0].strip()
                                span = next_page_h2.find("span")
                                title_b = span.get_text(strip=True) if span else ""
                                Short_Title = f"{title_a} {title_b}".strip()

                            long_next_text = article_soup.find("div", id="testa_atto").find("h3", class_="consultazione")
                            Long_Title = long_next_text.get_text(strip=True) if long_next_text else ""

                            Original_Title = f"{Short_Title} - {Long_Title}".strip(" -")

                            if any(term in Original_Title.lower() for term in excluded_keywords):
                                print(f"⛔ Skipping due to excluded term in title: {Original_Title}")
                                continue

                            try:
                                translated_title = GoogleTranslator(source='it', target='en').translate(Original_Title)
                                time.sleep(1)
                            except Exception as e:
                                translated_title = ""
                                print(f"❌ Translation failed: {e}")

                            entry_force_date = ""
                            rosso_spans = article_soup.find("div", id="testa_atto").find_all("span", class_="rosso")
                            date_pattern = r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"

                            for span in rosso_spans:
                                text = span.get_text(strip=True)
                                if "in vigore" in text.lower():
                                    match = re.search(date_pattern, text)
                                    if match:
                                        day, month, year = match.groups()
                                        try:
                                            date_obj = datetime.strptime(f"{day.zfill(2)}-{month.zfill(2)}-{year}", "%d-%m-%Y")
                                            entry_force_date = date_obj.strftime("%Y-%m-%d")
                                        except ValueError:
                                            print(f"⚠️ Failed to parse date: {match.group()}")
                                        break

                            entry = {
                                "Jurisdiction": "Italy",
                                "Original Title": Original_Title,
                                "English Translation": translated_title,
                                "Type of Regulation": regulation_type,
                                "Source Link": article_link,
                                "Date of Adoption": adoption_date,
                                "Entry Into Force Date": entry_force_date
                            }
                            if (entry["Source Link"] not in completed_sources and entry["Original Title"] not in completed_list):
                                result_list.append(entry)
                                completed_list.append(entry["Original Title"])
                                completed_sources.append(entry["Source Link"])
                                print(entry)

                except Exception as error:
                    message = f"Error link - {article_link}: {str(error)}"
                    print(f"{article_link}: {str(error)}")
                    error_list.append(message)

        else:
            print("⚠️ Your search session has expired - Results section not found in HTML!")

        time.sleep(2)

    except requests.RequestException as e:
        print(f"❌ Network error for '{keyword}': {e}")
    except Exception as ex:
        print(f"❌ Unexpected error for '{keyword}': {ex}")

if result_list:
    df = pd.DataFrame(result_list)
    df.to_excel(out_excel_file, index=False)
    print(f"\n✅ Metadata saved to '{out_excel_file}'")
else:
    print("\n⚠️ No valid metadata to save.")

if error_list:
    with open("errors.log", "w", encoding="utf-8") as f:
        for line in error_list:
            f.write(line + "\n")
    print("⚠️ Errors logged to 'errors.log'")
