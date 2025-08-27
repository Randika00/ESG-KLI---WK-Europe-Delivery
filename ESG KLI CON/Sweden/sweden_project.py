import urllib.parse
from bs4 import BeautifulSoup
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from deep_translator import GoogleTranslator
import pandas as pd
import time
import re

error_list = []
results_data = []
completed_list = []
completed_link_list = []


def get_english_text(text):
    try:
        translated_text = GoogleTranslator(source='sv', target='en').translate(text)
        return translated_text
    except Exception as e:
        msg = f"Translation error for text '{text}': {e}"
        error_list.append(msg)
        return text

def url_response(base_link):
    try:
        base_url_re = requests.get(base_link)
        base_url_re.raise_for_status()
        return BeautifulSoup(base_url_re.content, 'html.parser')
    except Exception as e:
        error_msg = f"Error fetching URL: {base_link} => {e}"
        print(error_msg)
        error_list.append(error_msg)
        return None

def custom_text_to_hex(text):
    try:
        text_with_plus = text.replace(" ", "+")
        encoded = urllib.parse.quote(text_with_plus, safe='+')
        return f"%22{encoded}%22"
    except Exception as e:
        msg = f"Encoding error for text '{text}': {e}"
        error_list.append(msg)
        return "%22%22"

try:
    with open('key_word.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().strip().splitlines()
except Exception as error:
    msg = f"Error reading keyword file: {error}"
    error_list.append(msg)
    keyword_list = []

if error_list:
    print("Errors:", error_list)

if not keyword_list:
    print("No keywords found.")
else:
    for sin_key in keyword_list:
        print(f"{sin_key}'s Details")
        list_of_links_each_key = []
        list_of_articles = []

        normal_input = f"{sin_key}"
        hex_output = custom_text_to_hex(normal_input)

        base_url = f"https://rkrattsbaser.gov.se/sfst/adv?fritext=&sbet=&rub={hex_output}&org="
        base_url_con = url_response(base_url)
        if base_url_con:
            # Find the parent div
            search_opt_div = base_url_con.find('div', class_='search-opt-pages')
            if search_opt_div:
                search_pages = search_opt_div.find_all('div', class_='search-page')
                search_pages_count = len(search_pages)
            else:
                search_pages_count = 0    
             
            count = 0
            correct_search_page_count = search_pages_count + 1
            for rep in range(correct_search_page_count):
                if count == 0:
                    list_of_links_each_key.append(f"{base_url}")
                elif count > 1:
                    if count == correct_search_page_count-1:
                        last_link = f"{base_url}&page={count}"

                        # print(f"Last:{count} :{base_url}&page={count}\n")
                        last_link_con = url_response(last_link)
                        if last_link_con:
                            search_hits_div = last_link_con.find('div', class_='search-hits')

                            if search_hits_div:
                                # Find all <strong> elements inside it
                                strong_tags = search_hits_div.find_all('strong')

                                if len(strong_tags) >= 2:
                                    value1 = strong_tags[0].get_text(strip=True)
                                    value2 = strong_tags[1].get_text(strip=True)

                                    if value1 == value2:
                                        print(last_link)
                                        source_link = last_link
                                        if source_link:
                                            source_link_con = url_response(source_link)
                                            if source_link_con:
                                                full_meta_div = source_link_con.find("div", class_="search-results-content")
                                                if full_meta_div:
                                                    all_meta_fields = full_meta_div.find_all("div", class_="result-inner-box")
                                                    if len(all_meta_fields) > 1:
                                                        title_div = all_meta_fields[1]
                                                        original_title = re.sub(r'\s+', ' ', title_div.get_text(strip=True)) if title_div else None
                                                        if original_title:
                                                            translated_title = get_english_text(original_title)
                                                            regulation_types = ['lag', 'förordning', 'kungörelse']
                                                            lower_title = original_title.lower()
                                                            for reg_type in regulation_types:
                                                                if reg_type in lower_title:
                                                                    regulation_type_ = reg_type.capitalize()
                                                                    regulation_type = get_english_text(regulation_type_)
                                                                    break
                                                    else:
                                                        original_title = None

                                                    for div_ in all_meta_fields:
                                                        if 'Utfärdad:' in div_.get_text(strip=True):
                                                            d_o_a = div_.get_text(strip=True).replace('Utfärdad:', '').strip()
                                                            if d_o_a:
                                                                entry_doa = datetime.strptime(d_o_a, '%Y-%m-%d')
                                                                date_of_adoption = entry_doa.strftime('%Y-%m-%d')
                                                            break

                                                    for div_ in all_meta_fields:
                                                        if 'Ikraft:' in div_.get_text(strip=True):
                                                            e_i_f_d = div_.get_text(strip=True).replace('Ikraft:', '').strip()
                                                            if e_i_f_d:
                                                                entry_dt = datetime.strptime(e_i_f_d, '%Y-%m-%d')
                                                                entry_into_force_date = entry_dt.strftime('%Y-%m-%d')
                                                            break
                                                        else:
                                                            entry_into_force_date = None

                                                    for div_ in all_meta_fields:
                                                        if 'Upphävd:' in div_.get_text(strip=True):
                                                            upphaved = div_.get_text(strip=True).replace('Upphävd:', '').strip()
                                                            break
                                                        else:
                                                            upphaved = None
                                                            
                                                    print(f"TITLE: {original_title}\nTranslated TITLE: {translated_title}\nREG Type: {regulation_type}\nSOURCE LINK: {source_link}\nDOA: {date_of_adoption}\nEIFD: {entry_into_force_date}\nKEY_WORD: {sin_key}\nUpphävd(True=?To Remove): {upphaved}\n")
                                                else:
                                                    msg = "Meta content 'search-results-content' not found in source_link"
                                                    print(msg)
                                                    error_list.append(msg)
                                            else:
                                                msg = "Failed to get content from source_link"
                                                print(msg)
                                                error_list.append(msg)
                                        else:
                                            msg = "source_link not found"
                                            print(msg)
                                            error_list.append(msg)

                                        list_of_articles.append({
                                            "Jurisdiction":'Sweden',
                                            "Original Title": original_title,
                                            "English Translation": translated_title,
                                            "Type of Regulation": regulation_type,
                                            "Source": source_link,
                                            "Date Of Adoption": date_of_adoption,
                                            "Entry Into Force Date": entry_into_force_date,
                                            "Remarks":sin_key,
                                            "PAGE_LINK": last_link,
                                            "Upphävd": upphaved

                                        })    
                                    else:
                                        list_of_links_each_key.append(f"{base_url}&page={count}")
                                        
                                else:
                                    print("Less than 2 <strong> tags found.")
                                    list_of_links_each_key.append(f"{base_url}&page={count}")
                            else:
                                print("<div class='search-hits'> not found.")
                                list_of_links_each_key.append(f"{base_url}&page={count}")
                    else:    
                        list_of_links_each_key.append(f"{base_url}&page={count}")
                    
                count += 1
            for links_in_link_list in list_of_links_each_key:
                print(f"{links_in_link_list}\n")
                if links_in_link_list:
                    base_url_con = url_response(links_in_link_list)
                    if base_url_con:
                        all_articles_container = base_url_con.find("div", class_="search-results-content")
                        if all_articles_container:
                            try:
                                all_articles_assigner = all_articles_container.find_all("div", class_="search-hit-info")

                                if not all_articles_assigner:
                                    msg = f"No articles found for keyword: {sin_key}"
                                    print(msg)
                                    error_list.append(msg)

                                for articles_wise in all_articles_assigner:
                                    a_in_title_tag = articles_wise.find("div", class_="search-hit-info-header")
                                    if a_in_title_tag:
                                        a_tag_for_title = a_in_title_tag.find('a')
                                        if a_tag_for_title and a_tag_for_title.has_attr('href'):
                                            try:
                                                article_link_inc = a_tag_for_title['href']
                                                article_link = urljoin(base_url, article_link_inc)

                                                if article_link:
                                                    article_link_con = url_response(article_link)
                                                    visa_register_link = source_link = original_title = translated_title = regulation_type = date_of_adoption = entry_into_force_date = upphaved = None

                                                    if article_link_con:
                                                        visa_register_div = article_link_con.find("div", class_="result-inner-box bold")
                                                        if visa_register_div:
                                                            visa_register_a = visa_register_div.find('a')
                                                            if visa_register_a and visa_register_a.has_attr('href'):
                                                                visa_register_link_inc = visa_register_a['href']
                                                                visa_register_link = urljoin(article_link, visa_register_link_inc)
                                                                if visa_register_link:
                                                                    visa_register_link_con = url_response(visa_register_link)
                                                                    if visa_register_link_con:
                                                                        visa_fulltext_div = visa_register_link_con.find("div", class_="result-inner-box bold")
                                                                        if visa_fulltext_div:
                                                                            visa_fulltext_a = visa_fulltext_div.find('a')
                                                                            if visa_fulltext_a and visa_fulltext_a.has_attr('href'):
                                                                                visa_fulltext_link_inc = visa_fulltext_a['href']
                                                                                source_link = urljoin(article_link, visa_fulltext_link_inc)
                                                                                if source_link:
                                                                                    source_link_con = url_response(source_link)
                                                                                    if source_link_con:
                                                                                        full_meta_div = source_link_con.find("div", class_="search-results-content")
                                                                                        if full_meta_div:
                                                                                            all_meta_fields = full_meta_div.find_all("div", class_="result-inner-box")
                                                                                            if len(all_meta_fields) > 1:
                                                                                                title_div = all_meta_fields[1]
                                                                                                original_title = re.sub(r'\s+', ' ', title_div.get_text(strip=True)) if title_div else None
                                                                                                if original_title:
                                                                                                    translated_title = get_english_text(original_title)
                                                                                                    regulation_types = ['lag', 'förordning', 'kungörelse']
                                                                                                    lower_title = original_title.lower()
                                                                                                    for reg_type in regulation_types:
                                                                                                        if reg_type in lower_title:
                                                                                                            regulation_type_ = reg_type.capitalize()
                                                                                                            regulation_type = get_english_text(regulation_type_)
                                                                                                            break
                                                                                            else:
                                                                                                original_title = None

                                                                                            for div_ in all_meta_fields:
                                                                                                if 'Utfärdad:' in div_.get_text(strip=True):
                                                                                                    d_o_a = div_.get_text(strip=True).replace('Utfärdad:', '').strip()
                                                                                                    if d_o_a:
                                                                                                        entry_doa = datetime.strptime(d_o_a, '%Y-%m-%d')
                                                                                                        date_of_adoption = entry_doa.strftime('%Y-%m-%d')
                                                                                                    break

                                                                                            for div_ in all_meta_fields:
                                                                                                if 'Ikraft:' in div_.get_text(strip=True):
                                                                                                    e_i_f_d = div_.get_text(strip=True).replace('Ikraft:', '').strip()
                                                                                                    if e_i_f_d:
                                                                                                        entry_dt = datetime.strptime(e_i_f_d, '%Y-%m-%d')
                                                                                                        entry_into_force_date = entry_dt.strftime('%Y-%m-%d')
                                                                                                    break

                                                                                            for div_ in all_meta_fields:
                                                                                                if 'Upphävd:' in div_.get_text(strip=True):
                                                                                                    upphaved = div_.get_text(strip=True).replace('Upphävd:', '').strip()
                                                                                                    break

                                                                                            print(f"TITLE: {original_title}\nTranslated TITLE: {translated_title}\nREG Type: {regulation_type}\nSOURCE LINK: {source_link}\nDOA: {date_of_adoption}\nEIFD: {entry_into_force_date}\nKEY_WORD: {sin_key}\nUpphävd(True=?To Remove): {upphaved}\n")
                                                                                        else:
                                                                                            msg = "Meta content 'search-results-content' not found in source_link"
                                                                                            print(msg)
                                                                                            error_list.append(msg)
                                                                                    else:
                                                                                        msg = "Failed to get content from source_link"
                                                                                        print(msg)
                                                                                        error_list.append(msg)
                                                                                else:
                                                                                    msg = "source_link not found"
                                                                                    print(msg)
                                                                                    error_list.append(msg)
                                                                            else:
                                                                                msg = "visa_fulltext <a> tag with href not found"
                                                                                print(msg)
                                                                                error_list.append(msg)
                                                                        else:
                                                                            msg = "visa_fulltext_div not found"
                                                                            print(msg)
                                                                            error_list.append(msg)
                                                                    else:
                                                                        msg = "visa_register_link_con not found"
                                                                        print(msg)
                                                                        error_list.append(msg)
                                                                else:
                                                                    msg = "visa_register_link not formed"
                                                                    print(msg)
                                                                    error_list.append(msg)
                                                            else:
                                                                msg = "visa_register <a> tag with href not found"
                                                                print(msg)
                                                                error_list.append(msg)
                                                        else:
                                                            msg = "visa_register_div not found"
                                                            print(msg)
                                                            error_list.append(msg)
                                                    else:
                                                        msg = "article_link_con not found"
                                                        print(msg)
                                                        error_list.append(msg)
                                                else:
                                                    msg = "article_link not formed"
                                                    print(msg)
                                                    error_list.append(msg)

                                                list_of_articles.append({
                                                    "Jurisdiction":'Sweden',
                                                    "Original Title": original_title,
                                                    "English Translation": translated_title,
                                                    "Type of Regulation": regulation_type,
                                                    "Source": source_link,
                                                    "Date Of Adoption": date_of_adoption,
                                                    "Entry Into Force Date": entry_into_force_date,
                                                    "Remarks":sin_key,
                                                    "PAGE_LINK": links_in_link_list,
                                                    "Upphävd": upphaved
                                                })
                                            except Exception as ex:
                                                msg = f"Exception processing article link: {ex}"
                                                print(msg)
                                                error_list.append(msg)
                                        else:
                                            msg = "Article <a> tag with href not found in title section"
                                            print(msg)
                                            error_list.append(msg)
                                    else:
                                        msg = "Title div not found inside article block"
                                        print(msg)
                                        error_list.append(msg)

                            except Exception as e:
                                msg = f"No content for keyword '{sin_key}': {e}\n"
                                print(msg)
                                error_list.append(msg)
                        else:
                            msg = f"'search-results-content' not found for keyword: {sin_key}\n"
                            print(msg)
                            error_list.append(msg)
                    else:
                        msg = f"Failed to parse base URL for keyword: {sin_key}\n"
                        print(msg)
                        error_list.append(msg)
                else:
                    msg = f"Base URL not generated properly for keyword: {sin_key}\n"
                    print(msg)
                    error_list.append(msg)

        include_article_list = []
        exclude_article_list = []

        non_esg_keywords = ["ändring","anslag","upphävd","återkallas","flygplats","flygbolag","utsedd","utnämning","Budget","Patient","coronavirus","COVID-19"]
        for extracted_articles in list_of_articles:
            if extracted_articles.get("Upphävd") is None:
                include_article_list.append(extracted_articles)
            else:
                exclude_article_list.append(extracted_articles)

        for included_articles in include_article_list:
            try:
                title_lower = included_articles["Original Title"].lower()
                if (
                    included_articles["Original Title"] not in completed_list
                    and included_articles["Source"] not in completed_link_list
                    and not any(keyword.lower() in title_lower for keyword in non_esg_keywords)
                ):
                    results_data.append(included_articles)
                    completed_list.append(included_articles["Original Title"])
                    completed_link_list.append(included_articles["Source"])
            except Exception as e:
                msg = f"Error filtering included articles: {e}"
                print(msg)
                error_list.append(msg)

        # for results in results_data:
        #     print(f"{results}\n")

        try:
            if results_data:
                df = pd.DataFrame(results_data)
                df.to_excel(f"Sweden_related_out.xlsx", index=False, engine='openpyxl')
                print(f"{sin_key}'s Results saved to 'Sweden_related_out.xlsx'")
            else:
                print(f"No results to save.\n")
        except Exception as e:
            msg = f"Error saving Excel file: {e}"
            print(msg)
            error_list.append(msg)

# Final summary of errors
if error_list:
    print("\nSUMMARY OF ERRORS:")
    for err in error_list:
        print(f"- {err}")

                