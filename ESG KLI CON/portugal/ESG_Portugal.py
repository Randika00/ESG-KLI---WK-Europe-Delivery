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
    "x-csrftoken": "T6C+9iB49TLra4jEsMeSckDMNhQ="
}
non_esg_keywords = [
    "alteração",       # amendment / amending
    "apropriação",     # appropriation
    "orçamento",       # budget
    "revogação",       # repealed
    "revogado",        # revoked
    "aeroporto",       # airport
    "companhia aérea", # airline
    "nomeação",        # appointment
    "nomeações",       # appointments
    "nomeado",         # appointed
    "doente",          # patient
    "coronavírus",     # coronavirus / COVID-19
    "covid-19",        # explicitly include this variation too
]
out_excel_file = os.path.join(os.getcwd(), "Portugal.xlsx")

try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().strip().splitlines()
except Exception as error:
    error_list.append(str(error))

def get_soup_with_post(url, payload,retries=10, delay=3):
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, json=payload, headers=headers)

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

def get_page_content(key_word):
    url = 'https://diariodarepublica.pt/dr/screenservices/dr/Pesquisas/PesquisaResultado/DataActionGetPesquisas'

    start_index = 0
    while True:
        payload = {
            "versionInfo": {
                "moduleVersion": "DEIUVWYnhV+8XFvFHVYxCQ",
                "apiVersion": "6Bnghy+TVcnOZSN2FpzXbQ"
            },
            "viewName": "Pesquisas.PesquisaResultado",
            "screenData": {
                "variables": {
                    "FiltrosDePesquisa": {
                        "tipoConteudo": {
                            "List": ["AtosSerie1", "AtosSerie2"]
                        },
                        "serie": {
                            "List": ["I", "II"]
                        },
                        "numero": "",
                        "ano": "0",
                        "suplemento": "0",
                        "dataPublicacao": "",
                        "parte": "",
                        "apendice": "",
                        "fasciculo": "",
                        "tipo": {
                            "List": ["\"Lei\"", "\"Decreto\"", "\"Decreto-Lei\""]
                        },
                        "emissor": {
                            "List": [],
                            "EmptyListItem": ""
                        },
                        "texto": "",
                        "sumario": f"\"{key_word}\"",
                        "entidadeProponente": {
                            "List": [],
                            "EmptyListItem": ""
                        },
                        "numeroDR": "",
                        "paginaInicial": "0",
                        "paginaFinal": "0",
                        "dataAssinatura": "",
                        "dataDistribuicao": "",
                        "entidadePrincipal": {
                            "List": [],
                            "EmptyListItem": ""
                        },
                        "entidadeEmitente": {
                            "List": [],
                            "EmptyListItem": ""
                        },
                        "docType": "",
                        "proferido": "",
                        "processo": "",
                        "assunto": "",
                        "recorrente": "",
                        "recorrido": "",
                        "relator": "",
                        "empresa": "",
                        "concelho": "",
                        "nif": "",
                        "anuncio": "",
                        "numeroDoc": "",
                        "semestre": "",
                        "IsLegConsolidadaSelected": "false",
                        "IsFromData": "false",
                        "DescritorList": {
                            "List": [],
                            "EmptyListItem": ""
                        }
                    },
                    "NumeroDeResultadosPorPagina": 200,
                    "StartIndex": start_index,
                    "OcultarRevogados": "false",
                    "DestaqueExcertos": "false",
                    "TipoOrdenacaoId": 9,
                    "Pesquisa": {
                        "List": [],
                        "EmptyListItem": ""
                    },
                    "Texto": "",
                    "ResultadosElastic": {
                        "Took": "0",
                        "Timed_out": "false",

                    },
                }
            },
            "clientVariables": {}
        }

        main_content = get_soup_with_post(url, payload)["data"]["Resultado"]
        law_content = json.loads(main_content)
        data = law_content["hits"]["hits"]

        read_json_content(data)
        start_index += 200

        if len(data) < 200:
            break

def read_json_content(all_law):

    for sin_law in all_law:
        try:
            metadata = sin_law["_source"]
            valid = metadata.get("vigencia")
            if valid:
                if valid == "VIGENTE":
                    read_metadata(metadata)
                    # break
            else:
                read_metadata(metadata)
                # break

        except Exception as error:
            error_list.append(str(error))




