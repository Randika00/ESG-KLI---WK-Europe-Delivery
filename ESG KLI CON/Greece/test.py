import requests
import json
url = "https://searchetv99.azurewebsites.net/api/search"

payload = {
    "advancedSearch": "\"Εθνικός Κλιματικός Νόμος\"",
    "selectYear": [],
    "selectIssue": [],
    "documentNumber": "",
    "entity": [],
    "categoryIds": [],
    "datePublished": "",
    "dateReleased": "",
    "legislationCatalogues": "",
    "selectedEntitiesSearchHistory": [],
    "tags": []
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Origin": "https://search.et.gr",
    "Referer": "https://search.et.gr/"
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    data = response.json()
    raw_data = data["data"]

    # parse into list of dicts
    parsed_data = json.loads(raw_data)

    # loop through each record
    for idx, record in enumerate(parsed_data, start=1):
        print(f"--- Record {idx} ---")
        for key, value in record.items():
            print(f"{key}: {value}")
        print("-" * 60)
else:
    print("Request failed:", response.status_code)
