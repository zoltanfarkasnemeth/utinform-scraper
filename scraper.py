import requests
import xml.etree.ElementTree as ET
import pandas as pd
import os
from datetime import datetime

URL = "https://www.utinform.hu/api/datex2/situation" 
FILE_NAME = "utinform_adatok.xlsx"

def scrape_datex():
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        # Kibővített névterek a pontos kereséshez
        ns = {
            'ns19': 'http://datex2.eu/schema/3/situation',
            'ns11': 'http://datex2.eu/schema/3/locationReferencing',
            'ns24': 'http://datex2.eu/schema/3/common'
        }

        data_list = []
        for record in root.findall('.//ns19:situationRecord', ns):
            # Típus kinyerése több helyről (Baleset vagy Útlezárás/Management)
            acc_type = record.find('.//ns19:accidentType', ns)
            mgmt_type = record.find('.//ns19:roadOrCarriagewayOrLaneManagementType', ns)
            comp_option = record.find('.//ns19:complianceOption', ns)
            
            # Végső típus meghatározása
            esemeny_neve = "Ismeretlen"
            if acc_type is not None: esemeny_neve = acc_type.text
            elif mgmt_type is not None: esemeny_neve = mgmt_type.text
            
            if comp_option is not None:
                esemeny_neve = f"{esemeny_neve} ({comp_option.text})"

            # Koordináták és Útszám
            road_num = record.find('.//ns11:roadNumber', ns)
            lat = record.find('.//ns11:latitude', ns)
            lon = record.find('.//ns11:longitude', ns)
            
            data_list.append({
                "Időpont": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Esemény típusa": esemeny_neve,
                "Út száma": road_num.text if road_num is not None else "N/A",
                "Szélesség (Lat)": lat.text if lat is not None else "N/A",
                "Hosszúság (Lon)": lon.text if lon is not None else "N/A"
            })

        if data_list:
            new_df = pd.DataFrame(data_list)
            if os.path.exists(FILE_NAME):
                old_df = pd.read_excel(FILE_NAME)
                # Összefűzés és duplikátum szűrés az összes oszlop alapján
                final_df = pd.concat([old_df, new_df]).drop_duplicates(subset=["Esemény típusa", "Út száma", "Szélesség (Lat)"], keep='first').reset_index(drop=True)
            else:
                final_df = new_df
            final_df.to_excel(FILE_NAME, index=False)
            print(f"Sikeres frissítés: {len(data_list)} rekord feldolgozva.")
        else:
            print("Nincs aktuális esemény az XML-ben.")

    except Exception as e:
        print(f"Hiba: {e}")

if __name__ == "__main__":
    scrape_datex()
