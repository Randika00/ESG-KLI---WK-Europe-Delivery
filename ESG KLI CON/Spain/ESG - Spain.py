import urllib.parse
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from deep_translator import GoogleTranslator
import time
import re
import pandas as pd
import os.path

# Headers to simulate a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

# Translate Spanish regulation types to English
RANGO_TRANSLATIONS = {
    'Ley': 'Law',
    'Ley Orgánica': 'Law',
    'Real Decreto': 'Decree',
    'Real Decreto-ley': 'Decree',
    'Real Decreto Legislativo': 'Decree',
    'Decreto-ley': 'Decree',
    'Resolución': 'Resolution',
    'Regulación': 'Regulation',
    'Decisión': 'Decision',
    'Orden': 'Order',
    'Directiva': 'Directive'
}

# Terms that indicate irrelevant or repealed legislation
DISALLOWED_TERMS = [
    "enmienda", "apropiación", "derogado", "revocado", "aeropuerto", "aerolínea",
    "cita", "fijado", "presupuesto", "paciente", "coronavirus", "covid-19", "disposición derogada"
]

# Output Excel path
out_excel_file = os.path.join(os.getcwd(), "Spain.xlsx")

# Global tracking sets and lists
seen_titles = set()
seen_links = set()
result_list = []
completed_list = []
completed_sources = []

def encode_keyword(keyword):
    return f"%22{urllib.parse.quote(keyword.replace(' ', '+'), safe='+')}%22"

def clean_url(url):
    return re.sub(r'(&page=\d+)', '', url) if "accion=Buscar" in url else url

def format_date(date_str):
    try:
        for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    except:
        pass
    return None

