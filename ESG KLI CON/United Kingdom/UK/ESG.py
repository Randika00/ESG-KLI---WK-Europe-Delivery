import requests
import os
import re
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

def get_soup(url):
    global statusCode
    response = requests.get(url,headers=headers,stream=True)
    statusCode = response.status_code
    soup= BeautifulSoup(response.content, 'html.parser')
    return soup

def get_response_with_retry(url):
    response = requests.get(url, headers=headers)
    return response

def get_entry_dates(source_link):
    try:
        page_response = requests.get(source_link)
        page_response.raise_for_status()
        page_soup = BeautifulSoup(page_response.content, "html.parser")

        introductory_text = page_soup.find("a", string="Introductory Text")
        if introductory_text:
            all_li_tags = page_soup.findAll("li", class_="LegContentsEntry")
            for sin_link in all_li_tags:
                if "commencement" in sin_link.text.lower():
                    last_link = base_url+sin_link.a["href"]
                    last_soup = get_soup(last_link)
                    text = last_soup.findAll("span",class_="pointer")[-1].find_next_sibling("span").text if last_soup.findAll("span",class_="pointer") else ""
                    match = re.search(r'\d{2}/\d{2}/\d{4}', text)
                    if match:
                        entry_into_force_date = match.group()
                    else:
                        entry_into_force_date = ""

                    info = last_soup.find("div", class_="LegClearFix LegPrelims")
                    if info:
                        adoption_info = info.find("p")
                        if adoption_info:
                            text_content = adoption_info.get_text(strip=True)
                            if "received Royal Assent on" in text_content:
                                date_of_adoption = text_content.split("received Royal Assent on")[1].strip()
                            else:
                                date_of_adoption = ""
                        else:
                            date_of_adoption = ""
                    else:
                        date_of_adoption = ""
                    break
                else:
                    entry_into_force_date = date_of_adoption = ""
        else:
            entry_into_force_date = date_of_adoption = ""

        return entry_into_force_date, date_of_adoption

    except Exception as e:
        print(f"Error accessing {source_link}: {e}")

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Priority": "u=0, i",
    "Sec-Ch-Ua": "\"Not/A)Brand\";v=\"8\", \"Chromium\";v=\"126\", \"Google Chrome\";v=\"126\"",
    "Sec-Ch-Ua-Arch": "\"x86\"",
    "Sec-Ch-Ua-Bitness": "\"64\"",
    "Sec-Ch-Ua-Full-Version": "\"126.0.6478.127\"",
    "Sec-Ch-Ua-Full-Version-List": "\"Not/A)Brand\";v=\"8.0.0.0\", \"Chromium\";v=\"126.0.6478.127\", \"Google Chrome\";v=\"126.0.6478.127\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Model": "\"\"",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Sec-Ch-Ua-Platform-Version": "\"15.0.0\"",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

error_list = []

try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().split("\n")
except Exception as error:
    error_list.append(str(error))

statusCode = None
base_url = "https://www.legislation.gov.uk"
results = []
out_excel_file = os.path.join(os.getcwd(), "United_Kingdom.xlsx")

def main():
    for sin_key in keyword_list:
        try:
            data = []
            corrected_keyword = sin_key.replace(" ","%20")
            pre_link = f"https://www.legislation.gov.uk/ukpga+asp+aosp+aep+aip+apgb+nisi+apni+uksi+wsi+ssi+ukmd?title={corrected_keyword}"

            page_content = get_soup(pre_link)

            if not statusCode == 200:
                raise Exception(f"Site error encountered. Status code: {statusCode}")

            current_url = pre_link
            while True:
                previous_entry = None  # Store last full entry
                response = requests.get(current_url)
                print(f"Fetching data from : {current_url}")
                soup = BeautifulSoup(response.content, "html.parser")

                content_div = soup.find("div", id="content")
                if content_div:
                    table = content_div.select_one("table")
                    if table:
                        rows = table.select("tbody tr")
                        for row in rows:
                            cols = row.find_all("td")
                            if len(cols) >= 3:
                                a_tag = cols[0].find("a")
                                title = a_tag.get_text(strip=True).replace('\xa0', ' ') if a_tag else cols[0].get_text(
                                    strip=True)
                                link = urljoin(base_url, a_tag['href']) if a_tag and 'href' in a_tag.attrs else None
                                year_number = cols[1].get_text(strip=True).replace('\xa0', ' ')
                                legislation_type = cols[2].get_text(strip=True).replace('\xa0', ' ')

                                entry_into_force_date, date_of_adoption = get_entry_dates(link) if link else ("", "")

                                entry = {
                                    "Jurisdiction":"United Kingdom",
                                    "Original Title": title,
                                    "Type of Regulation": legislation_type,
                                    "Source": link,
                                    "Date of adoption": date_of_adoption,
                                    "Entry Into Force Date": entry_into_force_date,
                                }

                                results.append(entry)
                                print(entry)
                                previous_entry = entry  # Save for potential continuation

                            elif len(cols) == 1 and previous_entry:
                                # Continuation row (e.g., Welsh)
                                a_tag = cols[0].find("a")
                                title = a_tag.get_text(strip=True).replace('\xa0', ' ') if a_tag else cols[0].get_text(
                                    strip=True)
                                link = urljoin(base_url, a_tag['href']) if a_tag and 'href' in a_tag.attrs else None

                                entry_into_force_date, date_of_adoption = get_entry_dates(link) if link else ("", "")

                                entry = {
                                    "Jurisdiction": "United Kingdom",
                                    "Original Title": title,
                                    "Type of Regulation": previous_entry["Type of Regulation"],
                                    "Source": link,
                                    "Date of adoption": date_of_adoption,
                                    "Entry Into Force Date": entry_into_force_date,
                                }

                                results.append(entry)
                                print(entry)

                next_li = soup.find("li", class_="pageLink next")
                if next_li and next_li.a:
                    next_href = next_li.a['href']
                    current_url = urljoin(base_url, next_href)
                else:
                    break

        except Exception as error:
            error_list.append(error)

    df = pd.DataFrame(results)
    df.to_excel(out_excel_file, index=False)


if __name__ == "__main__":
    main()