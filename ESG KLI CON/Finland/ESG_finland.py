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

headers3 = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0"
}
def getSoup(url):
    response = requests.get(url,headers=headers3)
    return response

non_esg_keywords = [
    "muutos",         # amendment
    "määräraha",      # appropriation
    "kumottu",        # repealed
    "peruutettu",     # revoked
    "lentokenttä",    # airport
    "lentoyhtiö",     # airline
    "nimittäminen",   # appointment
    "nimitetty",      # appointed
    "budjetti",       # budget
    "kärsivällinen",  # patient
    "koronaviirus",   # coronavirus
    "COVID 19"        # COVID-19
]
results = []
error_list = []
completed_list =[]
completed_sources = []
regulation_mapping = {
    "Laki": "Law",
    "Valtioneuvoston asetus": "Decree",
    "Asetus": "Decree",
    "Päätös": "Decision",
    "HE": "Government proposal"
}
case_law_terms = ["KHO", "KKO", "MAO", "TT", "HAO", "HO", "VakO", "EIT"]
def get_soup(url, payload,retries=10, delay=3):
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers)

            if response.status_code == 200:
                return response.text
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

def get_with_soup(url,retries=10, delay=3):
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=get_headers)

            if response.status_code == 200:
                return BeautifulSoup(response.content,"html.parser")
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
    page_count = 1
    url_keyword = quote_plus(key_word)

    while True:
        url = f"https://www.finlex.fi/fi/haku?type=EXTENDED&exact=%22{url_keyword}%22&limit=50&sort=relevance&page={page_count}&keywords=%22{url_keyword}%22&language=fin"
        print(f"➡️ Main Link (Page {page_count}): {url}...")
        payload = [
            {
                "type": "EXTENDED",
                "sort": "relevance",
                "limit": 50,
                "exact": f"\"{key_word}\"",
                "category": "",
                "page": page_count,
                "number": "",
                "year": "",
                "dateIssuedFrom": "",
                "dateIssuedTo": "",
                "keywords": f"\"{key_word}\"",
                "language": "fin",
                "documentType": "",
                "administrativeBranch": "",
                "agreementPartyEmployee": "",
                "agreementPartyEmployer": "",
                "archivalRecord": "",
                "caseYear": "",
                "dateEntryIntoForce": "",
                "dateInForceEnd": "",
                "datePublished": "",
                "decisionNumber": "",
                "diaryNumber": "",
                "typeStatute": "",
                "state": "",
                "authorityRegulationOrganization": ""
            }
        ]

        content = get_soup(url, payload)

        pattern = r'1:\s*({.*})'

        match = re.search(pattern, content, re.DOTALL)

        if match:
            json_text = match.group(1)

            try:
                data = json.loads(json_text)
                related_data = data["hits"]["hits"]
                if not related_data:
                    break
                read_json(related_data)
                page_count +=1
            except json.JSONDecodeError as e:
                raise Exception("JSON decoding error")
        else:
            raise Exception("No JSON found after '1:'")


