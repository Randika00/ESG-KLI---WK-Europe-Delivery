import urllib.parse
from datetime import date
import requests
import os
import re
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
from datetime import datetime
import requests
import urllib.parse
import json
from urllib.parse import urlparse

# List of your keywords
error_list = []
completed_list = []
completed_sources = []
data =[]

headers_template = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
    "content-type": "application/json",
    "origin": "https://www.govinfo.gov",
    "priority": "u=1, i",
    "sec-ch-ua": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
}

non_esg_keywords = [
    "amendment", "appropriation", "budget", "repealed", "revoked",
    "airport", "airline", "appointment", "appointed", "patient",
    "coronavirus", "covid-19"
]


try:
    with open('keywords.txt', 'r', encoding='utf-8') as file:
        keyword_list = file.read().strip().splitlines()
except Exception as error:
    error_list.append(str(error))



statusCode = None
results = []
out_excel_file = os.path.join(os.getcwd(), "US.xlsx")


today = date.today().isoformat()
referer_format = (
    'https://www.govinfo.gov/app/search/%7B%22historical%22%3Atrue%2C%22offset%22%3A0%2C'
    '%22query%22%3A%22collection%3A(PLAW%20OR%20COMPS)%20AND%20publishdate%3Arange(%2C{today})%20AND%20title%3A({{}})%22%2C%22pageSize%22%3A100%7D'
).format(today=today)

url = "https://www.govinfo.gov/wssearch/search"


