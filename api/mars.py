import requests
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import os
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

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

  def neo_feed(self,
               start_date: Optional[str] = None,
               end_date: Optional[str] = None) -> Optional[Dict]:
    """Retrieve a list of Asteroids based on their closest approach date to Earth."""
    params = {"api_key": self.api_key}

    if start_date:
      params["start_date"] = start_date
    else:
      params["start_date"] = datetime.now().strftime("%Y-%m-%d")

    if end_date:
      params["end_date"] = end_date
    else:
      params["end_date"] = (datetime.now() +
                            timedelta(days=7)).strftime("%Y-%m-%d")

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
      response = requests.get(f"{self.base_url}/neo/{asteroid_id}",
                              params=params)
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

  def __init__(self,
               api_key: str = NASA_API_KEY,
               start_date: Optional[str] = None,
               end_date: Optional[str] = None):
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

  def fetch(self,
            date: Optional[str] = None,
            count: Optional[int] = None,
            thumbs: bool = False) -> Optional[Union[Dict, List]]:
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

  def cme_analysis(self,
                   mostAccurateOnly: bool = True,
                   speed: Optional[int] = None,
                   halfAngle: Optional[int] = None,
                   catalog: str = "ALL") -> Optional[Dict]:
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

  def events(self,
             source: Optional[str] = None,
             status: Optional[str] = None,
             limit: Optional[int] = None,
             days: Optional[int] = None) -> Optional[Dict]:
    """Get event data (default: open events)."""
    params = {}
    if source: params["source"] = source
    if status: params["status"] = status
    if limit: params["limit"] = limit
    if days: params["days"] = days
    return self._get("events", **params)

  def categories(self,
                 category_id: Optional[int] = None,
                 source: Optional[str] = None,
                 status: Optional[str] = None,
                 limit: Optional[int] = None,
                 days: Optional[int] = None) -> Optional[Dict]:
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
  def image_url(date: str,
                image_name: str,
                color_type: str = "natural") -> str:
    """Construct direct PNG image URL from date and image name."""
    y, m, d = date.split("-")
    return f"https://api.nasa.gov/EPIC/archive/{color_type}/{y}/{m}/{d}/png/{image_name}.png?api_key={NASA_API_KEY}"


class InSight(NasaAPI):
  """InSight Mars Weather Service API wrapper."""

  BASE_URL = "https://api.nasa.gov/insight_weather/"

  def __init__(self,
               api_key: str = NASA_API_KEY,
               version: float = 1.0,
               feedtype: str = "json"):
    super().__init__(api_key)
    self.version = version
    self.feedtype = feedtype

  def latest_weather(self) -> Optional[Dict]:
    """Returns the latest available per-Sol weather summary data."""
    params = {"feedtype": self.feedtype, "ver": self.version}
    return self._get(self.BASE_URL, **params)


