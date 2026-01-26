import geopandas as gpd
from shapely.geometry import Point
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeoDecoder:
    def __init__(self, geojson_path: str):
        self.geojson_path = geojson_path
        self.gdf = None
        self._load_data()

    def _load_data(self):
        if not os.path.exists(self.geojson_path):
            logger.error(f"GeoJSON file not found at {self.geojson_path}")
            return
        
        logger.info(f"Loading GeoJSON data from {self.geojson_path}...")
        # Use pyogrio engine for faster loading if available
        try:
            self.gdf = gpd.read_file(self.geojson_path, engine='pyogrio')
        except Exception as e:
            logger.warning(f"Failed to load with pyogrio, falling back to default engine: {e}")
            self.gdf = gpd.read_file(self.geojson_path)
        
        logger.info(f"Loaded {len(self.gdf)} features.")
        # Ensure CTRS is WGS84
        if self.gdf.crs != "EPSG:4326":
            self.gdf = self.gdf.to_crs("EPSG:4326")

    def decode(self, lat: float, lon: float):
        if self.gdf is None:
            return None
        
        point = Point(lon, lat)
        # Spatial query
        # result = self.gdf[self.gdf.contains(point)] # Slow for large datasets
        
        # Use spatial index for performance
        possible_matches_index = self.gdf.sindex.query(point, predicate="contains")
        result = self.gdf.iloc[possible_matches_index]
        
        if result.empty:
            return None
        
        # Take the first match
        feature = result.iloc[0]
        
        # Mapping properties based on standard parawendy/hanifabd schema
        # Usually: PROV_CODE, KAB_CODE, KEC_CODE, DESA_CODE or similar
        # Let's try to detect the columns or mapping
        
        # Example output structure
        data = {
            "kode_wilayah": feature.get("code") or feature.get("kode") or feature.get("id_desa") or feature.get("ID") or feature.get("KODE_WILAYAH"),
            "provinsi": {
                "nama": feature.get("provinsi") or feature.get("PROVINSI") or feature.get("nm_prov"),
                "kode": feature.get("kode_prov") or feature.get("ID_PROV") or feature.get("id_prov")
            },
            "kabupaten": {
                "nama": feature.get("kabupaten") or feature.get("KABUPATEN") or feature.get("nm_kab"),
                "kode": feature.get("kode_kab") or feature.get("ID_KAB") or feature.get("id_kab")
            },
            "kecamatan": {
                "nama": feature.get("kecamatan") or feature.get("KECAMATAN") or feature.get("nm_kec"),
                "kode": feature.get("kode_kec") or feature.get("ID_KEC") or feature.get("id_kec")
            },
            "desa": {
                "nama": feature.get("desa") or feature.get("kelurahan") or feature.get("DESA") or feature.get("nm_desa"),
                "kode": feature.get("kode_desa") or feature.get("ID_DESA") or feature.get("id_desa")
            }
        }
        
        # If kode_wilayah is missing, construct it from parts if available
        if not data["kode_wilayah"] and data["desa"]["kode"]:
            data["kode_wilayah"] = data["desa"]["kode"]
            
        return data
