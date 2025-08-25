
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime

# ISS NORAD catalog ID
ISS_ID = 25544

def satellites() -> List[Dict[str, Any]]:
    """
    This endpoint returns a list of satellites that this API has information about, 
    including a common name and NORAD catalog id. Currently, there is only one, 
    the International Space Station. But in the future, we plan to provide more.
    """
    base_url = "https://api.wheretheiss.at/v1/satellites"
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching satellites: {e}")
        return []

def get_iss_position(units: Optional[str] = "kilometers", 
                     timestamps: Optional[bool] = False) -> Optional[Dict[str, Any]]:
    """
    Returns current position, velocity, and other related information about the ISS.
    
    Args:
        units: "kilometers" or "miles" 
        timestamps: Whether to include timestamp information
    
    Returns:
        Dictionary with ISS position data or None if error
    """
    base_url = f"https://api.wheretheiss.at/v1/satellites/{ISS_ID}"
    params = {}
    
    if units:
        params['units'] = units
    if timestamps:
        params['timestamps'] = str(timestamps).lower()
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching ISS position: {e}")
        return None

def get_iss_positions(timestamps: List[int], 
                      units: Optional[str] = "kilometers") -> Optional[List[Dict[str, Any]]]:
    """
    Returns a list of ISS positions for specific timestamps (up to 10).
    
    Args:
        timestamps: List of Unix timestamps (up to 10)
        units: "kilometers" or "miles"
    
    Returns:
        List of position data or None if error
    """
    if len(timestamps) > 10:
        print("Warning: Maximum 10 timestamps allowed, using first 10")
        timestamps = timestamps[:10]
    
    base_url = f"https://api.wheretheiss.at/v1/satellites/{ISS_ID}/positions"
    params = {
        'timestamps': ','.join(map(str, timestamps))
    }
    
    if units:
        params['units'] = units
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching ISS positions: {e}")
        return None

def get_iss_tle() -> Optional[Dict[str, Any]]:
    """
    Returns the TLE (Two-Line Element) data for the ISS.
    TLE data is used to calculate satellite orbits.
    
    Returns:
        Dictionary with TLE data or None if error
    """
    base_url = f"https://api.wheretheiss.at/v1/satellites/{ISS_ID}/tles"
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching ISS TLE: {e}")
        return None

def get_coordinates_info(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Returns position, current time offset, country code, and timezone id 
    for a given set of coordinates.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        Dictionary with coordinate information or None if error
    """
    base_url = f"https://api.wheretheiss.at/v1/coordinates/{latitude},{longitude}"
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching coordinate info: {e}")
        return None

def is_iss_overhead(latitude: float, longitude: float, 
                    altitude_threshold: float = 500) -> bool:
    """
    Check if the ISS is currently overhead at given coordinates.
    
    Args:
        latitude: Your latitude
        longitude: Your longitude
        altitude_threshold: Minimum altitude in km to consider "overhead"
    
    Returns:
        True if ISS is overhead, False otherwise
    """
    position = get_iss_position()
    if not position:
        return False
    
    # Simple distance calculation (this is approximate)
    lat_diff = abs(position['latitude'] - latitude)
    lon_diff = abs(position['longitude'] - longitude)
    
    # ISS is considered overhead if within ~5 degrees and above altitude threshold
    return (lat_diff <= 5 and lon_diff <= 5 and 
            position['altitude'] >= altitude_threshold)

def get_iss_pass_times(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Get upcoming ISS pass times for a specific location.
    Note: This is a placeholder - the actual API doesn't provide this endpoint.
    You would need to use a service like N2YO or calculate it from TLE data.
    
    Args:
        latitude: Your latitude
        longitude: Your longitude
    
    Returns:
        Pass time information or None
    """
    print("Pass time prediction requires additional services or TLE calculations")
    return None

# Legacy function names for backward compatibility
def satellite(id=ISS_ID, units: Optional[str] = "kilometers", 
              timestamps: Optional[bool] = False):
    """Legacy function - use get_iss_position() instead"""
    if id != ISS_ID:
        print(f"Warning: Only ISS (ID {ISS_ID}) is supported")
    return get_iss_position(units, timestamps)

def coordiantes(id=ISS_ID, units: Optional[str] = "kilometers", 
                timestamps: Optional[bool] = False):
    """Legacy function with typo - use get_iss_positions() instead"""
    if id != ISS_ID:
        print(f"Warning: Only ISS (ID {ISS_ID}) is supported")
    # This function had incorrect implementation, keeping for compatibility
    return get_iss_position(units, timestamps)

def tle(id=ISS_ID):
    """Legacy function - use get_iss_tle() instead"""
    if id != ISS_ID:
        print(f"Warning: Only ISS (ID {ISS_ID}) is supported")
    return get_iss_tle()

def coordinates2():
    """Legacy function - use get_coordinates_info() instead"""
    print("This function requires latitude and longitude parameters")
    return None
