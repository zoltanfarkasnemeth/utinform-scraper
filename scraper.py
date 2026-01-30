import requests
import xml.etree.ElementTree as ET
import pandas as pd
import os
from datetime import datetime

# Beállítások
URL = "https://www.utinform.hu/api/datex2/situation"
FILE_NAME = "utinformacio.xlsx"

def scrape_datex():
    most_idopont = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Lekérdezés indítása: {most_idopont}")
    
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        ns = {
            'ns19': 'http://datex2.eu/schema/3/situation',
            'ns11': 'http://datex2.eu/schema/3/locationReferencing',
            'ns24': 'http://datex2.eu/schema/3/common'
        }

        data_list = []
        for record in root.findall('.//ns19:situationRecord', ns):
            acc_type = record.find('.//ns19:accidentType', ns)
            mgmt_type = record.find('.//ns19:roadOrCarriagewayOrLaneManagementType', ns)
            comp_option = record.find('.//ns19:complianceOption', ns)
            
            esemeny = "Egyéb korlátozás"
            if acc_type is not None:
                esemeny = acc_type.text
            elif mgmt_type is not None:
                esemeny = mgmt_type.text
            
            if comp_option is not None:
                esemeny = f"{esemeny} ({comp_option.text})"

            road_num = record.find('.//ns11:roadNumber', ns)
            lat = record.find('.//ns11:latitude', ns)
            lon = record.find('.//ns11:longitude', ns)
            
            if lat is not None and lon is not None:
                data_list.append({
                    "Adatfrissítés": most_idopont,
                    "Esemény típusa": esemeny,
                    "Út száma": road_num.text if road_num is not None else "N/A",
                    "Szélesség (Lat)": lat.text,
                    "Hosszúság (Lon)": lon.text,
                    "Google Maps": f"https://www.google.com/maps?q={lat.text},{lon.text}"
                })

        # HA NINCS ADAT, akkor is létrehozunk egy üres DataFrame-et fejlécekkel
        if not data_list:
            print("Jelenleg nincs aktív esemény az XML-ben, üres táblázat készül.")
            df = pd.DataFrame(columns=["Adatfrissítés", "Esemény típusa", "Út száma", "Szélesség (Lat)", "Hosszúság (Lon)", "Google Maps"])
        else:
            df = pd.DataFrame(data_list)

        # Excel frissítése vagy létrehozása
        if os.path.exists(FILE_NAME):
            old_df = pd.read_excel(FILE_NAME)
            final_df = pd.concat([old_df, df]).drop_duplicates(
                subset=["Esemény típusa", "Út száma", "Szélesség (Lat)"], 
                keep='last'
            ).reset_index(drop=True)
        else:
            final_df = df

        final_df.to_excel(FILE_NAME, index=False)
        print(f"Sikeres mentés: {FILE_NAME} ({len(final_df)} sor)")

    except Exception as e:
        print(f"Hiba történt: {e}")
        # Hiba esetén is létrehozunk egy alap fájlt, hogy a GitHub Action ne dőljön össze
        if not os.path.exists(FILE_NAME):
            pd.DataFrame(columns=["Hiba"]).to_excel(FILE_NAME, index=False)

if __name__ == "__main__":
    scrape_datex()
