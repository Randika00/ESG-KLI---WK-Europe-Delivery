import requests
from bs4 import BeautifulSoup
from datetime import datetime
from deep_translator import GoogleTranslator
import pandas as pd
import time
import re

def get_english_text(text):
    translated_text = GoogleTranslator(source='nl', target='en').translate(text)
    return translated_text

keyword_list = []
results_data = [] 
error_list = []
completed_list = []
completed_link_list = []
non_esg_keywords = [
    "Wijziging","toe-eigening","begroting","etrokken","ingetrokken","luchthaven","luchtvaartmaatschappij","afspraak","benoemd","geduldig","coronavirus"
]

try:   
    with open('keyword_.txt', 'r', encoding='utf-8') as file: 
        keyword_list = file.read().strip().splitlines()
except Exception as error:    
    error_list.append(f"Error reading keyword file: {error}")

if error_list:
    print("Errors:", error_list)

if not keyword_list:
    print("No keywords found.")
else:
    for sin_key in keyword_list:   
        
        base_url = f"https://zoek.officielebekendmakingen.nl/resultaten?q=(c.product-area==%22officielepublicaties%22)and((dt.type==%22Beschikking%22)or(dt.type==%22Klein%20Koninklijk%20Besluit%22)or(dt.type==%22Wet%22))and(((w.publicatienaam==%22Tractatenblad%22))or((w.publicatienaam==%22Staatsblad%22))or((w.publicatienaam==%22Staatscourant%22))or((w.publicatienaam==%22Gemeenteblad%22))or((w.publicatienaam==%22Provinciaal%20blad%22))or((w.publicatienaam==%22Waterschapsblad%22))or((w.publicatienaam==%22Blad%20gemeenschappelijke%20regeling%22)))and(dt.title%20adj%20%22{sin_key}%22)&zv=%22{sin_key}%22&pg=50&col=AlleBekendmakingen&svel=Publicatiedatum&svol=Aflopend"
        
        print(f'ARTICLES RELATED TO THE: {sin_key}:\n')

        adding_string = "svel=Publicatiedatum&svol=Aflopend&pg=50&"

        try:
            first_url_re = requests.get(base_url)
            first_url_con = BeautifulSoup(first_url_re.content, 'html.parser')
        except Exception as error:
            error_list.append(f"Error requesting base URL for {sin_key}: {error}")
            continue

        if first_url_con:
            full_pagination_div = first_url_con.find("div", class_="pagination__index")
            if full_pagination_div:
                all_lis = full_pagination_div.find_all("li")
                if len(all_lis) >= 2:
                    li_before_last_li = all_lis[-2]
                    if li_before_last_li:
                        try:
                            count_as_string = li_before_last_li.get_text(strip=True)
                            count_as_int = int(count_as_string)
                        except Exception as error:
                            error_list.append(f"Error parsing pagination number: {error}")
                            count_as_int = 1
                    else:
                        print("li_before_last_li is not found")
                        error_list.append("li_before_last_li is None")
                        count_as_int = 1
                else:
                    print("Pagination list items not found or too short")
                    error_list.append("Pagination list too short")
                    count_as_int = 1
            else:
                count_as_int = 1

            link_list = []
            num = 1
            for i in range(0, count_as_int):
                if num == 1:
                    link_ = f'{base_url}'
                else:
                    insert_pos = base_url.find("resultaten?") + len("resultaten?")
                    if insert_pos:
                        modified_url_first = base_url[:insert_pos] + adding_string + base_url[insert_pos:]
                        if modified_url_first:
                            modified_url_second = modified_url_first.replace("pg=50&col=AlleBekendmakingen&svel=Publicatiedatum&svol=Aflopend", "")
                            if modified_url_second:
                                modified_url = modified_url_second + f"col=&pagina={num}"
                                if modified_url:
                                    link_ = f'{modified_url}'
                                else:
                                    print("Modified url not found")
                                    error_list.append("Final modified_url is None")
                                    link_ = ''
                            else:
                                print("Second_Modified_url not found") 
                                error_list.append("Second modified_url is None")
                                link_ = ''
                        else:
                            print("First_modified_url not found")
                            error_list.append("First modified_url is None")
                            link_ = ''
                    else:
                        print("insert_pos not found") 
                        error_list.append("Insert position not found in base_url")
                        link_ = ''

                if link_:
                    link_list.append(link_)
                num += 1

            for link_of_ in link_list:
                print(f"{link_of_}\n")
                try:
                    links_re = requests.get(link_of_)
                    links_con = BeautifulSoup(links_re.content, 'html.parser')
                except Exception as error:
                    print(f"Error fetching content for {link_of_}: {error}")
                    error_list.append(f"Request error for {link_of_}: {error}")
                    continue

                if links_con:
                    top_level_lis = links_con.select('#Publicaties > ul > li')

                    for top_li_of_ul in top_level_lis:

                        title_html_page = top_li_of_ul.find('a', class_="result--subtitle")
                        if title_html_page and title_html_page.has_attr('href'):
                            html_page_article = title_html_page['href']
                            url_of_main = "https://zoek.officielebekendmakingen.nl/"
                            source_link = url_of_main + html_page_article

                            if source_link:
                                try:
                                    article_url_re = requests.get(source_link)
                                    article_url_con = BeautifulSoup(article_url_re.content, 'html.parser')

                                    if article_url_con:
                                        try:
                                            original_title_DU_h1 = article_url_con.find("h1", class_="staatsblad_kop")
                                            if original_title_DU_h1:
                                                original_title_DU_h1 = article_url_con.find("h1", class_="staatsblad_kop").get_text()
                                            else:
                                                original_title_DU_h1 = article_url_con.find("td", attrs={"data-before":"Titel"}).get_text()
                                            original_title_DU = re.sub(r'\s+', ' ', original_title_DU_h1).strip()
                                        except Exception as error:
                                            original_title_DU = "Not found"
                                            error_list.append(f"Title not found: {str(error)}")

                                        try:
                                            original_title_DUC = get_english_text(original_title_DU)
                                            original_title_EN = original_title_DUC
                                        except Exception as error:
                                            original_title_EN = "Translation failed"
                                            error_list.append(f"Title translation error: {str(error)}")

                                        table_div = article_url_con.find("table", class_="table")
                                        if table_div:
                                            try:
                                                entry_into_force_site = table_div.find('td', attrs={'data-before': 'Datum publicatie'}).find('time').get_text(strip=True).split()[0]
                                                date_of_adoption_site = table_div.find('td', attrs={'data-before': 'Datum ondertekening'}).find('time').get_text(strip=True)

                                                entry_dt = datetime.strptime(entry_into_force_site, '%d-%m-%Y')
                                                adoption_dt = datetime.strptime(date_of_adoption_site, '%d-%m-%Y')

                                                entry_into_force = entry_dt.strftime('%Y-%m-%d')
                                                date_of_adoption = adoption_dt.strftime('%Y-%m-%d')
                                            except Exception as error:
                                                entry_into_force = "Not found"
                                                date_of_adoption = "Not found"
                                                error_list.append(f"Date parsing error: {str(error)}")

                                            try:
                                                type_of_regulation_DU = table_div.find('td', attrs={'data-before': 'Rubriek'}).get_text(strip=True)
                                                type_of_regulation_EN = get_english_text(type_of_regulation_DU)
                                                type_of_regulation_ENG = type_of_regulation_EN
                                            except Exception as error:
                                                type_of_regulation_ENG = "Translation failed"
                                                error_list.append(f"Regulation type translation error: {str(error)}")

                                        else:
                                            entry_into_force = "Not found"
                                            date_of_adoption = "Not found"
                                            type_of_regulation_ENG = "Not found"
                                            error_list.append("Table div not found")
                                    else:
                                        error_list.append("Article URL content parsing failed")

                                except Exception as error:
                                    error_list.append(f"Request or parsing error for source link: {str(error)}")
                            else:
                                error_list.append("Source link is empty or invalid")
                        else:
                            error_list.append("Title or href not found")

                        print(f'Dutch TITLE: {original_title_DU}\nEnglish TITLE: {original_title_EN}\nSource Link: {source_link}\nType of regulation: {type_of_regulation_ENG}\nEntry into force: {entry_into_force}\nDate of adoption: {date_of_adoption}\nKEYWORD:{sin_key}\n')

                        entry = {
                                "Jurisdiction": 'Netherland',
                                "Original Title": original_title_DU,
                                "English Translation": original_title_EN,
                                "Source": source_link,
                                "Type of Regulation": type_of_regulation_ENG,
                                "Date of Adoption": date_of_adoption,
                                "Entry Into Force": entry_into_force,
                                "Remarks": sin_key 
                            }
 
                        title_lower = entry["Original Title"].lower()
 
                        if ( entry["Original Title"] not in completed_list
                                and entry["Source"] not in completed_link_list
                                and not any(keyword.lower() in title_lower for keyword in non_esg_keywords)
                        ):
                            results_data.append(entry)
                            completed_list.append(entry["Original Title"])
                            completed_link_list.append(entry["Source"])

                else:
                    print("Link's content not parsed properly")
                    error_list.append(f"BeautifulSoup parse failed for {link_of_}")
        else:
            print("First URL connection not successful")
            error_list.append(f"Initial connection failed for keyword: {sin_key}")

        if results_data:
            df = pd.DataFrame(results_data)
            df.to_excel(f"Netherland_related_out.xlsx", index=False, engine='openpyxl')
            print("Netherland Spec Results saved to 'official_publications.xlsx'")
        else:
            print("No results to save.")
