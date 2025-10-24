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
import urllib.parse
import re
from datetime import datetime
import platform
from urllib.parse import urlparse
results = []
error_list = []
completed_list =[]
completed_sources = []

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
}

out_excel_file = os.path.join(os.getcwd(), "New Zealand.xlsx")

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
    "amendment",
    "appropriation",
    "repealed",
    "revoked",
    "airport",
    "airline",
    "appointment",
    "appointed",
    "budget",
    "patient",
    "coronavirus",
    "covid-19"
]


def get_english_text(text):
    translated_text = GoogleTranslator(source='pl', target='en').translate(text)
    return translated_text


def normalize_date(date_str):
    if not date_str:
        return None
    clean_date = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str.lower())
    clean_date = clean_date.replace("day of", "").strip()
    try:
        # Parse the cleaned date
        parsed_date = datetime.strptime(clean_date, "%d %B %Y")
        # Return in yyyy-mm-dd format
        return parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        return None


def legistaltion_data(soup):
    try:
        li_tag = soup.find("li", class_="whole")
        href = li_tag.find("a")["href"] if li_tag and li_tag.find("a") else None
        whole_link =f"https://www.legislation.govt.nz{href}"
        soup = get_soup(whole_link)
        div_tag = soup.find("div", class_="cover")
        # print(div_tag)

        if div_tag:
            # print("✅ Div found!")
            title_tag = div_tag.find("h1", class_="title")
            title = title_tag.get_text(strip=True) if title_tag else None

            # ✅ 2. Determine regulation type (Act, Bill, Regulation, etc.)
            reg_type = None
            if title:
                for keyword in ["Act", "Bill", "Regulation", "Decree", "Order"]:
                    if keyword.lower() in title.lower():
                        reg_type = keyword
                        break

            adoption_date = None

            adoption_tag = soup.find("div", class_="assent-date")
            adoption_date = adoption_tag.get_text(strip=True) if adoption_tag else None


            if adoption_date is None:
                made_div = soup.find("div", class_="made")

                if made_div:
                    # Look for <p> that contains the phrase "At Wellington this"
                    for p in made_div.find_all("p", class_="made-at"):
                        text = p.get_text(strip=True)
                        if "at wellington this" in text.lower():
                            # Extract date using regex
                            match = re.search(r'At Wellington this (.+)', text, re.IGNORECASE)
                            if match:
                                adoption_date = match.group(1).strip()

                            break
                else:
                    adoption_tag = soup.find("td", class_="assent-date")
                    adoption_date = adoption_tag.get_text(strip=True) if adoption_tag else None

            entry_force_date = None
            entry_force_tag = soup.find("div", class_="commencement")
            if entry_force_tag:
                entry_force_date = entry_force_tag.get_text(strip=True)


                # 🧠 Check if it contains a real date or a reference like "see section"
                if "see section" in entry_force_date.lower() or "see" in entry_force_date.lower():

                    table = soup.find("table", class_="tocentrylayout", summary="Table of Contents")
                    target_href = None
                    for tr in table.find_all("tr"):
                        td = tr.find("td", class_="tocColumn2")

                        if td:
                            text = td.get_text(strip=True).lower()

                            # Check for exact or partial match
                            if text == "short title and commencement" or "commencement" in text:
                                a_tag = td.find("a")
                                if a_tag and a_tag.get("href"):
                                    target_href = a_tag["href"]
                                    id = target_href.replace("#", "")
                                    # print(id)
                                    # You might want to store it instead of breaking, depending on your logic
                                    break
                            else:
                                entry_force_date = None  # ignore it if it's just a reference

                    div_tag = soup.find("div", attrs={"id": f"{id}"})

                    if div_tag:
                        # print(div_tag.prettify())
                        if text == "short title and commencement":
                            for p in div_tag.find_all("p"):
                                text = p.get_text(strip=True)
                                # Check if the phrase "come into force" is in the text
                                if "into force" in text.lower():
                                    # Extract the date after "on" using regex
                                    match = re.search(r"on\s+([0-9]{1,2}\s+\w+\s+[0-9]{4})", text)
                                    if match:
                                        entry_force_date = match.group(1)

                                        break
                                else:
                                    entry_force_date = None

                        elif text == "commencement":
                            entry_force_dates = []
                            for p in div_tag.find_all("p"):
                                text = p.get_text(strip=True)
                                # Check if the phrase "come into force" is in the text
                                if "into force" in text.lower():
                                    # Extract the date after "on" using regex
                                    match = re.search(r"on\s+([0-9]{1,2}\s+\w+\s+[0-9]{4})", text)
                                    if match:
                                        date_text = match.group(1)
                                        entry_force_dates.append(date_text)
                                        break
                                else:
                                    entry_force_date = None

                            history_div = div_tag.find("div", class_="history")
                            if history_div:
                                for p in history_div.find_all("p"):
                                    text = p.get_text(" ", strip=True).lower()
                                    if "into force" in text:
                                        date_span = p.find("span", class_="amendment-date")
                                        if date_span:
                                            date_text = date_span.get_text(strip=True).replace("\xa0", " ")
                                            entry_force_dates.append(date_text)


                            if entry_force_dates:
                                try:
                                    # Convert to datetime objects
                                    parsed_dates = [datetime.strptime(d, "%d %B %Y") for d in entry_force_dates]

                                    # Get the earliest date
                                    earliest_date = min(parsed_dates)

                                    # Convert back to string safely across platforms
                                    if platform.system() == "Windows":
                                        entry_force_date = earliest_date.strftime("%#d %B %Y")

                                    else:
                                        entry_force_date = earliest_date.strftime("%-d %B %Y")

                                except ValueError:
                                    # If date parsing fails for some reason
                                    entry_force_date = None

                        else:
                            entry_force_date = None

                    else:
                        print("Div not found.")
            else:
                toc_div = soup.find("div", class_="toc")

                if toc_div:
                    # Find all <a> tags with class "toc" inside this div
                    for a_tag in toc_div.find_all("a", class_="toc"):
                        text = a_tag.get_text(strip=True)
                        if "commencement" in text.lower():  # check if text contains "Commencement"
                            target_id = a_tag.get("href", "").replace("#", "")
                            # print("Found Commencement ID:", target_id)
                            break
                    div_tag = soup.find("div", attrs={"id": f"{target_id}"})
                    for p in div_tag.find_all("p"):
                        text = p.get_text(strip=True)
                        # Check if the phrase "come into force" is in the text
                        if "into force" in text.lower():
                            # Extract the date after "on" using regex
                            match = re.search(r"on\s+([0-9]{1,2}\s+\w+\s+[0-9]{4})", text)
                            if match:
                                entry_force_date = match.group(1)
                                break
                        else:
                            entry_force_date = None

            # ✅ Print results
            # print("Title:", title)
            # print("Regulation Type:", reg_type)
            # print("Date of Adoption:", adoption_date)
            # print("Entry into Force Date:", entry_force_date)
            parsed_url = urlparse(whole_link)
            source = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            adoption_date =normalize_date(adoption_date)
            entry_force_date = normalize_date(entry_force_date)


            row_data = {
                "Jurisdiction": "New Zealand",
                "Original Title": title,
                "Type of Regulation": reg_type,
                "Source": source,
                "Date of adoption": adoption_date,
                "Entry Into Force Date": entry_force_date
            }

            title_lower = title.lower()
            if (title not in completed_list
                    and source not in completed_sources
                    and not any(keyword in title_lower for keyword in
                                non_esg_keywords)):
                results.append(row_data)
                print(row_data)
                completed_list.append(title)
                completed_sources.append(source)
            else:
                print("the duplicate data or ESg exculded data have this link :", source, '\n')

        else:
            print("❌ Div not found.")

    except Exception as error:
        error_list.append(str(error))