class CuriosityRover(NasaAPI):
  """NASA Mars Rover Photos API wrapper."""

  BASE_URL = "https://api.nasa.gov/mars-photos/api/v1/rovers"

  def photos_by_sol(self,
                    rover: str,
                    sol: int,
                    camera: Optional[str] = None,
                    page: int = 1) -> Optional[Dict]:
    """Get photos taken by a rover on a specific Martian sol."""
    params = {"sol": sol, "page": page}
    if camera:
      params["camera"] = camera
    return self._get(f"{self.BASE_URL}/{rover}/photos", **params)

  def photos_by_earth_date(self,
                           rover: str,
                           earth_date: str,
                           camera: Optional[str] = None,
                           page: int = 1) -> Optional[Dict]:
    """Get photos taken by a rover on a specific Earth date (YYYY-MM-DD)."""
    params = {"earth_date": earth_date, "page": page}
    if camera:
      params["camera"] = camera
    return self._get(f"{self.BASE_URL}/{rover}/photos", **params)

  def mission_manifest(self, rover: str) -> Optional[Dict]:
    """Get the mission manifest for a rover."""
    return self._get(f"{self.BASE_URL}/{rover}")


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

  def search(self,
             q: str,
             media_type: Optional[str] = None,
             year_start: Optional[int] = None,
             year_end: Optional[int] = None) -> Optional[Dict]:
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

  def __init__(self, timeout: int = 30):
    """Initialize OSDR API client with configurable timeout."""
    self.timeout = timeout
    self.session = requests.Session()
    self.session.headers.update({
      'User-Agent': 'NASA-OSDR-Python-Client/1.0',
      'Accept': 'application/json'
    })

  def _get(self, url: str, **params) -> Optional[Dict]:
    """Internal helper for GET requests with enhanced error handling."""
    try:
      response = self.session.get(url, params=params, timeout=self.timeout)
      response.raise_for_status()
      
      # Handle empty responses
      if not response.content:
        return {"success": False, "message": "Empty response from server"}
      
      return response.json()
    except requests.Timeout:
      print(f"Timeout error for {url} - request took longer than {self.timeout} seconds")
      return None
    except requests.HTTPError as e:
      print(f"HTTP error {e.response.status_code} for {url}: {e}")
      return None
    except requests.RequestException as e:
      print(f"Request error for {url}: {e}")
      return None
    except ValueError as e:
      print(f"JSON decode error for {url}: {e}")
      return None

  def get_study_files(self,
                      study_ids: Union[str, int, List[Union[str, int]]],
                      page: int = 0,
                      size: int = 25,
                      all_files: bool = False,
                      file_types: Optional[List[str]] = None) -> Optional[Dict]:
    """
        Get data file metadata for one or more NASA OSDR study datasets.
        
        Args:
            study_ids: Single ID, list of IDs, or comma-separated string of study IDs/ranges
            page: Page number for pagination (starts from 0)
            size: Number of results per page (max 25)
            all_files: Include hidden files if True
            file_types: Filter by file extensions (e.g., ['zip', 'csv', 'txt'])
            
        Returns:
            JSON response with file metadata including download URLs
        """
    # Validate inputs
    if size > 25:
      print("Warning: Maximum size is 25, setting to 25")
      size = 25
    
    if page < 0:
      print("Warning: Page cannot be negative, setting to 0")
      page = 0

    # Format study IDs
    if isinstance(study_ids, list):
      study_ids_str = ",".join(str(id) for id in study_ids)
    else:
      study_ids_str = str(study_ids)

    url = f"{self.BASE_URL}/osdr/data/osd/files/{study_ids_str}/"
    params = {"page": page, "size": size, "all_files": str(all_files).lower()}

    result = self._get(url, **params)
    
    # Post-process to filter by file types if specified
    if result and file_types and result.get('success'):
      filtered_studies = {}
      for study_id, study_data in result.get('studies', {}).items():
        filtered_files = []
        for file_info in study_data.get('study_files', []):
          file_name = file_info.get('file_name', '')
          if any(file_name.lower().endswith(f'.{ext.lower()}') for ext in file_types):
            filtered_files.append(file_info)
        
        if filtered_files:
          study_data_copy = study_data.copy()
          study_data_copy['study_files'] = filtered_files
          study_data_copy['file_count'] = len(filtered_files)
          filtered_studies[study_id] = study_data_copy
      
      result['studies'] = filtered_studies
    
    return result

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

  def search_studies(
      self,
      term: Optional[str] = None,
      from_page: int = 0,
      size: int = 10,
      data_source: str = "cgene",
      sort_field: Optional[str] = None,
      sort_order: str = "ASC",
      filters: Optional[Dict[str, str]] = None) -> Optional[Dict]:
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

  def search_simple(self,
                    query: str,
                    data_source: str = "cgene") -> Optional[str]:
    """
        Simple search interface that returns HTML.
        
        Args:
            query: Search terms (supports AND, OR, NOT operators)
            data_source: cgene, nih_geo_gse, ebi_pride, or mg_rast
            
        Returns:
            HTML response as string
        """
    url = f"{self.BASE_URL}/bio/repo/search"
    params = {"q": query, "data_source": data_source}

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
  
  def bulk_download_urls(self, study_id: str, file_types: Optional[List[str]] = None) -> List[str]:
    """
        Get download URLs for all files in a study.
        
        Args:
            study_id: Study identifier 
            file_types: Filter by file extensions (e.g., ['zip', 'csv'])
            
        Returns:
            List of download URLs
        """
    study_files = self.get_study_files(study_id, size=25, all_files=True, file_types=file_types)
    urls = []
    
    if study_files and study_files.get('success'):
      studies = study_files.get('studies', {})
      for study_data in studies.values():
        for file_info in study_data.get('study_files', []):
          filename = file_info.get('file_name')
          if filename:
            urls.append(self.get_file_download_url(study_id, filename))
    
    return urls
  
  def search_advanced(self, 
                     keywords: Optional[str] = None,
                     organism: Optional[str] = None,
                     study_type: Optional[str] = None,
                     factor_name: Optional[str] = None,
                     date_range: Optional[tuple] = None,
                     size: int = 10) -> Optional[Dict]:
    """
        Advanced search with multiple filter options.
        
        Args:
            keywords: Search terms
            organism: Organism filter (e.g., "Mus musculus")
            study_type: Type of study
            factor_name: Experimental factor
            date_range: Tuple of (start_date, end_date) in YYYY-MM-DD format
            size: Number of results
            
        Returns:
            Search results with metadata
        """
    filters = {}
    
    if organism:
      filters["organism"] = organism
    if study_type:
      filters["study_type"] = study_type  
    if factor_name:
      filters["factor_name"] = factor_name
    if date_range and len(date_range) == 2:
      filters["publication_date_start"] = date_range[0]
      filters["publication_date_end"] = date_range[1]
    
    return self.search_studies(
      term=keywords,
      size=size,
      filters=filters if filters else None
    )
  
  def get_study_statistics(self) -> Optional[Dict]:
    """
        Get overview statistics about OSDR repository.
        
        Returns:
            Dictionary with counts of studies, experiments, missions, etc.
        """
    stats = {}
    
    try:
      # Get counts for different data types
      experiments = self.get_experiments()
      missions = self.get_missions() 
      vehicles = self.get_vehicles()
      payloads = self.get_payloads()
      
      stats['experiments_count'] = len(experiments) if experiments else 0
      stats['missions_count'] = len(missions) if missions else 0
      stats['vehicles_count'] = len(vehicles) if vehicles else 0
      stats['payloads_count'] = len(payloads) if payloads else 0
      
      # Try to get study count from search
      search_result = self.search_studies(size=1)
      if search_result:
        stats['total_studies'] = search_result.get('hits', 0)
      
      stats['last_updated'] = datetime.now().isoformat()
      
    except Exception as e:
      print(f"Error gathering statistics: {e}")
      return None
    
    return stats


