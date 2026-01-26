import requests
import zipfile
import io
import os

def download_data():
    url = "https://github.com/pararawendy/border-desa-indonesia-geojson/raw/master/indonesia_villages_border.geojson.zip"
    print(f"Downloading data from {url}...")
    
    response = requests.get(url)
    if response.status_code == 200:
        z = zipfile.ZipFile(io.BytesIO(response.content))
        # Find the geojson file in the zip
        geojson_file = [f for f in z.namelist() if f.endswith('.geojson')][0]
        z.extract(geojson_file, "data")
        # Rename to a standard name if needed
        os.rename(os.path.join("data", geojson_file), os.path.join("data", "indonesia_villages.geojson"))
        print("Data downloaded and extracted successfully.")
    else:
        print(f"Failed to download data. Status code: {response.status_code}")

if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
    download_data()
