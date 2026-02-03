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
    
    # User-Agent hozzáadása, hogy ne kapjunk 403-as hibát
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # Lekérés az álcázott fejléccel
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        ns = {
            'ns19': 'http://datex2.eu/schema/3/situation',
            'ns11': 'http://datex2.eu/schema/3/locationReferencing',
            'ns24': 'http://datex2.eu/schema/3/common'
        }

        data_list = []
        # Megkeressük az összes eseményt
        records = root.findall('.//ns19:situationRecord', ns)

        for record in records:
            acc_type = record.find('.//ns19:accidentType', ns)
            mgmt_type = record.find('.//ns19:roadOrCarriagewayOrLaneManagementType', ns)
            
            esemeny = "Egyéb korlátozás"
            if acc_type is not None: esemeny = acc_type.text
            elif mgmt_type is not None: esemeny = mgmt_type.text

            road_num = record.find('.//ns11:roadNumber', ns)
            lat = record.find('.//ns11:latitude', ns)
            lon = record.find('.//ns11:longitude', ns)
            
            if lat is not None:
                data_list.append({
                    "Adatfrissítés": most_idopont,
                    "Esemény típusa": esemeny,
                    "Út száma": road_num.text if road_num is not None else "N/A",
                    "Szélesség (Lat)": lat.text,
                    "Hosszúság (Lon)": lon.text,
                    "Google Maps": f"https://www.google.com/maps?q={lat.text},{lon.text}"
                })

        # Ha nincs adat, ne üres legyen a fájl
        if not data_list:
            data_list.append({
                "Adatfrissítés": most_idopont,
                "Esemény típusa": "Nincs aktív esemény",
                "Út száma": "-", "Szélesség (Lat)": "-", "Hosszúság (Lon)": "-", "Google Maps": "-"
            })

        df = pd.DataFrame(data_list)

        # Excel frissítése
        if os.path.exists(FILE_NAME):
            old_df = pd.read_excel(FILE_NAME)
            final_df = pd.concat([old_df, df]).drop_duplicates(
                subset=["Esemény típusa", "Út száma", "Szélesség (Lat)"], 
                keep='last'
            ).reset_index(drop=True)
        else:
            final_df = df

        final_df.to_excel(FILE_NAME, index=False)
        print(f"Sikeres mentés: {FILE_NAME}")

    except Exception as e:
        print(f"HIBA TÖRTÉNT: {e}")
        # Hiba esetén is hozzunk létre fájlt a Git miatt
        if not os.path.exists(FILE_NAME):
            pd.DataFrame([{"Hiba": str(e), "Időpont": most_idopont}]).to_excel(FILE_NAME, index=False)

if __name__ == "__main__":
    scrape_datex()