def read_metadata(metadata):
    # print(metadata["title"])
    # print(metadata)
    dbid = metadata["dbId"]
    reg_type = metadata["tipo"]
    number_int = metadata["numeroInt"]
    year_ano = metadata["ano"]
    source = f"https://diariodarepublica.pt/dr/detalhe/{reg_type}/{number_int}-{year_ano}-{dbid}".lower()
    get_data_from_final_json(dbid,source)

from babel.dates import format_date
def extract_date_from_portuguese_text(text):
    match = re.search(r"(\d{1,2}) de (\w+) de (\d{4})", text, re.IGNORECASE)
    if not match:
        return None

    day, month_pt, year = match.groups()
    month_map = {
        "janeiro": 1,
        "fevereiro": 2,
        "março": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12,
    }

    month_num = month_map.get(month_pt.lower())
    if not month_num:
        return None

    try:
        date_obj = datetime(int(year), month_num, int(day))
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return None
def get_english_text(text):
    translated_text = GoogleTranslator(source='pt', target='en').translate(text)
    return translated_text

def get_data_from_final_json(dbid,source):
    payload = {
        "versionInfo": {
            "moduleVersion": "DEIUVWYnhV+8XFvFHVYxCQ",
            "apiVersion": "Qu0vL8jfi9wtTh5e6QanXA"
        },
        "viewName": "Legislacao_Conteudos.Conteudo_Detalhe",
        "screenData": {
            "variables": {
                "DipLegisId": f"{dbid}",
            }
        }
    }

    url = 'https://diariodarepublica.pt/dr/screenservices/dr/Legislacao_Conteudos/Conteudo_Detalhe/DataActionGetConteudoDataAndApplicationSettings'

    # soup = get_soup_with_post(url,payload)["data"]["DetalheConteudo"]["TextoFormatado"]

    html_string = get_soup_with_post(url, payload)["data"]["DetalheConteudo"]["TextoFormatado"]

    # Parse the HTML with BeautifulSoup


    data = get_soup_with_post(url, payload)["data"]
    detalhe = data["DetalheConteudo"]

    title_p1 = detalhe.get("Titulo", "")
    regulation_type = detalhe.get("TipoDiplomaEnglish", "")
    adoption_date = detalhe.get("DataPublicacao", "")
    summary = detalhe.get("Sumario", "")

    if adoption_date:
        date_obj = datetime.strptime(adoption_date, "%Y-%m-%d")
        formatted_date = format_date(date_obj, format="d 'de' MMMM", locale='pt_PT')
        final_title = f"{title_p1}, de {formatted_date} - {summary}"
    else:
        final_title = f"{title_p1} - {summary}"

    soup = BeautifulSoup(html_string, "html.parser")

    # Find the <p> tag that contains the text "Entrada em vigor"
    target_p = soup.find("p", string=lambda text: text and "Entrada em vigor" in text)

    entry_into_force = ""
    if target_p:
        next_tag = target_p.find_next_sibling()
        if next_tag:
            next_text = next_tag.get_text(strip=True)
            if "no dia seguinte ao da sua publicação." in next_text:
                entry_into_force = adoption_date

            else:
                extracted_date = extract_date_from_portuguese_text(next_text)
                if extracted_date:
                    entry_into_force = extracted_date
                else:
                    entry_into_force = ""
        else:
            entry_into_force = ""
    else:
        entry_into_force = ""

    row_data = {
        "Jurisdiction": "Portugal",
        "Original Title": final_title,
        "English Translation": get_english_text(final_title),
        "Type of Regulation": regulation_type,
        "Source": source,
        "Date of adoption": adoption_date,
        "Entry Into Force Date": entry_into_force
    }

    title_lower = final_title.lower()
    if (final_title not in completed_list
            and source not in completed_sources
            and not any(keyword in title_lower for keyword in
                        non_esg_keywords) ):
        results.append(row_data)
        print(row_data)
        completed_list.append(final_title)
        completed_sources.append(source)
    else:
        print("the duplicate data or ESg exculded data have this link :", source, '\n')



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