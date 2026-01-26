from fastapi import FastAPI, HTTPException, Query
from geodecoder import GeoDecoder
import os
import uvicorn

app = FastAPI(title="Indonesia GeoDecode Service")

# Initialize GeoDecoder
DATA_PATH = os.getenv("GEOJSON_PATH", "data/indonesia_villages.geojson")
decoder = None

@app.on_event("startup")
async def startup_event():
    global decoder
    if os.path.exists(DATA_PATH):
        decoder = GeoDecoder(DATA_PATH)
    else:
        print(f"WARNING: Data not found at {DATA_PATH}. Please run download_data.py first.")

@app.get("/convert")
async def convert(
    latitude: float = Query(..., description="Latitude of the coordinate"),
    longitude: float = Query(..., description="Longitude of the coordinate")
):
    if decoder is None:
        raise HTTPException(status_code=503, detail="GeoDecoder data not loaded. Please ensure data is available.")
    
    result = decoder.decode(latitude, longitude)
    
    if not result:
        raise HTTPException(status_code=404, detail="Coordinate not found in any administrative boundary")
    
    return result

@app.get("/health")
async def health():
    return {"status": "ok", "data_loaded": decoder is not None}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
