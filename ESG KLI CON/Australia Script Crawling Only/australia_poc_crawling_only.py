import re
import sys
import time
import traceback
from bs4 import BeautifulSoup
import openpyxl
from openpyxl import Workbook
import requests
import json
import urllib.parse
from scraped_Data_Manager import ScrapedDataManager
from datetime import datetime
import os
import configparser
import random

session = requests.Session()
config = configparser.ConfigParser()

def clean_filename(text):

    cleaned_text = re.sub(r'[<>:"/\\|?*\']', '_', text)
    cleaned_text = cleaned_text.replace(' ', '_')
    max_length = 255  
    cleaned_text = cleaned_text[:max_length]
    cleaned_text = cleaned_text.strip('_')

    return cleaned_text


def format_effective_date(text):
    formatted_date = ""
    # Handle the effective date format
    dt = datetime.fromisoformat(text)

# Extract date in yyyy-mm-dd format
    formatted_date = dt.strftime('%Y-%m-%d')
    return formatted_date

def format_date(text):
    formatted_date = ""
    dt = datetime.fromisoformat(text)

# Extract date in yyyy-mm-dd format
    formatted_date = dt.strftime('%Y-%m-%d')

    return formatted_date

def read_search_items(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            search_items = [line.strip() for line in file if line.strip()]
        return search_items
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return []


def make_request_with_retry(session, url):
    response = ''
    retries = 3
    timeout = 40
    stat_code = 0
    trace_bck = ''
    
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=timeout, impersonate="chrome")
            # If the request was successful, return the response
            if response.status_code == 200:
                return response, response.status_code, trace_bck
            else:
                stat_code = response.status_code
        except:
            trace_bck = traceback.format_exc()
        
        print(f"Request Exeption. Retrying in 3 seconds... (Attempt {attempt + 1}/{retries})")
        time.sleep(3)    

    return response, stat_code, trace_bck

def check_keywords_in_text(text, keywords):
    """Check if any of the keywords are in the given text using regex."""
    text = text.upper()
    pattern = re.compile('|'.join(map(re.escape, keywords)), re.IGNORECASE)
    found_keywords = pattern.findall(text)
    return list(set(found_keywords))

def scraping_process(encoded_search_term, skip_numbers):
    url = f'https://api.prod.legislation.gov.au/v1/titles/search(criteria=\'and(text(%22{encoded_search_term}%22,nameAndText,contains),status(InForce),pointintime(Latest),collection(LegislativeInstrument,NotifiableInstrument,Act))\')?$select=administeringDepartments,collection,hasCommencedUnincorporatedAmendments,id,isInForce,isPrincipal,name,number,optionalSeriesNumber,searchContexts,seriesType,subCollection,year&$expand=administeringDepartments,searchContexts($expand=fullTextVersion,text)&$orderby=searchcontexts/text/relevance%20desc&$count=true&$top=100&$skip={skip_numbers}'

    session.headers.update( {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.6',
        'cache-control': 'no-cache',
        'origin': 'https://www.legislation.gov.au',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://www.legislation.gov.au/',
        'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Brave";v="132"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
    })

    # Send the request
    response = session.get(url)

    # Check for successful response
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        # print(data)
        odata_count = data.get('@odata.count', None) # This is the total count of the result items and will be used as pagination
        print("ODATA Count: ", odata_count)
        
        # Extract and print the required fields
        for index, item in enumerate(data.get("value", [])):
            

            id = item.get("id")
            name = item.get("name")

            found = check_keywords_in_text(name, exclude_keywords)
            if found:
                print(f'Exclusion Keywords found "{found}" not capturing....')
                continue
            else:
                print("No exclusion keywords found.")

            collection = item.get("collection")
            search_contexts = item.get("searchContexts", {})
            full_text_version = search_contexts.get("fullTextVersion", {})
            is_as_made = full_text_version.get("isAsMade")
            is_latest = full_text_version.get("isLatest")
            collection = re.sub(r'([a-z])([A-Z])', r'\1 \2', collection)
            registered_at = full_text_version.get("registeredAt")
            retrospective_start = full_text_version.get("retrospectiveStart")
            print(f"ID: {id}")
            print(f"Name: {name}")
            print(f"Collection: {collection}")
            # print(f"IsAsMade: {is_as_made}")
            # print(f"IsLatest: {is_latest}")
            # print(f"Adopt Date: {registered_at}")
            print(f"Effective Date: {retrospective_start}")

            
            # Convert registeredAt to YYYY-MM-DD format
            if is_as_made and is_latest:
                current_rec_status = 'asmade'
            elif is_latest and is_as_made == False:
                current_rec_status = 'latest'


            adopt_formatted_date = format_date(str(registered_at))
            retro_formatted_date = format_effective_date(str(retrospective_start))
            source_page_text_url = f"https://www.legislation.gov.au/{id}/{current_rec_status}/text"
            

            source_url_download_page = f"https://www.legislation.gov.au/{id}/{current_rec_status}/downloads"
            # print("Source Download Page:",source_url_download_page)
            print("-" * 40)
            print(f"Checking in the logs for: {source_page_text_url}")
            if not scrapedData_manager.is_already_scraped(source_page_text_url):
                
                # sleep every 10 urls crawled
                if index % 10 == 0 and index != 0:
                    time.sleep(random.randint(10, 15))
                    pass

                source_url_response = session.get(source_url_download_page)
            
                if source_url_response.status_code == 200:
                    # print(source_url_response.text)
                    soup = BeautifulSoup(source_url_response.text, "html.parser")
                    doc_icon = soup.find("frl-document-icon", attrs={"format": "pdf"})
                    if not doc_icon:
                        continue
                        ## skip if emtpy
                        
                    a_tag = doc_icon.find("a")
                    pdf_url = a_tag['href']
                    print("-" * 40)
                    print(pdf_url)
                    print("-" * 40)


                    data = [
                        jurisdiction, name, collection, source_page_text_url, adopt_formatted_date, retro_formatted_date
                    ]

                    ws.append(data)
                    wb.save(excel_file_path)
                    scrapedData_manager.save_data_to_logs(source_page_text_url)

                    # pdf_download_resp = session.get(pdf_url)
                    # status_code = 200
                    # if status_code == 200:
                    #     filename = f'{name}.pdf'
                    #     filename = clean_filename(filename)
                        # filename = f'Ch_{chap_num}_' + filename
                        # src_file_path = os.path.join(file_output_path, filename)
                        # with open(src_file_path, 'wb') as pdf_file:
                        #     pdf_file.write(pdf_download_resp.content)
                        #     print(f"Downloaded: {filename}")

                    #     data = [
                    #         jurisdiction, name, collection, source_page_text_url, adopt_formatted_date, retro_formatted_date
                    #     ]

                    #     ws.append(data)
                    #     wb.save(excel_file_path)
                    #     scrapedData_manager.save_data_to_logs(source_page_text_url)
                    # else:
                    #     print("Failed to request")
            else:
                print("Skipping already in logs...")
            print("-" * 40)

        if odata_count > 100 and skip_numbers < odata_count:
            skip_numbers = skip_numbers + 100
            print("Going to another Page....")
            print("-" * 40)
            scraping_process(encoded_search_term, skip_numbers)
            
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")            



