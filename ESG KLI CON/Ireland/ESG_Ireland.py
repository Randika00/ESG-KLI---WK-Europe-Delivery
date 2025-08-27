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

headers2= {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
    "cache-control": "max-age=0",

    "host": "www.irishstatutebook.ie",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
}


out_excel_file = os.path.join(os.getcwd(), "Ireland.xlsx")
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
    "covid-19",  # lowercase for consistency in matching
]

try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().strip().splitlines()
except Exception as error:
    error_list.append(str(error))

def get_soup(url, param,retries=10, delay=3):
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, params=param, headers=headers)

            if response.status_code == 200:
                return response.json()
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


def get_bill_soup(session, url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                  "image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8",
        "Cache-Control": "max-age=0",
    }

    response = session.get(url, headers=headers)
    response.raise_for_status()  # Raise error if request failed

    return BeautifulSoup(response.content, "html.parser")

def get_irish_statute_soup(session, original_url):
    match = re.search(r"https://www\.irishstatutebook\.ie/(\d{4})/en/act/pub/(\d{4})/index\.html", original_url)
    if not match:
        raise ValueError("Invalid original Irish Statute Book URL format")

    year, act_num = match.groups()
    eli_url = f"https://www.irishstatutebook.ie/eli/{year}/act/{int(act_num)}/enacted/en/html"

    # Make GET request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    }
    response = session.get(eli_url, headers=headers)
    response.raise_for_status()  # Raise an error if status is not 200 OK

    # Parse and return soup
    return BeautifulSoup(response.content, "html.parser")



def get_get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    # Convert to print-friendly ELI format
    parsed = urlparse(url)
    parts = parsed.path.strip('/').split('/')
    if len(parts) < 4 or parts[2] != 'si':
        raise ValueError("URL is not a valid SI link")

    year = parts[0]
    number = parts[3].split('.')[0].lstrip('0')  # e.g., '0188' → '188'
    print_url = f"https://{parsed.netloc}/eli/{year}/si/{number}/made/en/print"

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
        "cache-control": "max-age=0",
        "connection": "keep-alive",
        "host": parsed.netloc,

        "if-none-match": "\"76b2-63b3fe85f7291-gzip\"",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
    }

    response = session.get(print_url, headers=headers)
    response.raise_for_status()  # Raise error if request failed
    return BeautifulSoup(response.content, 'html.parser')

def get_page_content(key_word):

    url = f"https://www.irishstatutebook.ie/solr/all_leg_title/select?q=%22{key_word}%22&rows=100&hl.maxAnalyzedChars=-1&sort=year+desc&facet=true&facet.field=year&facet.field=type&facet.mincount=1&json.nl=map&wt=json"
    start_value = 0
    total_count = 0

    while True:
        param = {
            "q": f"\"{key_word}\"",
            "rows": "100",
            "hl.maxAnalyzedChars": "-1",
            "sort": "year desc",
            "facet": "true",
            "facet.field": ["year", "type"],
            "json.nl": "map",
            "start": f"{start_value}",
            "wt": "json",
        }

        json_content = get_soup(url, param, retries=10, delay=3)
        json_response = json_content["response"]
        all_legislation = json_response["docs"]

        read_json_response(all_legislation)

        law_count_per_page = len(all_legislation)
        start_value += 100
        total_count += law_count_per_page
        if law_count_per_page<100:
            print(f"[{total_count}] {key_word} records found"+"\n")
            break

