import requests
import xml.etree.ElementTree as ET
import pandas as pd
import os
from datetime import datetime

# URL, ahonnan az XML-t töltöd le (helyettesítsd a valódival)
URL = "https://pelda-url.hu/datex_adatok.xml"
FILE_NAME = "utinform_adatok.xlsx"

def scrape_datex():
    try:
        response = requests.get(URL)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        # Névterek definiálása a kereséshez
        ns = {
            'ns19': 'http://datex2.eu/schema/3/situation',
            'ns11': 'http://datex2.eu/schema/3/locationReferencing',
            'ns24': 'http://datex2.eu/schema/3/common'
        }

        data_list = []

        # Minden situationRecord végigjárása
        for record in root.findall('.//ns19:situationRecord', ns):
            # Típus kinyerése
            acc_type = record.find('ns19:accidentType', ns)
            type_val = acc_type.text if acc_type is not None else "N/A"
            
            # Útszám és koordináták kinyerése
            road_num = record.find('.//ns11:roadNumber', ns)
            lat = record.find('.//ns11:latitude', ns)
            lon = record.find('.//ns11:longitude', ns)
            
            data_list.append({
                "Időpont": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Esemény típusa": type_val,
                "Út száma": road_num.text if road_num is not None else "N/A",
                "Szélesség": lat.text if lat is not None else "N/A",
                "Hosszúság": lon.text if lon is not None else "N/A"
            })

        if not data_list:
            print("Nem találtam új adatot.")
            return

        new_df = pd.DataFrame(data_list)

        # Ha már létezik az Excel, fűzzük hozzá, különben hozzuk létre
        if os.path.exists(FILE_NAME):
            old_df = pd.read_excel(FILE_NAME)
            final_df = pd.concat([old_df, new_df]).drop_duplicates().reset_index(drop=True)
        else:
            final_df = new_df

        final_df.to_excel(FILE_NAME, index=False)
        print(f"Sikeres mentés: {len(data_list)} sor hozzáadva.")

    except Exception as e:
        print(f"Hiba történt: {e}")

if __name__ == "__main__":
    scrape_datex()