def translate_to_english(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except:
        return None

def print_article_metadata(meta):
    print("Jurisdiction : Spain")
    print(f"      🌐 Article URL: {meta['Source Link']}")
    print(f"         🟡 Original Title: {meta['Original Title']}")
    print(f"         🟢 English Title: {meta['English Translation']}")
    print(f"         📌 Type of Regulation: {meta['Type of Regulation']}")
    print(f"         🕒 Date of Adoption: {meta['Date of Adoption']}")
    print(f"         🕒 Entry into Force: {meta['Entry Into Force Date']}")

def extract_article_metadata(article_url):
    if article_url in seen_links:
        return None

    try:
        response = requests.get(article_url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        if "disposición derogada" in soup.get_text(strip=True).lower():
            return None

        title_tag = soup.find("h3", class_="documento-tit")
        title = title_tag.get_text(strip=True) if title_tag else None
        if not title:
            return None

        if any(term in title.lower() for term in DISALLOWED_TERMS):
            return None
        if title in seen_titles:
            return None

        seen_titles.add(title)
        seen_links.add(article_url)

        analysis = soup.find("div", id="panelAnalisis")
        rango_raw = fecha_disposicion = fecha_publicacion = fecha_vigor = None

        if analysis:
            items = analysis.select("ul.bullet-boe li")
            for li in items:
                txt = li.get_text(strip=True)
                if txt.startswith("Rango:"):
                    rango_raw = txt.split(":", 1)[1].strip()
                elif txt.startswith("Fecha de disposición:"):
                    fecha_disposicion = format_date(txt.split(":", 1)[1].strip())
                elif txt.startswith("Fecha de publicación:"):
                    fecha_publicacion = format_date(txt.split(":", 1)[1].strip())
                elif txt.startswith("Fecha de entrada en vigor:"):
                    fecha_vigor = format_date(txt.split(":", 1)[1].strip())

        # ✅ Skip if Rango not in translations
        if rango_raw not in RANGO_TRANSLATIONS:
            return None

        type_of_regulation = RANGO_TRANSLATIONS[rango_raw]
        entry_into_force = fecha_vigor or fecha_publicacion
        title_en = translate_to_english(title)

        entry = {
            "Jurisdiction": "Spain",
            "Original Title": title,
            "English Translation": title_en,
            "Type of Regulation": type_of_regulation,
            "Source Link": article_url,
            "Date of Adoption": fecha_disposicion,
            "Entry Into Force Date": entry_into_force
        }

        if (entry["Source Link"] not in completed_sources and entry["Original Title"] not in completed_list):
            result_list.append(entry)
            completed_list.append(entry["Original Title"])
            completed_sources.append(entry["Source Link"])
            print(entry)
            print()
            time.sleep(0.5)  # Delay after each article

    except Exception as e:
        print(f"      ❌ Error reading article: {e}")
        return None

def get_total_pages(soup):
    pag = soup.find("div", class_="paginar2")
    if not pag:
        return 1
    nums = [int(tag.text.strip()) for tag in pag.find_all(["a", "span"]) if tag.text.strip().isdigit()]
    return max(nums) if nums else 1

def process_page(url, visited, referer=None, page_number=None):
    cleaned = clean_url(url)
    if cleaned in visited:
        return [], False

    try:
        headers = HEADERS.copy()
        if referer:
            headers["Referer"] = referer
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return [], False

        visited.add(cleaned)
        soup = BeautifulSoup(resp.text, "lxml")

        print(f"   ✅ Page {page_number} URL: {url}")
        base = "https://www.boe.es/"
        for block in soup.find_all("li", class_="resultado-busqueda"):
            a = block.find("a", class_="resultado-busqueda-link-defecto")
            if a:
                article_url = urllib.parse.urljoin(base, a["href"])
                extract_article_metadata(article_url)

        new_links = []
        pagin = soup.find("div", class_="paginar2")
        if pagin:
            for a_tag in pagin.find_all("a", href=True):
                href = a_tag["href"]
                if "accion=Mas" in href and ',-0-50' not in href:
                    full_url = urllib.parse.urljoin(url, href)
                    new_links.append(full_url)

        time.sleep(1.0)  # Delay after each page
        return new_links, True

    except Exception as e:
        print(f"      ❌ Error processing page: {e}")
        return [], False

def scrape_boe_for_keyword(keyword):
    print(f"\n🔍 Keyword: {keyword}")
    encoded_kw = encode_keyword(keyword)
    search_url = (
        "https://www.boe.es/buscar/legislacion.php?"
        "campo%5B0%5D=ID_SRC&dato%5B0%5D=&operador%5B0%5D=and&"
        "campo%5B1%5D=NOVIGENTE&operador%5B1%5D=and&"
        f"campo%5B2%5D=&dato%5B2%5D={encoded_kw}&checkbox_solo_tit=S&"
        "operador%5B2%5D=and&page_hits=50&page=1&"
        "sort_field%5B0%5D=PESO&sort_order%5B0%5D=desc&"
        "sort_field%5B1%5D=REF&sort_order%5B1%5D=asc&accion=Buscar"
    )

    visited = set()
    queue = [search_url]
    page_number = 1

    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")
            total_pages = get_total_pages(soup)
            print(f"   📄 Total pages: {total_pages}")
    except Exception as e:
        print(f"   ⚠️ Could not fetch total pages early: {e}")

    while queue:
        current_url = queue.pop(0)
        new_links, success = process_page(current_url, visited, referer=search_url, page_number=page_number)
        if success:
            page_number += 1
            for link in new_links:
                if clean_url(link) not in visited and clean_url(link) not in map(clean_url, queue):
                    queue.append(link)

def main():
    try:
        with open("key_word.txt", "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"❌ Error reading 'key_word.txt': {e}")
        keywords = []

    for kw in keywords:
        scrape_boe_for_keyword(kw)
        time.sleep(2.0)  # Delay between keywords

    if result_list:
        df = pd.DataFrame(result_list)
        df.to_excel(out_excel_file, index=False)
        print(f"\n✅ Metadata saved to '{out_excel_file}'")
    else:
        print("\n⚠️ No valid metadata to save.")

if __name__ == "__main__":
    main()