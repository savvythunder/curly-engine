
import requests
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import os
import urllib.parse

# API Key Management
if os.environ.get('mars_api'):
    NASA_API_KEY = os.environ['mars_api']
else:
    NASA_API_KEY = 'DEMO_KEY'

def apod(
    date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    count: Optional[int] = None,
    thumbs: bool = False,
) -> Optional[Union[Dict, List]]:
    """
    Retrieve NASA's Astronomy Picture of the Day (APOD) data.

    Parameters:
        date (str, optional): Date in YYYY-MM-DD format for a specific image.
        start_date (str, optional): Start of a date range.
        end_date (str, optional): End of a date range (requires start_date).
        count (int, optional): Number of random images to fetch.
        thumbs (bool, optional): If True, return video thumbnails (default False).

    Returns:
        dict | list: JSON response from NASA's APOD API.
    """
    base_url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": NASA_API_KEY}

    if date:
        params["date"] = date
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if count:
        params["count"] = str(count)  # Convert to string for API
    if thumbs:
        params["thumbs"] = "true"

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching APOD data: {e}")
        return None

class Neow:
    """Near Earth Object Web Service (NeoWs) API wrapper."""
    
    def __init__(self, api_key: str = NASA_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.nasa.gov/neo/rest/v1"

    def neo_feed(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[Dict]:
        """Retrieve a list of Asteroids based on their closest approach date to Earth."""
        params = {"api_key": self.api_key}
        
        if start_date:
            params["start_date"] = start_date
        else: 
            params["start_date"] = datetime.now().strftime("%Y-%m-%d")
        
        if end_date:
            params["end_date"] = end_date
        else:
            params["end_date"] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        try:
            response = requests.get(f"{self.base_url}/feed", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching NEO feed: {e}")
            return None

    def neo_lookup(self, asteroid_id: str) -> Optional[Dict]:
        """Lookup a specific asteroid by NASA JPL ID."""
        if not asteroid_id:
            raise ValueError("Asteroid ID is required")
        
        params = {"api_key": self.api_key}
        
        try:
            response = requests.get(f"{self.base_url}/neo/{asteroid_id}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error looking up asteroid {asteroid_id}: {e}")
            return None

    def neo_browse(self) -> Optional[Dict]:
        """Browse all asteroids in the database."""
        params = {"api_key": self.api_key}
        
        try:
            response = requests.get(f"{self.base_url}/neo/browse", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error browsing NEOs: {e}")
            return None

class NasaAPI:
    """Base class for NASA API wrappers (handles requests & params)."""

    def __init__(self, api_key: str = NASA_API_KEY, start_date: Optional[str] = None, end_date: Optional[str] = None):
        self.api_key = api_key
        self.start_date = start_date
        self.end_date = end_date

    def _get(self, url: str, **extra_params) -> Optional[Dict]:
        """Internal method to handle GET requests with error handling."""
        params = {"api_key": self.api_key, **extra_params}

        # Handle optional date params
        if self.start_date:
            params.setdefault("start_date", self.start_date)
            params.setdefault("startDate", self.start_date)
        if self.end_date:
            params.setdefault("end_date", self.end_date)
            params.setdefault("endDate", self.end_date)

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return None

class Apod(NasaAPI):
    """Astronomy Picture of the Day (APOD) service."""

    BASE_URL = "https://api.nasa.gov/planetary/apod"

    def fetch(self, date: Optional[str] = None, count: Optional[int] = None, thumbs: bool = False) -> Optional[Union[Dict, List]]:
        """Get APOD data."""
        params = {}
        if date: 
            params["date"] = date
        if count: 
            params["count"] = count
        if thumbs: 
            params["thumbs"] = "true"
        return self._get(self.BASE_URL, **params)

class Donki(NasaAPI):
    """DONKI (Space Weather Database of Notifications, Knowledge, Information)."""

    BASE_URL = "https://api.nasa.gov/DONKI"

    def cme(self) -> Optional[Dict]:
        """Coronal Mass Ejections."""
        return self._get(f"{self.BASE_URL}/CME")

    def cme_analysis(self, mostAccurateOnly: bool = True, speed: Optional[int] = None,
                     halfAngle: Optional[int] = None, catalog: str = "ALL") -> Optional[Dict]:
        """CME Analysis with optional filters."""
        params = {
            "mostAccurateOnly": str(mostAccurateOnly).lower(),
            "catalog": catalog
        }
        if speed: 
            params["speed"] = speed
        if halfAngle: 
            params["halfAngle"] = halfAngle
        
        return self._get(f"{self.BASE_URL}/CMEAnalysis", **params)

    def gst(self) -> Optional[Dict]:
        """Geomagnetic Storms."""
        return self._get(f"{self.BASE_URL}/GST")

    def flr(self) -> Optional[Dict]:
        """Solar Flares."""
        return self._get(f"{self.BASE_URL}/FLR")

    def notifications(self, type: str = "all") -> Optional[Dict]:
        """Notifications (all, FLR, CME, etc.)."""
        return self._get(f"{self.BASE_URL}/notifications", type=type)

class Eonet:
    """Earth Observatory Natural Event Tracker (EONET)."""

    BASE_URL = "https://eonet.gsfc.nasa.gov/api/v2.1"

    def _get(self, endpoint: str, **params) -> Optional[Dict]:
        """Internal helper for GET requests."""
        try:
            response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching EONET data from {endpoint}: {e}")
            return None

    def events(self, source: Optional[str] = None, status: Optional[str] = None,
               limit: Optional[int] = None, days: Optional[int] = None) -> Optional[Dict]:
        """Get event data (default: open events)."""
        params = {}
        if source: params["source"] = source
        if status: params["status"] = status
        if limit: params["limit"] = limit
        if days: params["days"] = days
        return self._get("events", **params)

    def categories(self, category_id: Optional[int] = None, source: Optional[str] = None,
                   status: Optional[str] = None, limit: Optional[int] = None, days: Optional[int] = None) -> Optional[Dict]:
        """Get categories or filter events by category."""
        endpoint = f"categories/{category_id}" if category_id else "categories"
        params = {}
        if source: params["source"] = source
        if status: params["status"] = status
        if limit: params["limit"] = limit
        if days: params["days"] = days
        return self._get(endpoint, **params)

    def sources(self) -> Optional[Dict]:
        """Get list of event sources."""
        return self._get("sources")

    def layers(self, category_id: Optional[int] = None) -> Optional[Dict]:
        """Get visualization layers (maps)."""
        endpoint = f"layers/{category_id}" if category_id else "layers"
        return self._get(endpoint)

class Epic(NasaAPI):
    """Earth Polychromatic Imaging Camera (EPIC) API wrapper."""

    BASE_URL = "https://api.nasa.gov/EPIC/api"

    def natural_latest(self) -> Optional[List]:
        """Metadata for the most recent natural color image."""
        return self._get(f"{self.BASE_URL}/natural/images")

    def natural_by_date(self, date: str) -> Optional[List]:
        """Metadata for natural color imagery on a specific date (YYYY-MM-DD)."""
        return self._get(f"{self.BASE_URL}/natural/date/{date}")

    def natural_all_dates(self) -> Optional[List]:
        """List all dates with available natural color imagery."""
        return self._get(f"{self.BASE_URL}/natural/all")

    def enhanced_latest(self) -> Optional[List]:
        """Metadata for the most recent enhanced color image."""
        return self._get(f"{self.BASE_URL}/enhanced/images")

    def enhanced_by_date(self, date: str) -> Optional[List]:
        """Metadata for enhanced color imagery on a specific date (YYYY-MM-DD)."""
        return self._get(f"{self.BASE_URL}/enhanced/date/{date}")

    @staticmethod
    def image_url(date: str, image_name: str, color_type: str = "natural") -> str:
        """Construct direct PNG image URL from date and image name."""
        y, m, d = date.split("-")
        return f"https://api.nasa.gov/EPIC/archive/{color_type}/{y}/{m}/{d}/png/{image_name}.png?api_key={NASA_API_KEY}"

class InSight(NasaAPI):
    """InSight Mars Weather Service API wrapper."""

    BASE_URL = "https://api.nasa.gov/insight_weather/"

    def __init__(self, api_key: str = NASA_API_KEY, version: float = 1.0, feedtype: str = "json"):
        super().__init__(api_key)
        self.version = version
        self.feedtype = feedtype

    def latest_weather(self) -> Optional[Dict]:
        """Returns the latest available per-Sol weather summary data."""
        params = {
            "feedtype": self.feedtype,
            "ver": self.version
        }
        return self._get(self.BASE_URL, **params)

class CuriosityRover(NasaAPI):
    """NASA Mars Rover Photos API wrapper."""

    BASE_URL = "https://api.nasa.gov/mars-photos/api/v1/rovers"

    def photos_by_sol(self, rover: str, sol: int, camera: Optional[str] = None, page: int = 1) -> Optional[Dict]:
        """Get photos taken by a rover on a specific Martian sol."""
        params = {"sol": sol, "page": page}
        if camera: 
            params["camera"] = camera
        return self._get(f"{self.BASE_URL}/{rover}/photos", **params)

    def photos_by_earth_date(self, rover: str, earth_date: str, camera: Optional[str] = None, page: int = 1) -> Optional[Dict]:
        """Get photos taken by a rover on a specific Earth date (YYYY-MM-DD)."""
        params = {"earth_date": earth_date, "page": page}
        if camera: 
            params["camera"] = camera
        return self._get(f"{self.BASE_URL}/{rover}/photos", **params)

    def mission_manifest(self, rover: str) -> Optional[Dict]:
        """Get the mission manifest for a rover."""
        return self._get(f"{self.BASE_URL}/{rover}/manifests/{rover}")

class NasaImages:
    """NASA Image and Video Library API wrapper."""

    BASE_URL = "https://images-api.nasa.gov"

    def _get(self, endpoint: str, **params) -> Optional[Dict]:
        """Internal helper for GET requests."""
        try:
            response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching NASA Images data: {e}")
            return None

    def search(self, q: str, media_type: Optional[str] = None, year_start: Optional[int] = None, year_end: Optional[int] = None) -> Optional[Dict]:
        """Search NASA media by keyword and optional filters."""
        params = {"q": q}
        if media_type: params["media_type"] = media_type
        if year_start: params["year_start"] = year_start
        if year_end: params["year_end"] = year_end
        return self._get("search", **params)

    def asset(self, nasa_id: str) -> Optional[Dict]:
        """Get all media assets for a given NASA media ID."""
        return self._get(f"asset/{nasa_id}")

    def metadata(self, nasa_id: str) -> Optional[Dict]:
        """Get metadata for a given NASA media ID."""
        return self._get(f"metadata/{nasa_id}")

    def captions(self, nasa_id: str) -> Optional[Dict]:
        """Get captions for a video media asset."""
        return self._get(f"captions/{nasa_id}")

class OSDR:
    """
    NASA Open Science Data Repository (OSDR) API wrapper.
    
    Provides comprehensive access to NASA's life sciences data including:
    - Study files and metadata
    - Search capabilities
    - Experiments, missions, payloads, hardware, vehicles, subjects, and biospecimens
    """
    
    BASE_URL = "https://osdr.nasa.gov"
    
    def __init__(self):
        """Initialize OSDR API client."""
        pass
    
    def _get(self, url: str, **params) -> Optional[Dict]:
        """Internal helper for GET requests with error handling."""
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching OSDR data from {url}: {e}")
            return None
    
    def get_study_files(self, study_ids: Union[str, int, List[Union[str, int]]], 
                       page: int = 0, size: int = 25, all_files: bool = False) -> Optional[Dict]:
        """
        Get data file metadata for one or more NASA OSDR study datasets.
        
        Args:
            study_ids: Single ID, list of IDs, or comma-separated string of study IDs/ranges
            page: Page number for pagination (starts from 0)
            size: Number of results per page (max 25)
            all_files: Include hidden files if True
            
        Returns:
            JSON response with file metadata including download URLs
        """
        # Format study IDs
        if isinstance(study_ids, list):
            study_ids_str = ",".join(str(id) for id in study_ids)
        else:
            study_ids_str = str(study_ids)
        
        url = f"{self.BASE_URL}/osdr/data/osd/files/{study_ids_str}/"
        params = {
            "page": page,
            "size": size,
            "all_files": str(all_files).lower()
        }
        
        return self._get(url, **params)
    
    def get_study_metadata(self, study_id: Union[str, int]) -> Optional[Dict]:
        """
        Get complete metadata for a specific study.
        
        Args:
            study_id: Single study accession number
            
        Returns:
            JSON response with complete study metadata
        """
        url = f"{self.BASE_URL}/osdr/data/osd/meta/{study_id}"
        return self._get(url)
    
    def search_studies(self, term: Optional[str] = None, from_page: int = 0, size: int = 10,
                      data_source: str = "cgene", sort_field: Optional[str] = None, 
                      sort_order: str = "ASC", filters: Optional[Dict[str, str]] = None) -> Optional[Dict]:
        """
        Search study datasets by keywords and filters.
        
        Args:
            term: Search keyword
            from_page: Starting page (default 0)
            size: Results per page (default 10)
            data_source: Data source (cgene, nih_geo, ebi_pride, mg_rast)
            sort_field: Field to sort by
            sort_order: ASC or DESC
            filters: Dictionary of filter field/value pairs
            
        Returns:
            JSON response with search results
        """
        url = f"{self.BASE_URL}/osdr/data/search"
        params = {
            "from": from_page,
            "size": size,
            "type": data_source,
            "order": sort_order
        }
        
        if term:
            params["term"] = term
        if sort_field:
            params["sort"] = sort_field
        
        # Add filters
        if filters:
            for field, value in filters.items():
                params[f"ffield"] = field
                params[f"fvalue"] = value
        
        return self._get(url, **params)
    
    def search_simple(self, query: str, data_source: str = "cgene") -> Optional[str]:
        """
        Simple search interface that returns HTML.
        
        Args:
            query: Search terms (supports AND, OR, NOT operators)
            data_source: cgene, nih_geo_gse, ebi_pride, or mg_rast
            
        Returns:
            HTML response as string
        """
        url = f"{self.BASE_URL}/bio/repo/search"
        params = {
            "q": query,
            "data_source": data_source
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error performing simple search: {e}")
            return None
    
    # Metadata APIs for different data types
    def get_experiments(self) -> Optional[List[Dict]]:
        """Get all experiments."""
        url = f"{self.BASE_URL}/geode-py/ws/api/experiments"
        return self._get(url)
    
    def get_experiment(self, identifier: str) -> Optional[Dict]:
        """Get single experiment by identifier."""
        url = f"{self.BASE_URL}/geode-py/ws/api/experiment/{identifier}"
        return self._get(url)
    
    def get_missions(self) -> Optional[List[Dict]]:
        """Get all missions."""
        url = f"{self.BASE_URL}/geode-py/ws/api/missions"
        return self._get(url)
    
    def get_mission(self, identifier: str) -> Optional[Dict]:
        """Get single mission by identifier."""
        url = f"{self.BASE_URL}/geode-py/ws/api/mission/{identifier}"
        return self._get(url)
    
    def get_payloads(self) -> Optional[List[Dict]]:
        """Get all payloads."""
        url = f"{self.BASE_URL}/geode-py/ws/api/payloads"
        return self._get(url)
    
    def get_payload(self, identifier: str) -> Optional[Dict]:
        """Get single payload by identifier."""
        url = f"{self.BASE_URL}/geode-py/ws/api/payload/{identifier}"
        return self._get(url)
    
    def get_hardware(self) -> Optional[List[Dict]]:
        """Get all hardware."""
        url = f"{self.BASE_URL}/geode-py/ws/api/hardware"
        return self._get(url)
    
    def get_hardware_item(self, identifier: str) -> Optional[Dict]:
        """Get single hardware item by identifier."""
        url = f"{self.BASE_URL}/geode-py/ws/api/hardware/{identifier}"
        return self._get(url)
    
    def get_vehicles(self) -> Optional[List[Dict]]:
        """Get all vehicles."""
        url = f"{self.BASE_URL}/geode-py/ws/api/vehicles"
        return self._get(url)
    
    def get_vehicle(self, identifier: str) -> Optional[Dict]:
        """Get single vehicle by identifier."""
        url = f"{self.BASE_URL}/geode-py/ws/api/vehicle/{identifier}"
        return self._get(url)
    
    def get_subjects(self) -> Optional[List[Dict]]:
        """Get all subjects."""
        url = f"{self.BASE_URL}/geode-py/ws/api/subjects"
        return self._get(url)
    
    def get_subject(self, identifier: str) -> Optional[Dict]:
        """Get single subject by identifier."""
        url = f"{self.BASE_URL}/geode-py/ws/api/subject/{identifier}"
        return self._get(url)
    
    def get_biospecimens(self) -> Optional[List[Dict]]:
        """Get all biospecimens."""
        url = f"{self.BASE_URL}/geode-py/ws/api/biospecimens"
        return self._get(url)
    
    def get_biospecimen(self, identifier: str) -> Optional[Dict]:
        """Get single biospecimen by identifier."""
        url = f"{self.BASE_URL}/geode-py/ws/api/biospecimen/{identifier}"
        return self._get(url)
    
    def get_file_download_url(self, study_id: str, filename: str) -> str:
        """
        Construct download URL for a specific file.
        
        Args:
            study_id: Study identifier (e.g., "OSD-87")
            filename: Name of the file to download
            
        Returns:
            Complete download URL
        """
        return f"{self.BASE_URL}/geode-py/ws/studies/{study_id}/download?source=datamanager&file={filename}"

# Legacy class for backward compatibility (keep the original simple implementation)
class osdp:
    """
    Legacy OSDR class - kept for backward compatibility.
    Use OSDR class for enhanced functionality.
    """
    def __init__(self, OSD_STUDY_IDs: Union[int, List[int]] = 1, 
                 CURRENT_PAGE_NUMBER: int = 1, RESULTS_PER_PAGE: int = 100, ALL_FILES: bool = False):
        self.OSD_STUDY_IDs = OSD_STUDY_IDs
        self.CURRENT_PAGE_NUMBER = CURRENT_PAGE_NUMBER
        self.RESULTS_PER_PAGE = RESULTS_PER_PAGE
        self.ALL_FILES = ALL_FILES
        
        # Format study IDs for URL
        if isinstance(OSD_STUDY_IDs, list):
            study_ids_str = ",".join(str(id) for id in OSD_STUDY_IDs)
        else:
            study_ids_str = str(OSD_STUDY_IDs)
            
        self.syntax_url = f"https://osdr.nasa.gov/osdr/data/osd/files/{study_ids_str}/?page={CURRENT_PAGE_NUMBER}&size={RESULTS_PER_PAGE}&all_files={ALL_FILES}"

    def get_osdr_study_files(self) -> Optional[Dict]:
        """Get OSDR study files using the configured parameters."""
        try:
            response = requests.get(self.syntax_url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching OSDR study files: {e}")
            return None