def data_extract(soup):

    h1_tag = soup.find('h1', class_="styles_title__DVElS styles_title__FvTRD styles_h1__NPKCR")
    h1_text = h1_tag.get_text(strip=True) if h1_tag else ""


    if re.search(r'[A-Za-z]', h1_text) and re.search(r'\d', h1_text):
        regulation_type = ""
        section_tag = soup.find('section', class_='styles_documentHeader__z6lG_')
        if not section_tag:
            # Section not found, return empty defaults
            return {
                "Original Title": "",
                "Type of Regulation": "",
                "Date of adoption": "",
                "Entry Into Force Date": "",
                "Source": ""
            }
        regulation_type = h1_text.split()[0]
        h1_text_last =h1_text.split()[1]
        title_div = section_tag.find('div', class_='styles_titleContainer__maCvk')
        if title_div:
            h2_tag = title_div.find('h2', class_='styles_description__0Zy03')
            if h2_tag:
                source_title = h2_tag.get_text(strip=True)
                title = f"{source_title} {h1_text}"
        else:
            title = h1_text

        # Map dt text to corresponding dd for easy access
        dt_tags = section_tag.find_all('dt')
        dd_tags = section_tag.find_all('dd')
        dt_dd_map = {dt.get_text(strip=True).lower(): dd for dt, dd in zip(dt_tags, dd_tags)}

        def extract_date(dd_tag):
            if not dd_tag:
                return ""
            time_tag = dd_tag.find('time')
            if not time_tag:
                return ""
            # Prefer datetime attribute
            datetime_attr = time_tag.get('datetime')
            if datetime_attr:
                return datetime_attr.strip()
            # fallback: parse text like "10.6.2022"
            raw_text = time_tag.get_text(strip=True)
            try:
                dt = datetime.strptime(raw_text, "%d.%m.%Y")
                return dt.strftime("%Y-%m-%d")
            except Exception:
                return ""

        date_of_adoption = extract_date(dt_dd_map.get('antopäivä'))
        entry_in_force_date = extract_date(dt_dd_map.get('julkaisupäivä'))

        # Extract source link
        source_link = ""
        ul_tag = soup.find('ul', class_='styles_breadCrumbsList__UOPLA')
        source_link = ""
        if ul_tag:
            li_tags = ul_tag.find_all('li')
            if li_tags:
                last_li = li_tags[-1]
                a_tag = last_li.find('a')
                if a_tag and a_tag.has_attr('href'):
                    source_link = f"https://www.finlex.fi{a_tag['href']}"

        # Return all extracted data
        return {
            "Original Title": title,
            "Type of Regulation": regulation_type,
            "Date of adoption": date_of_adoption,
            "Entry Into Force Date": entry_in_force_date,
            "Source": source_link
        }


    elif re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", h1_text):

        section_tag = soup.find('section', class_='styles_documentHeader__z6lG_')
        if not section_tag:
            # Section not found, return empty defaults
            return {
                "Original Title": "",
                "Type of Regulation": "",
                "Date of adoption": "",
                "Entry Into Force Date": "",
                "Source": ""
            }
        h2_tag = section_tag.find('h2', class_="styles_description__0Zy03")
        original_title = h2_tag.get_text(strip=True) if h2_tag else ""
        # regulation_type = original_title.split(":")[0] if ":" in original_title else ""
        match = re.match(r"^([A-Za-z]+)", original_title)
        regulation_type = match.group(1) if match else ""

        # Find <time> tag and get datetime attribute in yyyy-mm-dd format
        time_tag = section_tag.find('time')
        date_of_adoption = time_tag['datetime'] if time_tag and time_tag.has_attr('datetime') else ""


        ul_tag = soup.find('ul', class_='styles_breadCrumbsList__UOPLA')
        source_link = ""
        if ul_tag:
            li_tags = ul_tag.find_all('li')
            if li_tags:
                last_li = li_tags[-1]
                a_tag = last_li.find('a')
                if a_tag and a_tag.has_attr('href'):
                    source_link = f"https://www.finlex.fi{a_tag['href']}"
        return {
            "Original Title": original_title,
            "Type of Regulation": regulation_type,
            "Date of adoption": date_of_adoption,
            "Entry Into Force Date": "",
            "Source": source_link
        }



    else:
        section_tag = soup.find('section', class_='styles_documentHeader__z6lG_')
        if not section_tag:
            # Section not found, return empty defaults
            return {
                "Original Title": "",
                "Type of Regulation": "",
                "Date of adoption": "",
                "Entry Into Force Date": "",
                "Source": ""
            }


        authorial_note_div = section_tag.find('div', class_='styles_titleAuthorialNote__mYAra')
        if authorial_note_div:
            a_tag = authorial_note_div.find('a', href=True)
            if a_tag:
                authorial_note_href = a_tag['href']
                auth_link =f"https://www.finlex.fi/{authorial_note_href}"
                print(auth_link)
            auth_response = getSoup(auth_link)
            auth_soup = BeautifulSoup(auth_response.content, 'html.parser')
            h1_tag = auth_soup.find('h1', class_="styles_title__DVElS styles_title__FvTRD styles_h1__NPKCR")
            h1_text = h1_tag.get_text(strip=True) if h1_tag else ""
            auth_section_tag = auth_soup.find('section', class_='styles_documentHeader__z6lG_')

            source_title = ""
            title_div = auth_section_tag.find('div', class_='styles_titleContainer__maCvk')
            if title_div:
                h2_tag = title_div.find('h2', class_='styles_description__0Zy03')
                if h2_tag:
                    source_title = h2_tag.get_text(strip=True)
                    title = f"{source_title} {h1_text}"
            else:
                title = h1_text

            # Map dt text to corresponding dd for easy access
            dt_tags = auth_section_tag.find_all('dt')
            dd_tags = auth_section_tag.find_all('dd')
            dt_dd_map = {dt.get_text(strip=True).lower(): dd for dt, dd in zip(dt_tags, dd_tags)}

            # Extract regulation type
            regulation_type = ""
            if 'säädöksen tyyppi' in dt_dd_map:
                regulation_type = dt_dd_map['säädöksen tyyppi'].get_text(strip=True)

            # Helper to extract ISO date from <time> tag
            def extract_date(dd_tag):
                if not dd_tag:
                    return ""
                time_tag = dd_tag.find('time')
                if not time_tag:
                    return ""
                # Prefer datetime attribute
                datetime_attr = time_tag.get('datetime')
                if datetime_attr:
                    return datetime_attr.strip()
                # fallback: parse text like "10.6.2022"
                raw_text = time_tag.get_text(strip=True)
                try:
                    dt = datetime.strptime(raw_text, "%d.%m.%Y")
                    return dt.strftime("%Y-%m-%d")
                except Exception:
                    return ""

            date_of_adoption = extract_date(dt_dd_map.get('antopäivä'))
            entry_in_force_date = extract_date(dt_dd_map.get('julkaisupäivä'))

            # Extract source link
            source_link = ""
            if 'eli-tunnus' in dt_dd_map:
                span = dt_dd_map['eli-tunnus'].find('span', class_='styles_ecliText__3mM1K')
                if span:
                    source_link = span.get_text(strip=True)
            else:
                # Fallback
                for dt, dd in zip(dt_tags, dd_tags):
                    if "ajantasaistettu" in dt.get_text(strip=True).lower():
                        a_tag = dd.find('a', href=True)
                        if a_tag:
                            source_link = f"https://www.finlex.fi{a_tag['href'].strip()}"
                            break

            # Return all extracted data
            return {
                "Original Title": title,
                "Type of Regulation": regulation_type,
                "Date of adoption": date_of_adoption,
                "Entry Into Force Date": entry_in_force_date,
                "Source": source_link
            }


        else:
            h1_tag = soup.find('h1', class_="styles_title__DVElS styles_title__FvTRD styles_h1__NPKCR")
            h1_text = h1_tag.get_text(strip=True) if h1_tag else ""
            source_title = ""
            title_div = section_tag.find('div', class_='styles_titleContainer__maCvk')
            if title_div:
                h2_tag = title_div.find('h2', class_='styles_description__0Zy03')
                if h2_tag:
                    source_title = h2_tag.get_text(strip=True)
                    title = f"{source_title} {h1_text}"
            else:
                title = h1_text

            # Map dt text to corresponding dd for easy access
            dt_tags = section_tag.find_all('dt')
            dd_tags = section_tag.find_all('dd')
            dt_dd_map = {dt.get_text(strip=True).lower(): dd for dt, dd in zip(dt_tags, dd_tags)}

            # Extract regulation type
            regulation_type = ""
            if 'säädöksen tyyppi' in dt_dd_map:
                regulation_type = dt_dd_map['säädöksen tyyppi'].get_text(strip=True)

            # Helper to extract ISO date from <time> tag
            def extract_date(dd_tag):
                if not dd_tag:
                    return ""
                time_tag = dd_tag.find('time')
                if not time_tag:
                    return ""
                # Prefer datetime attribute
                datetime_attr = time_tag.get('datetime')
                if datetime_attr:
                    return datetime_attr.strip()
                # fallback: parse text like "10.6.2022"
                raw_text = time_tag.get_text(strip=True)
                try:
                    dt = datetime.strptime(raw_text, "%d.%m.%Y")
                    return dt.strftime("%Y-%m-%d")
                except Exception:
                    return ""

            date_of_adoption = extract_date(dt_dd_map.get('antopäivä'))
            entry_in_force_date = extract_date(dt_dd_map.get('julkaisupäivä'))

            # Extract source link
            source_link = ""
            if 'eli-tunnus' in dt_dd_map:
                span = dt_dd_map['eli-tunnus'].find('span', class_='styles_ecliText__3mM1K')
                if span:
                    source_link = span.get_text(strip=True)
            else:
                # Fallback
                for dt, dd in zip(dt_tags, dd_tags):
                    if "ajantasaistettu" in dt.get_text(strip=True).lower():
                        a_tag = dd.find('a', href=True)
                        if a_tag:
                            source_link = f"https://www.finlex.fi{a_tag['href'].strip()}"
                            break

            # Return all extracted data
            return {
                "Original Title": title,
                "Type of Regulation": regulation_type,
                "Date of adoption": date_of_adoption,
                "Entry Into Force Date": entry_in_force_date,
                "Source": source_link
            }


