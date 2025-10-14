import requests
import json
import pandas as pd


def fetch_regulations(keyword: str, regulation_type: str):
    """
    Fetches Chilean regulations (Law or Decree) from nuevo.leychile.cl API.

    :param keyword: Search term (e.g. 'SERVICIO DE BIODIVERSIDAD Y ÁREAS PROTEGIDAS')
    :param regulation_type: Either 'law' or 'decree'
    :return: List of parsed JSON records
    """
    base_url = "https://nuevo.leychile.cl/servicios/Consulta/listaresultadosavanzada"

    # Determine XX1 (law) or XX2 (decree)
    xx_type = "XX1" if regulation_type.lower() == "law" else "XX2"

    # Build query string
    params = {
        "stringBusqueda": f"-2#normal#on||46#normal#({{{json.dumps(keyword)}}})#()||2#normal#{xx_type}||117#normal#on||48#normal#on",
        "tipoNormaBA": "",
        "npagina": 1,
        "itemsporpagina": 50,
        "orden": 2,
        "tipoviene": 1,
        "totalitems": "",
        "seleccionado": 0,
        "taxonomia": "",
        "valor_taxonomia": "",
        "o": "experta",
        "r": ""
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
        "origin": "https://www.bcn.cl",
        "referer": "https://www.bcn.cl/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0"
    }

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Some responses wrap data in a nested array
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            data = data[0]

        results = []
        for item in data:
            results.append({
                "Tipo": item.get("TIPO", ""),
                "Numero": item.get("NUMERO", ""),
                "Norma": item.get("NORMA", ""),
                "Titulo": item.get("TITULO_NORMA", ""),
                "Organismo": item.get("ORGANISMO", ""),
                "Fecha Publicacion": item.get("FECHA_PUBLICACION", ""),
                "Fecha Promulgacion": item.get("FECHA_PROMULGACION", ""),
                "Fecha Vigencia": item.get("FECHA_VIGENCIA", ""),
                "Descripcion": item.get("DESCRIPCION", ""),
                "Tipo Version": item.get("TIPOVERSION_TEXTO", "")
            })

        return results

    except Exception as e:
        print(f"Error fetching {regulation_type}: {e}")
        return []


if __name__ == "__main__":
    keyword = "SERVICIO DE BIODIVERSIDAD Y ÁREAS PROTEGIDAS"

    law_data = fetch_regulations(keyword, "law")
    decree_data = fetch_regulations(keyword, "decree")

    # Combine and display
    all_data = law_data + decree_data
    df = pd.DataFrame(all_data)

    print(df)
    df.to_excel("Chile_Regulations.xlsx", index=False)
    print("\n✅ Data saved to 'Chile_Regulations.xlsx'")
