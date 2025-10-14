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

out_excel_file = os.path.join(os.getcwd(), "Chile.xlsx")

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

regulation_translation_map_es = {
    "Ley": "Law",
    "Decreto": "Decree"
}

allowed_regulation_types = {
    "Law",
    "Decree"
}
non_esg_keywords = [
    "apropiación",   # appropriation
    "presupuesto",   # budget
    "revocar",       # repealed / revoked
    "aeropuerto",    # airport
    "aerolínea",     # airline
    "designación",   # appointment
    "designado",     # appointed
    "paciente",      # patient
    "coronavirus",   # COVID-19
    "covid-19"       # COVID-19
]


def get_english_text(text):
    try:
        # Explicitly set source language to Spanish
        translated_text = GoogleTranslator(source='es', target='en').translate(text)
        return translated_text
    except Exception as e:
        print(f"Translation failed: {e}")
        return text  # fallback to original

# def fetch_regulations(keyword: str, regulation_type: str):
#
#     base_url = "https://nuevo.leychile.cl/servicios/Consulta/listaresultadosavanzada"
#
#     # Determine XX1 (law) or XX2 (decree)
#     xx_type = "XX1" if regulation_type.lower() == "law" else "XX2"
#
#     # Build query string
#     params = {
#         "stringBusqueda": f"-2#normal#on||46#normal#({{{json.dumps(keyword)}}})#()||2#normal#{xx_type}||117#normal#on||48#normal#on",
#         "tipoNormaBA": "",
#         "npagina": 1,
#         "itemsporpagina": 50,
#         "orden": 2,
#         "tipoviene": 1,
#         "totalitems": "",
#         "seleccionado": 0,
#         "taxonomia": "",
#         "valor_taxonomia": "",
#         "o": "experta",
#         "r": ""
#     }
#
#     headers = {
#         "accept": "application/json, text/plain, */*",
#         "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
#         "origin": "https://www.bcn.cl",
#         "referer": "https://www.bcn.cl/",
#         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0"
#     }
#
#     try:
#         response = requests.get(base_url, headers=headers, params=params, timeout=30)
#         response.raise_for_status()
#         data = response.json()
#
#         # Handle nested JSON array (some responses are [[{...}, {...}]])
#         if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
#             data = data[0]
#         month_map = {
#             "ENE": "JAN", "FEB": "FEB", "MAR": "MAR", "ABR": "APR",
#             "MAY": "MAY", "JUN": "JUN", "JUL": "JUL", "AGO": "AUG",
#             "SEP": "SEP", "OCT": "OCT", "NOV": "NOV", "DIC": "DEC"
#         }
#         results = []
#         for item in data:
#             norma = item.get("NORMA", "").strip()
#             titulo_norma = item.get("TITULO_NORMA", "").strip()
#             title = f"{norma} {titulo_norma}".strip()
#             id =item.get("IDNORMA", "")
#
#             raw_date = item.get("FECHA_PUBLICACION", "").strip()
#             entryforce_date = ""
#             if raw_date:
#                 for es, en in month_map.items():
#                     raw_date = raw_date.replace(es, en)
#                 try:
#                     entryforce_date = datetime.strptime(raw_date, "%d-%b-%Y").strftime("%Y-%m-%d")
#                 except ValueError:
#                     entryforce_date = raw_date  # keep original if still unrecognized
#
#             source =f"https://www.bcn.cl/leychile/navegar?idNorma={id}"
#
#             tipo_original = item.get("TIPO", "").strip()
#             tipo_traducido = regulation_translation_map_es.get(tipo_original, tipo_original)
#
#             row_data = {
#                 "Jurisdiction": "Chile",
#                 "Original Title": title,
#                 "English Translation": get_english_text(title),
#                 "Type of Regulation": tipo_traducido,
#                 "Source": source,
#                 "Date of adoption": item.get("FECHA_PROMULGACION", ""),
#                 "Entry Into Force Date": entryforce_date,
#                 "Remark": keyword
#             }
#
#
#             title_lower = title.lower()
#             if (title not in completed_list
#                     and source not in completed_sources
#                     and not any(keyword in title_lower for keyword in
#                                 non_esg_keywords)and tipo_traducido in allowed_regulation_types ):
#                 results.append(row_data)
#                 print(row_data)
#                 completed_list.append(title)
#                 completed_sources.append(source)
#             else:
#                 print("the duplicate data or ESg exculded data have this link :", source, '\n')
#
#         return results
#
#     except Exception as e:
#         print(f"Error fetching {regulation_type}: {e}")
#         return []

