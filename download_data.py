import requests
import zipfile
import io
import os

def download_spatial_data():
    url = "https://github.com/pararawendy/border-desa-indonesia-geojson/raw/master/indonesia_villages_border.geojson.zip"
    print(f"Downloading spatial data from {url}...")
    
    response = requests.get(url)
    if response.status_code == 200:
        z = zipfile.ZipFile(io.BytesIO(response.content))
        geojson_file = [f for f in z.namelist() if f.endswith('.geojson')][0]
        z.extract(geojson_file, "data")
        os.rename(os.path.join("data", geojson_file), os.path.join("data", "indonesia_villages.geojson"))
        print("Spatial data downloaded and extracted successfully.")
    else:
        print(f"Failed to download spatial data. Status code: {response.status_code}")

def download_and_convert_sql():
    sql_url = "https://raw.githubusercontent.com/cahyadsn/wilayah/master/db/wilayah.sql"
    print(f"Downloading SQL data from {sql_url}...")
    
    response = requests.get(sql_url)
    if response.status_code == 200:
        sql_content = response.text
        print("SQL data downloaded. Converting to JSON...")
        
        # Simple extraction of (kode, nama) from INSERT INTO `wilayah` VALUES ('61.02.13.2003', 'NANGA EMAU');
        import re
        import json
        
        # Pattern to match ('CODE', 'NAME')
        pattern = re.compile(r"\('([0-9.]+)',\s*'([^']*)'\)")
        matches = pattern.findall(sql_content)
        
        mapping = {code: name for code, name in matches}
        
        with open("data/kode_wilayah.json", "w") as f:
            json.dump(mapping, f, indent=2)
            
        print(f"Successfully converted {len(mapping)} codes to data/kode_wilayah.json")
    else:
        print(f"Failed to download SQL data. Status code: {response.status_code}")

if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
    download_spatial_data()
    download_and_convert_sql()