# Legacy class for backward compatibility (keep the original simple implementation)
class osdp:
  """
    Legacy OSDR class - kept for backward compatibility.
    Use OSDR class for enhanced functionality.
    """

  def __init__(self,
               OSD_STUDY_IDs: Union[int, List[int]] = 1,
               CURRENT_PAGE_NUMBER: int = 1,
               RESULTS_PER_PAGE: int = 100,
               ALL_FILES: bool = False):
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


class SSCWebClient:
  """
    Python client for NASA's Satellite Situation Center Web (SSCWeb) API.
    Provides methods to query spacecraft location data and metadata.
    """

  BASE_URL = "https://sscweb.gsfc.nasa.gov/WS/sscr/2"

  def __init__(self, timeout: int = 10):
    """
        Initialize SSCWeb client.

        Args:
            timeout (int): Timeout for API requests in seconds. Default is 10.
        """
    self.timeout = timeout

  def get_satellite_list(self) -> List[str]:
    """
        Fetch available satellites supported by SSCWeb.

        Returns:
            List[str]: List of satellite names.
        """
    url = f"{self.BASE_URL}/satellites"
    response = requests.get(url, timeout=self.timeout)
    response.raise_for_status()
    data = response.json()
    return [sat['Id'] for sat in data.get('Satellite', [])]

  def get_satellite_positions(self,
                              satellites: List[str],
                              start_time: str,
                              end_time: str,
                              coord_system: str = "GSE") -> Dict[str, Any]:
    """
        Fetch spacecraft positions for given satellites and time range.

        Args:
            satellites (List[str]): List of satellite IDs (e.g. ["ace", "wind"]).
            start_time (str): Start time in ISO format, e.g. "2022-01-01T00:00:00Z".
            end_time (str): End time in ISO format, e.g. "2022-01-02T00:00:00Z".
            coord_system (str): Coordinate system (default: "GSE").

        Returns:
            Dict[str, Any]: JSON response containing position data.
        """
    url = f"{self.BASE_URL}/locations"
    params = {
        "satellites": ",".join(satellites),
        "startTime": start_time,
        "endTime": end_time,
        "coordinatesystem": coord_system
    }
    response = requests.get(url, params=params, timeout=self.timeout)
    response.raise_for_status()
    return response.json()

  def get_observatories(self) -> List[Dict[str, Any]]:
    """
        Fetch metadata about available observatories.

        Returns:
            List[Dict[str, Any]]: List of observatory metadata.
        """
    url = f"{self.BASE_URL}/observatories"
    response = requests.get(url, timeout=self.timeout)
    response.raise_for_status()
    return response.json().get("Observatory", [])