def fetch_regulations(keyword: str, regulation_type: str):
    base_url = "https://nuevo.leychile.cl/servicios/Consulta/listaresultadosavanzada"

    # Determine XX1 (law) or XX2 (decree)
    xx_type = "XX1" if regulation_type.lower() == "law" else "XX2"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
        "origin": "https://www.bcn.cl",
        "referer": "https://www.bcn.cl/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0"
    }

    month_map = {
        "ENE": "JAN", "FEB": "FEB", "MAR": "MAR", "ABR": "APR",
        "MAY": "MAY", "JUN": "JUN", "JUL": "JUL", "AGO": "AUG",
        "SEP": "SEP", "OCT": "OCT", "NOV": "NOV", "DIC": "DEC"
    }

    results = []
    npagina = 1
    total_items = 1  # initialize >0 to enter the loop
    itemsporpagina = 50  # records per page

    try:
        while (npagina - 1) * itemsporpagina < total_items:

            params = {
                "stringBusqueda": f"-2#normal#on||46#normal#({{{json.dumps(keyword)}}})#()||2#normal#{xx_type}||117#normal#on||48#normal#on",
                "tipoNormaBA": "",
                "npagina": npagina,
                "itemsporpagina": itemsporpagina,
                "orden": 2,
                "tipoviene": 1,
                "totalitems": "",
                "seleccionado": 0,
                "taxonomia": "",
                "valor_taxonomia": "",
                "o": "experta",
                "r": ""
            }

            response = requests.get(base_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Check total items from response
            if isinstance(data, list) and len(data) > 1 and isinstance(data[1], dict):
                total_items = int(data[1].get("totalitems", 0))

            # Some responses wrap data in nested array
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                page_data = data[0]
            else:
                page_data = []

            if not page_data:
                print(f"No data found on page {npagina}.")
                break

            for item in page_data:
                norma = item.get("NORMA", "").strip()
                titulo_norma = item.get("TITULO_NORMA", "").strip()
                title = f"{norma} {titulo_norma}".strip()
                id = item.get("IDNORMA", "")

                raw_date = item.get("FECHA_PUBLICACION", "").strip()
                entryforce_date = ""
                if raw_date:
                    for es, en in month_map.items():
                        raw_date = raw_date.replace(es, en)
                    try:
                        entryforce_date = datetime.strptime(raw_date, "%d-%b-%Y").strftime("%Y-%m-%d")
                    except ValueError:
                        entryforce_date = raw_date

                source = f"https://www.bcn.cl/leychile/navegar?idNorma={id}"

                tipo_original = item.get("TIPO", "").strip()
                tipo_traducido = regulation_translation_map_es.get(tipo_original, tipo_original)

                row_data = {
                    "Jurisdiction": "Chile",
                    "Original Title": title,
                    "English Translation": get_english_text(title),
                    "Type of Regulation": tipo_traducido,
                    "Source": source,
                    "Date of adoption": item.get("FECHA_PROMULGACION", ""),
                    "Entry Into Force Date": entryforce_date,
                    "Remark": keyword
                }

                title_lower = title.lower()
                if (title not in completed_list
                        and source not in completed_sources
                        and not any(k in title_lower for k in non_esg_keywords)
                        and tipo_traducido in allowed_regulation_types):
                    results.append(row_data)
                    print(row_data)
                    completed_list.append(title)
                    completed_sources.append(source)
                else:
                    print("the duplicate data or ESg exculded data have this link :", source, '\n')

            npagina += 1  # move to next page

        return results

    except Exception as e:
        print(f"Error fetching {regulation_type}: {e}")
        return []

def main():
    for key_word in keyword_list:
        try:
            print(key_word)
            law_data = fetch_regulations(key_word, "law")
            decree_data = fetch_regulations(key_word, "decree")
            all_data = law_data + decree_data
            df = pd.DataFrame(all_data)
            df.to_excel(out_excel_file, index=False)
            print("✅ Data saved to 'Chile.xlsx'\n")

            # print(key_word)
            # get_page_content(key_word)
            # df = pd.DataFrame(results)
            # df.to_excel(out_excel_file, index=False)
        except Exception as error:
            error_list.append(str(error))

if __name__ == "__main__":
    main()