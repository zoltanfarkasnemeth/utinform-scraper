import requests
import xml.etree.ElementTree as ET
import pandas as pd
import os
from datetime import datetime

# Útinform Datex2 API végpont
URL = "https://www.utinform.hu/api/datex2/situation" 
FILE_NAME = "utinform_adatok.xlsx"

def scrape_datex():
    most = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Lekérdezés indítása: {most}")
    
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        # Datex2 névterek definíciója
        ns = {
            'ns19': 'http://datex2.eu/schema/3/situation',
            'ns11': 'http://datex2.eu/schema/3/locationReferencing',
            'ns24': 'http://datex2.eu/schema/3/common'
        }

        data_list = []

        # Minden situationRecord elem végigjárása
        for record in root.findall('.//ns19:situationRecord', ns):
            # 1. Típus meghatározása (Baleset vagy Útlezárás)
            acc_type = record.find('.//ns19:accidentType', ns)
            mgmt_type = record.find('.//ns19:roadOrCarriagewayOrLaneManagementType', ns)
            comp_option = record.find('.//ns19:complianceOption', ns)
            
            esemeny = "Egyéb korlátozás"
            if acc_type is not None:
                esemeny = acc_type.text
            elif mgmt_type is not None:
                esemeny = mgmt_type.text
            
            # Compliance kiegészítés (pl. mandatory)
            if comp_option is not None:
                esemeny = f"{esemeny} ({comp_option.text})"

            # 2. Útszám és koordináták kinyerése
            road_num = record.find('.//ns11:roadNumber', ns)
            lat = record.find('.//ns11:latitude', ns)
            lon = record.find('.//ns11:longitude', ns)
            
            # Adatsor összeállítása
            data_list.append({
                "Adatfrissítés": most,
                "Esemény típusa": esemeny,
                "Út száma": road_num.text if road_num is not None else "N/A",
                "Szélesség (Lat)": lat.text if lat is not None else "N/A",
                "Hosszúság (Lon)": lon.text if lon is not None else "N/A",
                "Google Maps": f"https://www.google.com/maps?q={lat.text},{lon.text}" if lat is not None else "N/A"
            })

        # Ha nincs adat, ne álljon le, hogy a GitHub Action ne jelezzen hibát
        if not data_list:
            print("Jelenleg nincs aktív esemény az XML-ben.")
            # Hozzáadunk egy sort, hogy lássuk: a script lefutott
            data_list.append({
                "Adatfrissítés": most,
                "Esemény típusa": "Nincs esemény",
                "Út száma": "-", "Szélesség (Lat)": "-", "Hosszúság (Lon)": "-", "Google Maps": "-"
            })

        new_df = pd.DataFrame(data_list)

        # Excel fájl kezelése (hozzáfűzés duplikáció szűréssel)
        if os.path.exists(FILE_NAME):
            old_df = pd.read_excel(FILE_NAME)
            # Ha a típus, útszám és koordináta egyezik, nem vesszük fel új sorként (csak frissítjük az időt)
            final_df = pd.concat([old_df, new_df]).drop_duplicates(
                subset=["Esemény típusa", "Út száma", "Szélesség (Lat)"], 
                keep='last'
            ).reset_index(drop=True)
        else:
            final_df = new_df

        # Mentés
        final_df.to_excel(FILE_NAME, index=False)
        print(f"Sikeres mentés az Excelbe. Sorok száma: {len(final_df)}")

    except Exception as e:
        print(f"Hiba történt: {e}")

if __name__ == "__main__":
    scrape_datex()