def generate_legislation_url(keyword) :
    base_url = "https://www.legislation.govt.nz/all/results.aspx"
    encoded_keyword = urllib.parse.quote_plus(keyword)  # ✅ encodes spaces as '+'

    query = (
        f"ad_act%40bill%40regulation__%22{encoded_keyword}%22____200_"
        "ac%40bc%40rc%40dn%40apub%40bgov%40rpub%40rimp_"
        "ac%40bc%40rc%40ainf%40anif%40aaif%40aase%40bcur%40bena%40rinf%40rnif%40raif%40rasm_a_ew_sd_"
        "&p=1"
    )
    url =f"{base_url}?search={query}"
    print(url)
    soup = get_soup(url)
    table = soup.find("table", id="ctl00_Cnt_mixedTable")

    if table:
        for row in table.find_all("tr", class_=["resultsOdd", "resultsEven"]):
            a_tag = row.find("a", href=True)
            if a_tag:
                href =a_tag["href"]
                a_url =f"https://www.legislation.govt.nz{href}"
                print(a_url)
                a_soup = get_soup(a_url)
                legistaltion_data(a_soup)

    else:
        print("❌ Table not found.")
    return f"{base_url}?search={query}"


def main():
    for key_word in keyword_list:
        try:
            print(key_word)
            generate_legislation_url(key_word)
            df = pd.DataFrame(results)
            df.to_excel(out_excel_file, index=False)
        except Exception as error:
            error_list.append(str(error))

if __name__ == "__main__":
    main()