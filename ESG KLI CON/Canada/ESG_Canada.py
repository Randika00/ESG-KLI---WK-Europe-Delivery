import requests
import os
import re
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import quote_plus
from datetime import datetime

def get_soup(url):
    global statusCode
    response = requests.get(url,headers=headers,stream=True)
    statusCode = response.status_code
    soup= BeautifulSoup(response.content, 'html.parser')
    return soup

def get_correct_date(year,month,day):
    date_obj = datetime.strptime(f"{year}-{month}-{day}", "%Y-%B-%d")
    last_date = date_obj.strftime("%Y-%m-%d")
    return last_date

def get_entry_date(current_soup,adoption_date):
    if_entry = current_soup.find("div", class_="ReaderNote")
    if_entry1 = current_soup.find(lambda tag: tag.string == "Coming into Force")
    pattern = re.compile(r"(This Order|These Regulations) come[s]? into force on the day on which (it|they) (is|are) registered",re.IGNORECASE)
    if_entry2 = current_soup.find(lambda tag: tag.name == "p" and pattern.search(tag.get_text(strip=True)))

    if if_entry:
        if re.search(r"[A-Za-z]+\s*\d{1,2},\s*\d{4}", if_entry.get_text(strip=True)):
            month, day, year = re.search(r"([A-Za-z]+)\s*(\d{1,2}),\s*(\d{4})", if_entry.get_text(strip=True)).groups()
            entry_date = get_correct_date(year, month, day)
        elif if_entry1:
            if_entry1_1 = if_entry1.find_next(lambda tag: tag.name == "p" and re.search(r"come[s]?\s*into\s*force\s*on\s*[A-Za-z]+\s*\d{1,2},\s*\d{4}\.?", tag.get_text(strip=True),re.IGNORECASE))
            if if_entry1_1:
                pre_entry_date = if_entry1_1.get_text(strip=True)
                month, day, year = re.search(r"come[s]?\s*into\s*force\s*on\s*([A-Za-z]+)\s*(\d{1,2}),\s*(\d{4})",pre_entry_date).groups()
                entry_date = get_correct_date(year, month, day)
            elif if_entry2:
                entry_date = adoption_date
            else:
                entry_date = None
        elif if_entry2:
            entry_date = adoption_date
        else:
            entry_date = None

    elif if_entry1:
        if_entry1_1 = if_entry1.find_next(lambda tag: tag.name == "p" and re.search(r"come[s]?\s*into\s*force\s*on\s*[A-Za-z]+\s*\d{1,2},\s*\d{4}\.?",tag.get_text(strip=True), re.IGNORECASE))
        if if_entry1_1:
            pre_entry_date = if_entry1_1.get_text(strip=True)
            month, day, year = re.search(r"come[s]?\s*into\s*force\s*on\s*([A-Za-z]+)\s*(\d{1,2}),\s*(\d{4})",pre_entry_date).groups()
            entry_date = get_correct_date(year, month, day)
        elif if_entry2:
            entry_date = adoption_date
        else:
            entry_date = None

    elif if_entry2:
        entry_date = adoption_date

    else:
        entry_date = None

    return entry_date

def get_dates(current_link):
    adoption_date = entry_date = None
    if_enter = True
    current_soup = get_soup(current_link)

    p_tag = current_soup.find("p", class_="centered")
    if p_tag:
        span_tag = p_tag.find("span", class_="Repealed")
        if span_tag:
            return adoption_date,entry_date,False

    if_adoption1 = current_soup.find("p", string=re.compile(r"Registration\s*\d{4}-\d{1,2}-\d{1,2}"))
    if_adoption2 = current_soup.find("p", string=re.compile(r"Assented\s*to\s*\s*\d{4}-\d{1,2}-\d{1,2}"))
    if if_adoption1:
        pre_adop_date = current_soup.find("p", string=re.compile(r"Registration\s*\d{4}-\d{1,2}-\d{1,2}")).get_text(strip=True)
        adoption_date = re.search(r"Registration\s*(.*)", pre_adop_date).group(1)
        entry_date = get_entry_date(current_soup,adoption_date)
    elif if_adoption2:
        pre_adop_date = current_soup.find("p", string=re.compile(r"Assented\s*to\s*\s*\d{4}-\d{1,2}-\d{1,2}")).get_text(strip=True)
        adoption_date = re.search(r"Assented\s*to\s*\s*(.*)", pre_adop_date).group(1)
        entry_date = get_entry_date(current_soup, adoption_date)
    else:
        adoption_date = entry_date = None

    return adoption_date,entry_date,if_enter

def get_details(soup,key_word):
    all_articles = soup.find("ol",class_="wet-boew-zebra resultList").findAll("li",class_="resultType1")
    for sin_art in all_articles:
        try:
            title = re.sub(r"\s+"," ",sin_art.find("a",class_="hitTitleLink").get_text(strip=True))
            source_link = sin_art.find("a",class_="hitTitleLink")["href"]

            base_value = source_link.rsplit("/", 1)[0]
            full_link = f"{base_value}/FullText.html"
            reg_type = "Act" if "Act" in title else "Regulation"
            adoption_date,entry_date,if_enter = get_dates(full_link)

            entry = {
                "Jurisdiction": "Canada",
                "Original Title": title,
                "Type of Regulation": reg_type,
                "Source": source_link,
                "Date of adoption": adoption_date,
                "Entry Into Force Date": entry_date,
                "Remarks":key_word
            }
            if (if_enter and entry["Source"] not in completed_sources and entry["Original Title"] not in completed_list):
                print(entry)
                results.append(entry)
                completed_list.append(entry["Original Title"])
                completed_sources.append(entry["Source"])

        except Exception as error:
            error_list.append(str(error))

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

statusCode = None
base_url = "https://laws-lois.justice.gc.ca"
results = []
error_list = []
completed_list =[]
completed_sources = []
out_excel_file = os.path.join(os.getcwd(), "Canada.xlsx")

try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().strip().splitlines()
except Exception as error:
    error_list.append(str(error))

def main():
    for sin_key in keyword_list:
        try:
            encoded_keyword = quote_plus(sin_key)
            page_count = 1
            while True:
                main_link = f"https://laws-lois.justice.gc.ca/Search/Advanced.aspx?ddC0nt3ntTyp3=ActsRegs&txtS3arch3xact={encoded_keyword}&h1dd3nPag3Num={page_count}&h1ts0n1y=1"
                print("\n"+f"Main URL: {main_link}(Page:{page_count})"+"\n")
                main_soup = get_soup(main_link)
                get_details(main_soup,sin_key)
                if not main_soup.find("a",string = "Next Results Page"):
                    break
                page_count+=1

        except Exception as error:
            error_list.append(str(error))

    df = pd.DataFrame(results)
    df.to_excel(out_excel_file, index=False)

if __name__ == "__main__":
    main()