class SSDCNEOSClient:
  """
    Python client for NASA JPL's SSD (Solar System Dynamics) and CNEOS (Center for Near-Earth Object Studies) APIs.
    Provides access to close-approach data (CAD), Fireball data, Mission Design,
    NHATS, Scout, and Sentry services.
    """

  BASE_URL = "https://ssd-api.jpl.nasa.gov"

  def __init__(self, timeout: int = 10):
    """
        Initialize the SSD/CNEOS API client.

        Args:
            timeout (int): Timeout for requests in seconds. Default = 10.
        """
    self.timeout = timeout

  def _get(self,
           endpoint: str,
           params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Internal helper for GET requests with error handling."""
    url = f"{self.BASE_URL}/{endpoint}"
    response = requests.get(url, params=params, timeout=self.timeout)
    response.raise_for_status()
    return response.json()

  # ---- CAD (Close Approach Data) ----
  def get_cad(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
        Fetch asteroid and comet close-approach data.

        Args:
            params (Dict[str, Any], optional): Query parameters like 'date-min', 'date-max', 'dist-max', etc.

        Returns:
            Dict[str, Any]: JSON response with CAD results.
        """
    return self._get("cad.api", params)

  # ---- Fireball ----
  def get_fireballs(self,
                    params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
        Fetch fireball atmospheric impact data.

        Args:
            params (Dict[str, Any], optional): Query parameters like 'date-min', 'date-max', 'energy-min', etc.

        Returns:
            Dict[str, Any]: JSON response with fireball records.
        """
    return self._get("fireball.api", params)

  # ---- Mission Design ----
  def get_mission_design(self,
                         params: Optional[Dict[str,
                                               Any]] = None) -> Dict[str, Any]:
    """
        Fetch mission design data for small bodies.

        Args:
            params (Dict[str, Any], optional): Query parameters like 'des' (designation).

        Returns:
            Dict[str, Any]: JSON response with mission design details.
        """
    return self._get("mdesign.api", params)

  # ---- NHATS ----
  def get_nhats(self,
                params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
        Fetch NHATS (human-accessible NEOs) data.

        Args:
            params (Dict[str, Any], optional): Query parameters like 'dv-min', 'dv-max', 'dur-max', etc.

        Returns:
            Dict[str, Any]: JSON response with NHATS data.
        """
    return self._get("nhats.api", params)

  # ---- Scout ----
  def get_scout(self,
                params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
        Fetch near-realtime data from CNEOS Scout system.

        Args:
            params (Dict[str, Any], optional): Query parameters like 'des', 'orb', 'cov'.

        Returns:
            Dict[str, Any]: JSON response with Scout results.
        """
    return self._get("scout.api", params)

  # ---- Sentry ----
  def get_sentry(self,
                 params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
        Fetch impact risk assessment data from CNEOS Sentry system.

        Args:
            params (Dict[str, Any], optional): Modes include:
                - 'O' (object-specific details)
                - 'S' (summary table)
                - 'V' (virtual impactor table)
                - 'R' (removed objects)

        Returns:
            Dict[str, Any]: JSON response with Sentry risk results.
        """
    return self._get("sentry.api", params)


class TechPortClient:
  """
  Python client for NASA's TechPort API.
  Provides access to NASA technology project data.
  """

  BASE_URL = "https://techport.nasa.gov/api"

  def __init__(self, api_key: str = "DEMO_KEY", timeout: int = 10):
    """
      Initialize TechPort client.

      Args:
          api_key (str): NASA API key (default: DEMO_KEY).
          timeout (int): Timeout for requests in seconds. Default = 10.
      """
    self.api_key = api_key
    self.timeout = timeout

  def _get(self,
           endpoint: str,
           params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Internal helper for GET requests with API key injection."""
    if params is None:
      params = {}
    params["api_key"] = self.api_key

    url = f"{self.BASE_URL}/{endpoint}"
    response = requests.get(url, params=params, timeout=self.timeout)
    response.raise_for_status()
    return response.json()

  # ---- Projects ----
  def get_project(self, project_id: int) -> Dict[str, Any]:
    """
      Fetch metadata for a single TechPort project.

      Args:
          project_id (int): TechPort project ID.

      Returns:
          Dict[str, Any]: JSON response with project details.
      """
    return self._get(f"projects/{project_id}")

  def get_projects(self) -> Dict[str, Any]:
    """
      Fetch a list of all TechPort projects (IDs and titles).

      Returns:
          Dict[str, Any]: JSON response containing projects.
      """
    return self._get("projects")

  def get_projects_updated_since(self, date: str) -> Dict[str, Any]:
    """
      Fetch all projects updated since a given date.

      Args:
          date (str): Date in format 'YYYY-MM-DD'.

      Returns:
          Dict[str, Any]: JSON response with updated projects.
      """
    return self._get(f"projects", {"updatedSince": date})

  # ---- Additional Endpoints (Organizations, etc.) ----
  def get_organizations(self) -> Dict[str, Any]:
    """
      Fetch a list of NASA organizations available in TechPort.

      Returns:
          Dict[str, Any]: JSON response containing organizations.
      """
    return self._get("organizations")

  def get_project_by_org(self, org_id: int) -> Dict[str, Any]:
    """
      Fetch projects associated with a specific organization.

      Args:
          org_id (int): Organization ID.

      Returns:
          Dict[str, Any]: JSON response with projects for that organization.
      """
    return self._get(f"organizations/{org_id}/projects")


class TechTransferClient:
  """
  Python client for NASA's TechTransfer API.
  Provides access to NASA patents, software, and spinoffs.
  """

  BASE_URL = "https://api.nasa.gov/techtransfer"

  def __init__(self, api_key: str = "NASA_API_KEY", timeout: int = 10):
    """
      Initialize TechTransfer client.

      Args:
          api_key (str): NASA API key (default = NASA_API_KEY).
          timeout (int): Timeout for API requests in seconds. Default = 10.
      """
    self.api_key = api_key
    self.timeout = timeout

  def _get(self, endpoint: str, query: str) -> Dict[str, Any]:
    """
      Internal helper for GET requests.

      Args:
          endpoint (str): API endpoint (patent, software, spinoff).
          query (str): Search term.

      Returns:
          Dict[str, Any]: JSON response.
      """
    url = f"{self.BASE_URL}/{endpoint}/"
    params = {"query": query, "api_key": self.api_key}
    response = requests.get(url, params=params, timeout=self.timeout)
    response.raise_for_status()
    return response.json()

  # ---- Patents ----
  def search_patents(self, keyword: str) -> Dict[str, Any]:
    """
      Search NASA patents by keyword.

      Args:
          keyword (str): Search term for patents.

      Returns:
          Dict[str, Any]: JSON response with patents.
      """
    return self._get("patent", keyword)

  def search_patent_issued(self, keyword: str) -> Dict[str, Any]:
    """
      Search NASA patents by issued details.

      Args:
          keyword (str): Search term for issued patents.

      Returns:
          Dict[str, Any]: JSON response with issued patents.
      """
    return self._get("patent_issued", keyword)

  # ---- Software ----
  def search_software(self, keyword: str) -> Dict[str, Any]:
    """
      Search NASA software by keyword.

      Args:
          keyword (str): Search term for software.

      Returns:
          Dict[str, Any]: JSON response with software.
      """
    return self._get("software", keyword)

  # ---- Spinoff ----
  def search_spinoffs(self, keyword: str) -> Dict[str, Any]:
    """
      Search NASA spinoffs by keyword.

      Args:
          keyword (str): Search term for spinoffs.

      Returns:
          Dict[str, Any]: JSON response with spinoffs.
      """
    return self._get("spinoff", keyword)


class TLEClient:
  """
    Python client for the TLE (Two-Line Element Set) API.
    Provides access to daily-updated orbital element sets from CelesTrak.
    """

  BASE_URL = "http://tle.ivanstanojevic.me/api/tle"

  def __init__(self, timeout: int = 10):
    """
        Initialize TLE client.

        Args:
            timeout (int): Timeout for API requests in seconds. Default = 10.
        """
    self.timeout = timeout

  def _get(self,
           url: str,
           params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Internal GET helper with error handling."""
    response = requests.get(url, params=params, timeout=self.timeout)
    response.raise_for_status()
    return response.json()

  # ---- Search by name ----
  def search(self, query: str) -> Dict[str, Any]:
    """
        Search TLE records by satellite name.

        Args:
            query (str): Satellite name (e.g., 'ISS', 'Starlink').

        Returns:
            Dict[str, Any]: JSON response containing matching satellites and TLEs.
        """
    return self._get(self.BASE_URL, {"search": query})

  # ---- Get by NORAD ID ----
  def get_by_id(self, satellite_id: int) -> Dict[str, Any]:
    """
        Fetch a TLE record by NORAD catalog number.

        Args:
            satellite_id (int): NORAD ID (e.g., 25544 for ISS).

        Returns:
            Dict[str, Any]: JSON response with the TLE record.
        """
    return self._get(f"{self.BASE_URL}/{satellite_id}")


class TrekWMTSClient:
  """
    Python client for NASA Trek WMTS services (Moon, Mars, Vesta).
    Supports fetching WMTS capabilities and downloading map tiles.
    """

  def __init__(self, base_url: str, timeout: int = 10):
    """
        Args:
            base_url (str): The WMTS endpoint, e.g.,
                "https://trek.nasa.gov/tiles/Moon/EQ/{LAYER}/1.0.0"
            timeout (int): Request timeout (seconds). Default = 10.
        """
    self.base_url = base_url.rstrip("/")
    self.timeout = timeout

  def get_capabilities(self, capabilities_url: str) -> Dict[str, Any]:
    """
        Fetch and parse WMTS GetCapabilities XML.

        Args:
            capabilities_url (str): URL to the WMTS GetCapabilities XML.

        Returns:
            Dict[str, Any]: Available layers, styles, tile matrix sets.
        """
    response = requests.get(capabilities_url, timeout=self.timeout)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    namespaces = {
        "wmts": "http://www.opengis.net/wmts/1.0",
        "ows": "http://www.opengis.net/ows/1.1",
    }

    layers = []
    for layer in root.findall(".//wmts:Layer", namespaces):
      identifier = layer.find("ows:Identifier", namespaces).text
      title = layer.find("ows:Title", namespaces).text
      layers.append({"id": identifier, "title": title})

    return {"layers": layers}

  def get_tile_url(
      self,
      style: str,
      tile_matrix_set: str,
      tile_matrix: str,
      tile_row: int,
      tile_col: int,
      ext: str = "jpg",
  ) -> str:
    """
        Construct a WMTS tile URL.

        Args:
            style (str): Layer style identifier.
            tile_matrix_set (str): TileMatrixSet identifier.
            tile_matrix (str): Zoom level identifier.
            tile_row (int): Tile row index.
            tile_col (int): Tile column index.
            ext (str): Image format, "jpg" or "png". Default = "jpg".

        Returns:
            str: Fully formed WMTS tile URL.
        """
    return (f"{self.base_url}/{style}/{tile_matrix_set}/"
            f"{tile_matrix}/{tile_row}/{tile_col}.{ext}")

  def download_tile(
      self,
      url: str,
      save_path: Optional[Path] = None,
  ) -> Path:
    """
        Download a tile image from WMTS service.

        Args:
            url (str): Tile URL from get_tile_url.
            save_path (Path, optional): Where to save image. If None, saves in cwd.

        Returns:
            Path: Path to the downloaded image file.
        """
    response = requests.get(url, timeout=self.timeout)
    response.raise_for_status()

    if save_path is None:
      save_path = Path(url.split("/")[-1])

    with open(save_path, "wb") as f:
      f.write(response.content)

    return save_path