def get_english_text(text):
    translated_text = GoogleTranslator(source='fi', target='en').translate(text)
    return translated_text

def reg_maping(data):
    reg_type = data.get("Type of Regulation", "").strip()
    if reg_type in regulation_mapping:
        data["Type of Regulation"] = regulation_mapping[reg_type]
    elif any(term in reg_type for term in case_law_terms):
        data["Type of Regulation"] = "Case Law"

    return data["Type of Regulation"]


allowed_regulation_types = {"Law", "Decree", "Decision", "Government proposal", "Case Law"}


def final_output(data):
    title_lower = data["Original Title"].lower()
    regulation_type = reg_maping(data)

    if (data["Original Title"] not in completed_list
            and data["Source"] not in completed_sources
            and not any(keyword in title_lower for keyword in non_esg_keywords) and regulation_type in allowed_regulation_types
    ):
        english_title = get_english_text(data["Original Title"])
        data["English Translation"] = english_title
        data["Jurisdiction"] = "Finland"
        # print(data)

        preferred_order = [
            "Jurisdiction",
            "Original Title",
            "English Translation",
            "Type of Regulation",
            "Source",
            'Date of adoption',
            'Entry Into Force Date'
        ]

        ordered_data = {key: data.get(key, "") for key in preferred_order}
        for key in data:
            if key not in ordered_data:
                ordered_data[key] = data[key]

        print(ordered_data)
        results.append(ordered_data)
        completed_list.append(data["Original Title"])
        completed_sources.append(data["Source"])

