import cloudscraper
from bs4 import BeautifulSoup
import re
import os
import certifi
import pandas as pd
from urllib.parse import quote
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

scraper = cloudscraper.create_scraper()

def get_soup(url):
    response = scraper.get(url, headers=headers1, verify=certifi.where())
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

headers1 = {
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

error_list = []
data = []
base_url = "https://www.legifrance.gouv.fr"
out_excel_file = os.path.join(os.getcwd(), "France.xlsx")

try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().split("\n")
except Exception as error:
    error_list.append(str(error))

def main():
    for sin_key in keyword_list:
        try:
            encoded_keyword = quote(sin_key)
            encoded_url_1 = f"https://www.legifrance.gouv.fr/search/lois?tab_selection=lawarticledecree&query=%7B(%40TITLE%5Bt%22{encoded_keyword}%22%5D)%7D&nature=LOI&nature=ORDONNANCE&nature=DECRET&nature=ARRETE&nature=DECRET_LOI&etatTexte=VIGUEUR&etatTexte=ABROGE_DIFF&etatArticle=VIGUEUR&etatArticle=ABROGE_DIFF&isAdvancedResult=true&sortValue=SIGNATURE_DATE_DESC&pageSize=10&typeRecherche=etat&page=1"
            encoded_url_2 = f"https://www.legifrance.gouv.fr/search/jorf?tab_selection=jorf&query=%7B(%40TITLE%5Bt%22{encoded_keyword}%22%5D)%7D&nature=mVucbw%3D%3D&nature=1Q6KYg%3D%3D&nature=QZ3O1g%3D%3D&nature=3M-Rcg%3D%3D&nature=o_ZqUg%3D%3D&nature=AIl5ag%3D%3D&isAdvancedResult=true&sortValue=SIGNATURE_DATE_DESC&pageSize=10&typeRecherche=date&init=true&page=1"
            encoded_url_3 = f"https://www.legifrance.gouv.fr/search/circ?tab_selection=circ&query=%7B(%40TITLE%5Bt%22{encoded_keyword}%22%5D)%7D&isAdvancedResult=true&sortValue=SIGNATURE_DATE_DESC&pageSize=10&typeRecherche=date&init=true&page=1"
            encoded_url_4 = f"https://www.legifrance.gouv.fr/search/constit?tab_selection=constit&query=%7B(%40TITLE%5Bt%22{encoded_keyword}%22%5D)%7D&isAdvancedResult=true&sortValue=DATE_DESC&pageSize=10&typeRecherche=date&init=true&page=1"
            link_list = [encoded_url_1, encoded_url_2, encoded_url_3, encoded_url_4]
            for sin_url in link_list:
                soup = get_soup(sin_url)

                try:
                    pager_items = soup.find_all("li", class_="pager-item")[-1]
                    a_tag = pager_items.find("a")
                    if a_tag and a_tag.text.strip().isdigit():
                        last_page = int(a_tag.text.strip())
                        # print(last_page)
                    else:
                        last_page = 1
                except Exception:
                    continue

                parsed_url = urlparse(sin_url)
                query_params = parse_qs(parsed_url.query)

                for page in range(1, last_page + 1):
                    query_params['page'] = [str(page)]
                    new_query = urlencode(query_params, doseq=True)
                    new_url = urlunparse(parsed_url._replace(query=new_query))
                    print(new_url)
                    c_response = scraper.get(new_url, headers=headers1, verify=certifi.where())
                    c_soup = BeautifulSoup(c_response.content, 'html.parser')
                    # print(c_soup.prettify())
                    artis = c_soup.find_all("article", class_="result-item")
                    for arti in artis:
                        h2 = arti.find("h2", class_="title-result-item")
                        if h2:
                            a_tag = h2.find("a")
                            if a_tag:
                                title = a_tag.get_text(strip=True)
                                href = a_tag.get("href")
                                full_url = base_url + href if href.startswith("/") else href
                                print("Title:", title)
                                print("Link:", full_url)
                                # pattern = r"^(?P<type>\w+) du (?P<date>\d{1,2} \w+ \d{4})"
                                pattern = r"^(?P<type>.+?) du (?P<date>\d{1,2} \w+ \d{4})"

                                match = re.search(pattern, title)
                                if match:
                                    regulation_type = match.group("type")
                                    adoption_date = match.group("date")
                                    print("Type of Regulation:", regulation_type)
                                    print("Date of Adoption:", adoption_date)
                                else:
                                    adoption_date = regulation_type = None
                                    print("No match found.")
                            else:
                                title = full_url = regulation_type = adoption_date = None
                        else:
                            title = full_url = regulation_type = adoption_date = None

                        a_response = scraper.get(full_url, headers=headers1, verify=certifi.where())
                        a_soup = BeautifulSoup(a_response.content, 'html.parser')
                        # print(a_soup.prettify())
                        p_tag = a_soup.find("p", class_="info word-break-all")
                        if p_tag:
                            match = re.search(r"du (\d{1,2} \w+ \d{4})", p_tag.get_text(strip=True))
                            if match:
                                entry_date = match.group(1)
                                print("Entry into Force Date:", entry_date)
                            else:
                                entry_date = None
                        else:
                            ul_tag = a_soup.find('ul', class_='links-init-version')
                            if ul_tag:
                                a_tag = ul_tag.find('a')
                                if a_tag and 'href' in a_tag.attrs:
                                    j_href = a_tag['href']
                                    j_url = base_url + j_href
                                    j_response = scraper.get(j_url, headers=headers1, verify=certifi.where())
                                    j_soup = BeautifulSoup(j_response.content, 'html.parser')
                                    span_tag = j_soup.find('span', class_='word-break-all')
                                    if span_tag:
                                        text = span_tag.get_text(strip=True)
                                        # Extract date using regex
                                        match = re.search(r'JORF du (\d{1,2} \w+ \d{4})', text)
                                        if match:
                                            entry_date = match.group(1)
                                            print("Entry into Force Date:", entry_date)
                                        else:
                                            entry_date = None
                                            print("Date not found in span text.")
                                    else:
                                        entry_date = None
                                        print("Span tag not found.")
                                else:
                                    entry_date = None
                                    print("No <a> tag or href found.")
                            else:
                                entry_date = None
                                print("No <ul> with class 'links-init-version' found.")

                        print("---")
                        # break
                        entry = {
                            "Jurisdiction":"France",
                            "Original Title": title,
                            "Type of Regulation": regulation_type,
                            "Source": full_url,
                            "Date of adoption": adoption_date,
                            "Entry Into Force Date": entry_date,
                        }
                        data.append(entry)
                    # break
            df = pd.DataFrame(data)
            df.to_excel(out_excel_file, index=False)
        except Exception as error:
            error_list.append(str(error))

if __name__ == "__main__":
    main()