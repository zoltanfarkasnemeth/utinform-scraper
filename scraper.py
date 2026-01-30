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
        
        # Datex2 névterek - kiterjesztve
        ns = {
            'ns2': 'http://datex2.eu/schema/3/messageContainer',
            'ns19': 'http://datex2.eu/schema/3/situation',
            'ns11': 'http://datex2.eu/schema/3/locationReferencing',
            'ns24': 'http://datex2.eu/schema/3/common'
        }

        data_list = []

        # Rekordok keresése - rugalmasabb elérési úttal
        records = root.findall('.//ns19:situationRecord', ns)
        print(f"Talált rekordok száma: {len(records)}")

        for record in records:
            # Típusok kinyerése
            acc_type = record.find('.//ns19:accidentType', ns)
            mgmt_type = record.find('.//ns19:roadOrCarriagewayOrLaneManagementType', ns)
            
            esemeny = "Egyéb esemény"
            if acc_type is not None: esemeny = acc_type.text
            elif mgmt_type is not None: esemeny = mgmt_type.text

            # Út és koordináták
            road_num = record.find('.//ns11:roadNumber', ns)
            lat = record.find('.//ns11:latitude', ns)
            lon = record.find('.//ns11:longitude', ns)
            
            if lat is not None:
                data_list.append({
                    "Adatfrissítés": most_idopont,
                    "Esemény típusa": esemeny,
                    "Út száma": road_num.text if road_num is not None else "N/A",
                    "Szélesség (Lat)": lat.text,
                    "Hosszúság (Lon)": lon.text
                })

        # Ha nincs adat az XML-ben, akkor is csinálunk egy sort a fájlba
        if not data_list:
            data_list.append({
                "Adatfrissítés": most_idopont,
                "Esemény típusa": "Nincs aktív esemény az útinfón",
                "Út száma": "-", "Szélesség (Lat)": "-", "Hosszúság (Lon)": "-"
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
        # Hiba esetén is létrehozzuk a fájlt, hogy a GitHub Action ne álljon le!
        error_df = pd.DataFrame([{"Hiba": str(e), "Időpont": most_idopont}])
        error_df.to_excel(FILE_NAME, index=False)

if __name__ == "__main__":
    scrape_datex()