def read_json(json_data):
    for sin in json_data:
        try:
            base_url = "https://www.finlex.fi"
            low_url = base_url+sin["_source"]["href"]
            print(low_url)
            response = getSoup(low_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            data = data_extract(soup)

            final_output(data)


        except Exception as error:
            error_list.append(f"{error}")


def get_next_action():
    pre_value = "3d65513f1dab5b062b88698e17ec5b7223daf510"
    try:
        main_url = "https://www.finlex.fi/en"
        main_content = get_with_soup(main_url)
        js_link = main_content.find_all("script")[16]
        last_part = js_link["src"]
        full_link = "https://www.finlex.fi"+last_part

        second_content = get_with_soup(full_link)
        last_soup = str(second_content)
        match = re.search(r'\$\)\("([^"]+)"\)', last_soup)
        if match:
            next_action = match.group(1)
        else:
            next_action = pre_value
    except Exception as error:
        next_action = pre_value

    return next_action

get_headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Priority": "u=0, i",
    "Sec-Ch-Ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "Sec-Ch-Ua-Arch": '"x86"',
    "Sec-Ch-Ua-Bitness": '"64"',
    "Sec-Ch-Ua-Full-Version": '"134.0.6998.89"',
    "Sec-Ch-Ua-Full-Version-List": '"Chromium";v="134.0.6998.89", "Not:A-Brand";v="24.0.0.0", "Google Chrome";v="134.0.6998.89"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Model": '""',
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Ch-Ua-Platform-Version": '"15.0.0"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

headers = {
    "accept": "text/x-component",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "content-length": "544",
    "content-type": "text/plain;charset=UTF-8",
    "next-action": get_next_action(),
    "origin": "https://www.finlex.fi",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}


out_excel_file = os.path.join(os.getcwd(), "Finland.xlsx")

try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().strip().splitlines()
except Exception as error:
    error_list.append(str(error))

def main():
    for key_word in keyword_list:
        try:
            get_page_content(key_word)
            df = pd.DataFrame(results)
            df.to_excel(out_excel_file, index=False)
        except Exception as error:
            error_list.append(str(error))



if __name__ == "__main__":
    main()