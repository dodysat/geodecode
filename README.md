# Indonesia Coordinate to Kode Wilayah Geodecoder

A high-performance FastAPI service that converts geographic coordinates (latitude, longitude) into the Indonesian administrative code format (**Kode Wilayah**).

## Features

- **Accurate Geocoding**: Uses village-level (Level 4) boundary data from Kemendagri/BPS.
- **Hierarchical Breakdown**: Returns codes for Province, Regency (Kabupaten/Kota), District (Kecamatan), and Village (Desa/Kelurahan).
- **Fast Queries**: Utilizes `geopandas` with spatial indexing (R-Tree) for sub-second lookups.
- **Dockerized**: Easy deployment with Docker and Docker Compose.

## Administrative Code Format (Example)
Given coordinate `-7.892473, 110.719908`:
- **Province**: 34 (DI Yogyakarta)
- **Regency**: 03 (Gunung Kidul)
- **District**: 12 (Semin)
- **Village**: 2010 (Semin)
- **Full Code**: `34.03.12.2010`

## Getting Started

### Prerequisites
- Docker and Docker Compose

### Setup & Run

1. **Clone the repository and build the container:**
   ```bash
   docker compose up --build -d
   ```

2. **Download Boundary Data:**
   The service requires GeoJSON boundary data. Run the helper script inside the container to fetch it:
   ```bash
   docker compose exec geodecode python download_data.py
   ```
   *Note: The dataset contains over 80,000 villages and is approximately 125MB compressed.*

### API Usage

#### Convert Coordinate to Code
**Endpoint:** `GET /convert`

**Parameters:**
- `latitude` (float)
- `longitude` (float)

**Example:**
```bash
curl "http://localhost:8000/convert?latitude=-7.892473&longitude=110.719908"
```

**Response:**
```json
{
  "kode_wilayah": "34.03.12.2010",
  "provinsi": {
    "nama": "DI YOGYAKARTA",
    "kode": "34"
  },
  "kabupaten": {
    "nama": "GUNUNG KIDUL",
    "kode": "34.03"
  },
  "kecamatan": {
    "nama": "SEMIN",
    "kode": "34.03.12"
  },
  "desa": {
    "nama": "SEMIN",
    "kode": "34.03.12.2010"
  }
}
```

#### Health Check
**Endpoint:** `GET /health`

## Development

### Local Setup (without Docker)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Download data:
   ```bash
   python download_data.py
   ```
3. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

## Data Source
Boundary data is sourced from [pararawendy/border-desa-indonesia-geojson](https://github.com/pararawendy/border-desa-indonesia-geojson), which provides cleaned GeoJSON files based on BPS/BIG data.
