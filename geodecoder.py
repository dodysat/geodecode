import geopandas as gpd
from shapely.geometry import Point
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeoDecoder:
    def __init__(self, geojson_path: str, codes_path: str = None):
        self.geojson_path = geojson_path
        self.codes_path = codes_path
        self.gdf = None
        self.codes_mapping = {}
        self._load_data()
        self._load_codes()

    def _load_data(self):
        if not os.path.exists(self.geojson_path):
            logger.error(f"GeoJSON file not found at {self.geojson_path}")
            return
        
        logger.info(f"Loading data from {self.geojson_path}...")
        try:
            # Try loading as standard GeoJSON first
            # But skip if it starts with [ (custom format) to avoid fiona errors
            with open(self.geojson_path, 'r') as f:
                first_char = f.read(1)
            
            if first_char == '[':
                logger.info("Detected custom JSON array format. Skipping GeoJSON check.")
                raise ValueError("Custom format detected")
                
            self.gdf = gpd.read_file(self.geojson_path)
            logger.info(f"Loaded {len(self.gdf)} features as standard GeoJSON.")
        except Exception as e:
            logger.info("Loading as custom JSON array format...")
            try:
                import pandas as pd
                from shapely.geometry import Polygon
                
                # pd.read_json is generally faster
                df = pd.read_json(self.geojson_path)
                logger.info(f"Read {len(df)} rows from JSON.")
                
                # Convert 'border' list of points to Polygon
                # Using list comprehension for speed
                geoms = [Polygon(x) if x and len(x) >= 3 else None for x in df['border']]
                df['geometry'] = geoms
                df = df.dropna(subset=['geometry'])
                
                self.gdf = gpd.GeoDataFrame(df, crs="EPSG:4326")
                logger.info(f"Loaded {len(self.gdf)} features from custom JSON format.")
            except Exception as e2:
                logger.error(f"Failed to load data with all methods: {e2}")
                return

        # Ensure CRS is WGS84
        if self.gdf.crs is None:
            self.gdf.set_crs("EPSG:4326", inplace=True)
        elif self.gdf.crs != "EPSG:4326":
            self.gdf = self.gdf.to_crs("EPSG:4326")
        
        # Create spatial index
        _ = self.gdf.sindex

    def _load_codes(self):
        if self.codes_path and os.path.exists(self.codes_path):
            logger.info(f"Loading codes mapping from {self.codes_path}...")
            import json
            with open(self.codes_path, 'r') as f:
                self.codes_mapping = json.load(f)
            logger.info(f"Loaded {len(self.codes_mapping)} codes.")

    def _normalize_name(self, name: str) -> str:
        if not name:
            return ""
        # Remove common prefixes and whitespace
        name = str(name).upper().strip()
        prefixes = ["KABUPATEN ", "KOTA ", "KECAMATAN ", "DESA ", "KELURAHAN ", "PROVINSI "]
        for p in prefixes:
            if name.startswith(p):
                name = name[len(p):]
                break
        # Special case for DI Yogyakarta
        if "YOGYAKARTA" in name:
            return "YOGYAKARTA"
        return name

    def decode(self, lat: float, lon: float):
        if self.gdf is None:
            return None
        
        point = Point(lon, lat)
        logger.info(f"Decoding point: {point}")
        
        # Use spatial index for performance
        try:
            # 'intersects' is more robust for points
            possible_matches_index = self.gdf.sindex.query(point, predicate="intersects")
            logger.info(f"Potential matches count: {len(possible_matches_index)}")
            result = self.gdf.iloc[possible_matches_index]
        except Exception as e:
            logger.error(f"Spatial query failed: {e}")
            # Fallback to slow way
            result = self.gdf[self.gdf.intersects(point)]
            logger.info(f"Fallback matches count: {len(result)}")
        
        if result.empty:
            return None
        
        # Take the first match
        feature = result.iloc[0]
        
        # Spatial names
        s_prov = feature.get("province") or feature.get("provinsi") or feature.get("PROVINSI")
        s_kab = feature.get("district") or feature.get("kabupaten") or feature.get("KABUPATEN")
        s_kec = feature.get("sub_district") or feature.get("kecamatan") or feature.get("KECAMATAN")
        s_desa = feature.get("village") or feature.get("desa") or feature.get("kelurahan") or feature.get("DESA")

        # Normalize spatial names
        n_prov = self._normalize_name(s_prov)
        n_kab = self._normalize_name(s_kab)
        n_kec = self._normalize_name(s_kec)
        n_desa = self._normalize_name(s_desa)

        # Fallback to code from spatial if available
        code = (feature.get("code") or feature.get("kode") or feature.get("id_desa") or 
                feature.get("ID") or feature.get("KODE_WILAYAH"))

        # If code is missing, find it from names in codes_mapping
        if not code and self.codes_mapping:
            logger.info("Code missing from spatial data. Searching in codes_mapping...")
            # 1. Find all possible province codes (len 2)
            prov_codes = [c for c, n in self.codes_mapping.items() if len(c) == 2 and n_prov in self._normalize_name(n)]
            
            # 2. Find all possible village codes (usually length is 13 or similar)
            village_codes = [c for c, n in self.codes_mapping.items() if len(c) >= 10 and n_desa in self._normalize_name(n)]
            
            # Filter village codes by hierarchy
            valid_villages = []
            for vc in village_codes:
                p_code = vc[:2]
                k_code = vc[:5]
                # Check if hierarchy matches
                if p_code in prov_codes:
                    kab_official = self.codes_mapping.get(k_code, "")
                    if n_kab in self._normalize_name(kab_official):
                        valid_villages.append(vc)
            
            if valid_villages:
                code = valid_villages[0]
                logger.info(f"Found code via hierarchy lookup: {code}")

        # Helper to get official name
        def get_name(c, default):
            return self.codes_mapping.get(c, default) if c else default

        # Build detailed breakdown
        prov_code = code[:2] if code else None
        kab_code = code[:5] if code and len(code) >= 5 else None
        kec_code = code[:8] if code and len(code) >= 8 else None
        desa_code = code

        data = {
            "kode_wilayah": code,
            "provinsi": {
                "nama": get_name(prov_code, s_prov),
                "kode": prov_code
            },
            "kabupaten": {
                "nama": get_name(kab_code, s_kab),
                "kode": kab_code
            },
            "kecamatan": {
                "nama": get_name(kec_code, s_kec),
                "kode": kec_code
            },
            "desa": {
                "nama": get_name(desa_code, s_desa),
                "kode": desa_code
            }
        }
        
        return data
