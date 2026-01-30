import requests
import xml.etree.ElementTree as ET
import pandas as pd
import os
from datetime import datetime

# Az Útinform Datex2 API végpontja
URL = "https://www.utinform.hu/api/datex2/situation" 
FILE_NAME = "utinform_adatok.xlsx"

def scrape_datex():
    print(f"Lekérdezés indítása: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        # Adatok letöltése
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        # Datex2 névterek meghatározása
        ns = {
            'ns19': 'http://datex2.eu/schema/3/situation',
            'ns11': 'http://datex2.eu/schema/3/locationReferencing',
            'ns24': 'http://datex2.eu/schema/3/common'
        }

        data_list = []

        # Végigmegyünk minden eseményrekordon
        for record in root.findall('.//ns19:situationRecord', ns):
            # 1. Típus kinyerése (Baleset vagy Útlezárás/Management)
            acc_type = record.find('.//ns19:accidentType', ns)
            mgmt_type = record.find('.//ns19:roadOrCarriagewayOrLaneManagementType', ns)
            comp_option = record.find('.//ns19:complianceOption', ns)
            
            esemeny_neve = "Ismeretlen"
            if acc_type is not None: 
                esemeny_neve = acc_type.text
            elif mgmt_type is not None: 
                esemeny_neve = mgmt_type.text
            
            # Kiegészítés (pl. mandatory/optional)
            if comp_option is not None:
                esemeny_neve = f"{esemeny_neve} ({comp_option.text})"

            # 2. Útszám kinyerése
            road_num = record.find('.//ns11:roadNumber', ns)
            
            # 3. Koordináták kinyerése (Lat/Lon)
            lat = record.find('.//ns11:latitude', ns)
            lon = record.find('.//ns11:longitude', ns)
            
            # Adatok hozzáadása a listához
            data_list.append({
                "Frissítve": datetime.now().strftime("%H:%M:%S"),
                "Esemény típusa": esemeny_neve,
                "Út száma": road_num.text if road_num is not None else "N/A",
                "Szélesség (Lat)": lat.text if lat is not None else "N/A",
                "Hosszúság (Lon)": lon.text if lon is not None else "N/A"
            })

        # Ha épp nincs esemény, jelezzük a táblázatban, hogy lefutott a kód
        if not data_list:
            data_list.append({
                "Frissítve": datetime.now().strftime("%H:%M:%S"),
                "Esemény típusa": "Nincs aktív korlátozás",
                "Út száma": "-", 
                "Szélesség (Lat)": "-", 
                "Hosszúság (Lon)": "-"
            })

        new_df = pd.DataFrame(data_list)

        # Excel mentése/frissítése
        if os.path.exists(FILE_NAME):
            old_df = pd.read_excel(FILE_NAME)
            # Összefűzzük, de csak azokat tartjuk meg, amiknél az Út, Típus vagy Koordináta eltér
            # A 'keep=last' biztosítja, hogy a legfrissebb időpont maradjon meg
            final_df = pd.concat([old_df, new_df]).drop_duplicates(
                subset=["Esemény típusa", "Út száma", "Szélesség (Lat)", "Hosszúság (Lon)"], 
                keep='last'
            ).reset_index(drop=True)
        else:
            final_df = new_df

        # Mentés Excel fájlba
        final_df.to_excel(FILE_NAME, index=False)
        print(f"Sikeres mentés. Aktuális rekordszám: {len(final_df)}")

    except Exception as e:
        print(f"Hiba történt a futás során: {e}")

if __name__ == "__main__":
    scrape_datex()
