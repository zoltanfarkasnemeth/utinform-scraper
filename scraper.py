import requests
import xml.etree.ElementTree as ET
import pandas as pd
import os
from datetime import datetime

# Ide másold be a pontos URL-t!
URL = "https://www.utinform.hu/api/datex2/situation" 
FILE_NAME = "utinform_adatok.xlsx"

def scrape_datex():
    print(f"Lekérdezés indítása: {URL}")
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        
        # Ha üres a válasz, ne álljon le hibával
        if not response.content:
            print("Üres válasz érkezett a szervertől.")
            create_empty_if_not_exists()
            return

        root = ET.fromstring(response.content)
        
        ns = {
            'ns19': 'http://datex2.eu/schema/3/situation',
            'ns11': 'http://datex2.eu/schema/3/locationReferencing',
            'ns24': 'http://datex2.eu/schema/3/common'
        }

        data_list = []
        for record in root.findall('.//ns19:situationRecord', ns):
            acc_type = record.find('ns19:accidentType', ns)
            road_num = record.find('.//ns11:roadNumber', ns)
            lat = record.find('.//ns11:latitude', ns)
            lon = record.find('.//ns11:longitude', ns)
            
            data_list.append({
                "Időpont": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Esemény típusa": acc_type.text if acc_type is not None else "Ismeretlen",
                "Út száma": road_num.text if road_num is not None else "N/A",
                "Szélesség": lat.text if lat is not None else "N/A",
                "Hosszúság": lon.text if lon is not None else "N/A"
            })

        if data_list:
            new_df = pd.DataFrame(data_list)
            if os.path.exists(FILE_NAME):
                old_df = pd.read_excel(FILE_NAME)
                final_df = pd.concat([old_df, new_df]).drop_duplicates().reset_index(drop=True)
            else:
                final_df = new_df
            final_df.to_excel(FILE_NAME, index=False)
            print(f"Sikeres mentés: {len(data_list)} sor.")
        else:
            print("Nem találtam feldolgozható rekordot az XML-ben.")
            create_empty_if_not_exists()

    except Exception as e:
        print(f"Hiba történt: {e}")
        create_empty_if_not_exists()

def create_empty_if_not_exists():
    if not os.path.exists(FILE_NAME):
        pd.DataFrame(columns=["Időpont", "Esemény típusa", "Út száma", "Szélesség", "Hosszúság"]).to_excel(FILE_NAME, index=False)
        print("Üres Excel fájl létrehozva a hiba elkerülése végett.")

if __name__ == "__main__":
    scrape_datex()