def main():
    for sin_key in keyword_list:
        try:
            encoded_keyword = urllib.parse.quote(sin_key)
            link = referer_format.format(encoded_keyword)
            print(f"{sin_key} - {link}")

            for i in range(10):
                try:
                    payload = {
                        "historical": True,
                        "offset": i,
                        "pageSize": 100,
                        "query": f"collection:(PLAW OR COMPS) AND publishdate:range(,{today}) AND title:({sin_key})"
                    }
                    headers = headers_template.copy()
                    headers["referer"] = link

                    # Send POST request
                    response = requests.post(url, headers=headers, data=json.dumps(payload))

                    result_set = response.json().get("resultSet", [])  # or handle response['results'] etc.
                    if not result_set:
                        break

                    for item in result_set:
                        try:
                            line1 = item.get("line1")
                            line2 = item.get("line2")
                            a_url = item.get("fieldMap", {}).get("url")
                            a_url = re.sub(r'/html/[^/]+\.htm$', '', a_url)
                            Source_link= a_url.replace('content/pkg','app/details')

                            doc_id = a_url.rstrip('/').split('/')[-1]
                            a_url= f"https://www.govinfo.gov/wssearch/publink/PLAW/{doc_id}"
                            new_url = None
                            if "COMPS" in Source_link:
                                parsed = urlparse(Source_link)
                                parts = parsed.path.strip("/").split("/")

                                if len(parts) >= 4:
                                    package_id = parts[2]
                                    granule_id = parts[3]
                                    new_url = f"https://www.govinfo.gov/wssearch/getContentDetail?packageId={package_id}&granuleId={granule_id}"

                            if new_url:
                                t_url =new_url
                            else:
                                t_url= f"https://www.govinfo.gov/wssearch/getContentDetail?packageId={doc_id}"



                            referer = f"https://www.govinfo.gov/app/details/{doc_id}/related"
                            # print(t_url)

                            headers = {
                                "accept": "application/json, text/javascript, */*; q=0.01",
                                "accept-encoding": "gzip, deflate, br, zstd",
                                "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
                                "content-type": "application/json",
                                "priority": "u=1, i",
                                "referer": Source_link,
                                "sec-ch-ua": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
                                "sec-ch-ua-mobile": "?0",
                                "sec-ch-ua-platform": '"Windows"',
                                "sec-fetch-dest": "empty",
                                "sec-fetch-mode": "cors",
                                "sec-fetch-site": "same-origin",
                                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
                            }
                            headers_1 = {
                                "accept": "application/json, text/javascript, */*; q=0.01",
                                "accept-encoding": "gzip, deflate, br, zstd",
                                "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
                                "content-type": "application/json",
                                "priority": "u=1, i",
                                "referer": referer,
                                "sec-ch-ua": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
                                "sec-ch-ua-mobile": "?0",
                                "sec-ch-ua-platform": '"Windows"',
                                "sec-fetch-dest": "empty",
                                "sec-fetch-mode": "cors",
                                "sec-fetch-site": "same-origin",
                                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
                            }
                            a_response = requests.get(a_url, headers=headers_1)
                            t_response = requests.get(t_url, headers=headers)

                            if t_response.status_code == 200:
                                try:
                                    t_data = t_response.json()
                                    title = t_data.get("title", "Title not found")
                                    collection = next((item["colvalue"] for item in
                                                       t_data.get("metadata", {}).get("columnnamevalueset", []) if
                                                       item.get("colname") == "Collection"), "Collection not found")

                                    # print(title)
                                    match = re.match(r'^Public Law \d+ - \d+ - (.+)', title)
                                    if match:
                                        title = match.group(1).strip()
                                    else:
                                        title=title
                                    # print(title)
                                    # print("Collection:", collection)


                                    if collection == "Public and Private Laws":
                                        txtlink = t_data.get("download", {}).get("txtlink", "")
                                        if txtlink.startswith("//"):
                                            full_url = "https:" + txtlink
                                        else:
                                            full_url = url

                                        # print(full_url)
                                        raw_date = next(
                                            (item["colvalue"] for item in
                                             t_data.get("metadata", {}).get("columnnamevalueset", [])
                                             if item.get("colname") == "Date Approved"),
                                            None
                                        )

                                        formatted_date = "Date not found or invalid"
                                        if raw_date:
                                            clean_date_str = raw_date.replace("\n", " ").replace("\t", " ").strip()
                                            try:
                                                parsed_date = datetime.strptime(clean_date_str, "%B %d, %Y")
                                                entry_into_force_date = parsed_date.strftime("%Y-%m-%d")
                                                # print(entry_into_force_date)
                                            except ValueError:
                                                pass  # Keep default message if parsing fails

                                        if a_response.status_code == 200:
                                            try:
                                                data = a_response.json()
                                                versionset = data.get("legistationincontext", {}).get("versionset", [])
                                                if versionset:
                                                    contents = versionset[0].get("contents", [])
                                                    if contents:
                                                        date_of_adoption = contents[0].get("issuedDate")
                                                        try:
                                                            # Try DD/MM/YYYY first
                                                            parsed_date = datetime.strptime(date_of_adoption, "%d/%m/%Y")
                                                        except ValueError:
                                                            try:
                                                                # If that fails, try MM/DD/YYYY
                                                                parsed_date = datetime.strptime(date_of_adoption, "%m/%d/%Y")
                                                            except ValueError:
                                                                print("Invalid date format:", date_of_adoption)
                                                                parsed_date = None

                                                        if parsed_date:
                                                            # date_of_adoption = parsed_date.strftime("%#d-%b-%y")
                                                            date_of_adoption = parsed_date.strftime("%Y-%m-%d")
                                                            # print(date_of_adoption)

                                                    else:
                                                        print("No contents found in versionset.")
                                                else:
                                                    print("No versionset found.")
                                            except Exception as e:
                                                print("Error processing JSON:", e)
                                        else:
                                            print(f"Failed to retrieve data. Status code: {a_response.status_code}")

                                        # if regulation_type in ["Private Law", "Public Law"]:
                                        #     regulation_type = "Act"
                                        # else:
                                        #     regulation_type = regulation_type

                                    else:
                                        date_of_adoption= None
                                        entry_into_force_date= None
                                        txtlink = t_data.get("download", {}).get("uslmlink", "")
                                        if txtlink.startswith("//"):
                                            full_url = "https:" + txtlink
                                        else:
                                            full_url = url

                                        # print(full_url)
                                        # print("This is NOT a Public and Private Law document.")


                                except Exception as e:
                                    print("Error processing JSON:", e)
                            else:
                                print(f"Failed to retrieve data. Status code: {t_response.status_code}")


                            entry = {
                                "Jurisdiction": "US",
                                "Original Title": title,
                                "Type of Regulation": "Act",
                                "Source": full_url,
                                "Date of adoption": date_of_adoption,
                                "Entry Into Force Date": entry_into_force_date,
                                "Remarks":sin_key
                            }


                            title_lower = entry["Original Title"].lower()

                            if ( entry["Original Title"] not in completed_list
                                    and entry["Source"] not in completed_sources
                                    and not any(keyword in title_lower for keyword in non_esg_keywords)
                            ):
                                print(entry)
                                results.append(entry)
                                completed_list.append(entry["Original Title"])
                                completed_sources.append(entry["Source"])

                            print('*'*100)

                        except Exception as error:
                            error_list.append(error)

                except Exception as error:
                    error_list.append(error)

        except Exception as error:
            error_list.append(error)

    df = pd.DataFrame(results)
    df.to_excel(out_excel_file, index=False)

if __name__ == "__main__":
    main()