def main():

    global scrapedData_manager, file_path, ws, wb, file_output_path, jurisdiction, excel_file_path, exclude_keywords
    jurisdiction = 'Australia'
    try:
        config.read('ESG_POC_script_config.ini')

        file_path = config['Paths']['file_output_path']
        logs_path = config['Paths']['scraped_logs_path']

        file_output_path = os.path.join(file_path, jurisdiction)
        # run_status_logs_path = config['Paths']['run_status_logs_path']
        # if not os.path.exists(run_status_logs_path):
        #     os.makedirs(run_status_logs_path)
        #Check if folder exist. If not exist create folder
        if not os.path.exists(file_output_path):
            os.makedirs(file_output_path)
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)

    except Exception as _e:
        print(_e)
        print("Initialization error. Check error logs.")
        sys.exit()

    
    current_time = datetime.now()
    file_time = current_time.strftime("%Y%m%d_%H%M%S")
    excel_file_path = os.path.join(file_output_path, f'{jurisdiction}_{file_time}.xlsx')
    scraped_logs_path = os.path.join(logs_path, f"{jurisdiction}_logs.txt")
    scrapedData_manager = ScrapedDataManager(scraped_logs_path)

    keywords_filename = 'australia_search_keywords.txt'
    
    headers = [
        'Jurisdiction', 'Original Title', 'Type of Regulation', 'Source', 'Date of adoption', 'Entry Into Force Date' 
    ]

    # THIS is for the Excel Output ***********
    # Check if the file exists
    if os.path.exists(excel_file_path):
        # Load the existing workbook and select the active sheet
        wb = openpyxl.load_workbook(excel_file_path)
        ws = wb.active
    else:
        # Create a new workbook and add a worksheet
        wb = Workbook()
        ws = wb.active
        # Add headers
        ws.append(headers)

    excluded_keywords_filename = 'australia_exclude_keywords.txt'
    search_items = read_search_items(keywords_filename)    
    exclude_keywords = read_search_items(excluded_keywords_filename)    

    for search_item in search_items:
        print("*" * 70)
        print(f"Searching Item: {search_item}")
        print("*" * 70)
        encoded_search_term = urllib.parse.quote(search_item)
        skip_numbers = 0
        scraping_process(encoded_search_term, skip_numbers)
        # break


if __name__ == "__main__":
    main()