from urllib.parse import urlparse
from dateutil import parser
def read_json_response(all_laws):

    for sin_law in all_laws:

        try:
            title = None
            pdf_link = None
            entry_date = None
            adoption_date = None
            reg_type = None

            session = requests.Session()
            link = sin_law["link"]
            print(link)
            if "/si/" in link:
                try:
                    soup = get_get_soup(session, link)
                except Exception as e:
                    print("Failed to fetch or parse page:", e)
                    soup = None

                if soup:
                    # Extract title
                    try:
                        title = soup.find('h1', class_='row content-title col-md-12').get_text(strip=True)
                        reg_type = "S.I"
                    except Exception as e:
                        print("Title not found:", e)

                    # Extract PDF link
                    # try:
                    #     pdf_href = soup.find('ul', class_='nav nav-pills document-toolbar md-pull-right sm-pull-right') \
                    #         .find('a', class_='btn')['href']
                    #     if pdf_href:
                    #         parts = pdf_href.strip('/').split('/')  # ['pdf', '2025', 'en.si.2025.0188.pdf']
                    #         year = parts[1]
                    #         filename = parts[2]
                    #         number = filename.split('.')[3].lstrip('0')
                    #         pdf_link = f"https://www.irishstatutebook.ie/eli/{year}/si/{number}/made/en/pdf"
                    #     else:
                    #         pdf_link = link
                    #
                    # except Exception as e:
                    #     print("The Issue:", e)
                    try:
                        ul_tag = soup.find('ul', class_='nav nav-pills document-toolbar md-pull-right sm-pull-right')
                        a_tag = ul_tag.find('a', class_='btn') if ul_tag else None

                        if a_tag and a_tag.has_attr('href'):
                            pdf_href = a_tag['href']
                            parts = pdf_href.strip('/').split('/')  # e.g. ['pdf', '2025', 'en.si.2025.0188.pdf']
                            year = parts[1]
                            filename = parts[2]
                            number = filename.split('.')[3].lstrip('0')
                            pdf_link = f"https://www.irishstatutebook.ie/eli/{year}/si/{number}/made/en/pdf"
                        else:
                            pdf_link = link  # fallback
                    except Exception as e:
                        print("The Issue:", e)
                        pdf_link = link  # double fallback in case of parsing issues

                    # Extract table
                    try:
                        table = soup.find('div', class_='act-content', id='act').table
                    except Exception as e:
                        print("Table not found in act-content:", e)
                        table = None

                    # Extract Entry into Force Date
                    if table:
                        try:
                            entry_p = None
                            for p in table.find_all('p'):
                                text = p.get_text(separator=' ', strip=True)
                                if "Iris Oifigiúil" in text:
                                    entry_p = p
                                    break

                            if entry_p:
                                full_text = entry_p.get_text(separator=' ', strip=True)
                                if 'of' in full_text:
                                    entry_date = full_text.split('of', 1)[1].strip()
                                    parsed_entry_date = parser.parse(entry_date, fuzzy=True)
                                    entry_date = parsed_entry_date.strftime("%Y-%m-%d")
                        except Exception as e:
                            print("Error extracting entry into force date:", e)



                    if table:
                        try:
                            p_tags = table.find_all('p')
                            adoption_date = None

                            for i, p in enumerate(p_tags):
                                text = p.get_text(strip=True)
                                if "GIVEN under my Official Seal" in text:
                                    if i + 1 < len(p_tags):
                                        next_text = p_tags[i + 1].get_text(strip=True)
                                        try:
                                            # Try to parse and format the date
                                            parsed_date = parser.parse(next_text, fuzzy=True)
                                            adoption_date = parsed_date.strftime("%d %B %Y")  # e.g., 26 November 2009
                                            adoption_date = parsed_date.strftime("%Y-%m-%d")
                                        except Exception:
                                            adoption_date = None
                                    break

                            # Fallback: Look for pattern like "12th day of May, 1997"
                            if not adoption_date:
                                # date_pattern = re.compile(r"\d{1,2}(st|nd|rd|th)? day of [A-Za-z]+, \d{4}")
                                date_pattern = re.compile(
                                    r"\b(?:this\s+)?\d{1,2}(st|nd|rd|th)?\s+day\s+of\s+[A-Za-z]+,?\s+\d{4}\b"
                                )
                                for p in p_tags:
                                    match = date_pattern.search(p.get_text())
                                    if match:
                                        adoption_date = match.group()
                                        parsed_date = parser.parse(adoption_date, fuzzy=True)
                                        adoption_date = parsed_date.strftime("%Y-%m-%d")
                                        break

                        except Exception as e:
                            print("Error extracting adoption date:", e)




                # print("Title:", title)
                # print("Regulation type:", reg_type)
                # print("Entry into force date:", entry_date)
                # print("Adoption date:", adoption_date)
                # print("PDF link:", pdf_link)

            elif "/act/" in link:
                session = requests.Session()
                soup = get_irish_statute_soup(session, link)


                try:
                    # title = soup.find('h1', class_='row content-title col-md-12').get_text(strip=True)
                    h1 = soup.find('h1', class_='row content-title col-md-12')
                    title = h1.find(string=True, recursive=False).strip()
                    reg_type = "ACT"

                except Exception as e:
                    print("Title not found:", e)

                year, act_num = re.search(r"(\d{4})/en/act/pub/(\d{4})", link).groups()

                # Construct print URL
                pdf_link = f"https://www.irishstatutebook.ie/eli/{year}/act/{int(act_num)}/enacted/en/print.html"
                ul = soup.find("ul", class_="nav nav-pills document-toolbar")

                li = ul.find("li", role="presentation")  # Find first <li> with role="presentation"
                if li:
                    a = li.find("a", href=True)
                    if a:
                        url=a['href']
                        soup = get_bill_soup(session, url)
                        adoption_date_tag = soup.find('p', class_='c-ribbon__date')
                        adop_date = adoption_date_tag.get_text(strip=True) if adoption_date_tag else None
                        entry_date=adoption_date = datetime.strptime(adop_date, "%d %b %Y").strftime("%Y-%m-%d")


                    else:
                        entry_date = None
                        adoption_date = None
                else:
                    entry_date = None
                    adoption_date = None

                # print("Title:", title)
                # print("Regulation type:", reg_type)
                # print("Entry into force date:", entry_date)
                # print("Adoption date:", adoption_date)
                # print("PDF link:", pdf_link)
            else:
                print("Unknown type.")

            row_data = {
                "Jurisdiction": "Ireland",
                "Original Title": title,
                "Type of Regulation": reg_type,
                "Source": pdf_link,
                "Date of adoption": adoption_date,
                "Entry Into Force Date": entry_date
            }

            title_lower = title.lower()
            if (title not in completed_list
                    and pdf_link not in completed_sources
                    and not any(keyword in title_lower for keyword in
                                non_esg_keywords)):
                results.append(row_data)
                print(row_data,'\n')
                completed_list.append(title)
                completed_sources.append(pdf_link)
            else:
                print("the duplicate data or ESg exculded data have this link :", link, '\n')

        except Exception as error:
            error_list.append(str(error))

def main():
    for key_word in keyword_list:
        try:
            print(key_word)
            get_page_content(key_word)
            df = pd.DataFrame(results)
            df.to_excel(out_excel_file, index=False)

        except Exception as error:
            error_list.append(str(error))

if __name__ == "__main__":
    main()