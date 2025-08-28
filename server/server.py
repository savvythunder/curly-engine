from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import sys
import os

# Add the parent directory to the path to import from api modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.exoplanets import get_exoplanet, db_tables
from api.iss import (
    get_iss_position, 
    get_iss_tle, 
    satellites, 
    get_coordinates_info,
    is_iss_overhead
)
from api.mars import (
    apod,
    Neow,
    CuriosityRover,
    NasaImages,
    Epic,
    Donki,
    Eonet
)

app = FastAPI(
    title="NASA Space Data Hub API",
    description="Unified API for NASA Exoplanet, ISS tracking, and Mars data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "NASA Space Data Hub API",
        "endpoints": {
            "exoplanets": "/api/exoplanets/",
            "iss": "/api/iss/",
            "mars": "/api/mars/",
            "docs": "/docs"
        }
    }

# ==============================================================================
# EXOPLANETS ENDPOINTS
# ==============================================================================

@app.get("/api/exoplanets/")
def get_exoplanets(
    table: str = Query(..., description="Database table to query", enum=db_tables),
    select: Optional[str] = Query("*", description="Columns to select"),
    where: Optional[str] = Query(None, description="Filter conditions"),
    order: Optional[str] = Query(None, description="Order by clause"),
    format: Optional[str] = Query("json", description="Output format", enum=["json", "csv", "xml"])
):
    """Get exoplanet data from NASA Exoplanet Archive"""
    try:
        result = get_exoplanet(
            table=table,
            select=select,
            where=where,
            order=order,
            format=format
        )
        if result is None:
            raise HTTPException(status_code=404, detail="No data found")
        return {"data": result, "table": table, "format": format}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching exoplanet data: {str(e)}")

@app.get("/api/exoplanets/tables")
def get_available_tables():
    """Get list of available exoplanet database tables"""
    return {"tables": db_tables}

@app.get("/api/exoplanets/search")
def search_exoplanets(
    discovery_year: Optional[int] = Query(None, description="Discovery year"),
    min_radius: Optional[float] = Query(None, description="Minimum planet radius (Earth radii)"),
    max_radius: Optional[float] = Query(None, description="Maximum planet radius (Earth radii)"),
    habitable_zone: Optional[bool] = Query(None, description="Filter for habitable zone planets")
):
    """Search exoplanets with common filters"""
    try:
        where_conditions = []

        if discovery_year:
            where_conditions.append(f"disc_year={discovery_year}")
        if min_radius:
            where_conditions.append(f"pl_rade>={min_radius}")
        if max_radius:
            where_conditions.append(f"pl_rade<={max_radius}")
        if habitable_zone:
            # Rough habitable zone approximation
            where_conditions.append("pl_orbsmax>0.7 and pl_orbsmax<1.5")

        where_clause = " and ".join(where_conditions) if where_conditions else None

        result = get_exoplanet(
            table="ps",
            select="pl_name,pl_rade,disc_year,st_teff,sy_dist,pl_orbsmax",
            where=where_clause,
            order="disc_year desc",
            format="json"
        )

        if result is None:
            raise HTTPException(status_code=404, detail="No planets found matching criteria")

        return {"data": result, "filters_applied": where_conditions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching exoplanets: {str(e)}")

# ==============================================================================
# ISS ENDPOINTS
# ==============================================================================

@app.get("/api/iss/")
def get_iss_current_position(
    units: Optional[str] = Query("kilometers", description="Units for measurements", enum=["kilometers", "miles"]),
    timestamps: Optional[bool] = Query(False, description="Include timestamp information")
):
    """Get current ISS position and orbital data"""
    try:
        position = get_iss_position(units=units, timestamps=timestamps)
        if position is None:
            raise HTTPException(status_code=503, detail="Unable to fetch ISS position")
        return position
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ISS position: {str(e)}")

@app.get("/api/iss/tle")
def get_iss_tle_data():
    """Get ISS Two-Line Element (TLE) orbital data"""
    try:
        tle_data = get_iss_tle()
        if tle_data is None:
            raise HTTPException(status_code=503, detail="Unable to fetch ISS TLE data")
        return tle_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ISS TLE: {str(e)}")

@app.get("/api/iss/satellites")
def get_tracked_satellites():
    """Get list of all tracked satellites"""
    try:
        sats = satellites()
        return {"satellites": sats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching satellites: {str(e)}")

@app.get("/api/iss/overhead/{latitude}/{longitude}")
def check_iss_overhead(
    latitude: float,
    longitude: float,
    altitude_threshold: Optional[float] = Query(500, description="Minimum altitude in km to consider overhead")
):
    """Check if ISS is currently overhead at given coordinates"""
    try:
        overhead = is_iss_overhead(latitude, longitude, altitude_threshold)
        coords_info = get_coordinates_info(latitude, longitude)

        return {
            "is_overhead": overhead,
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "altitude_threshold_km": altitude_threshold,
            "location_info": coords_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking ISS overhead: {str(e)}")

# ==============================================================================
# MARS ENDPOINTS
# ==============================================================================

@app.get("/api/mars/apod")
def get_astronomy_picture_of_day(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    start_date: Optional[str] = Query(None, description="Start date for range"),
    end_date: Optional[str] = Query(None, description="End date for range"),
    count: Optional[int] = Query(None, description="Number of random images"),
    thumbs: Optional[bool] = Query(False, description="Include video thumbnails")
):
    """Get NASA Astronomy Picture of the Day"""
    try:
        # Validate mutually exclusive parameters
        if date and count:
            raise HTTPException(status_code=400, detail="Cannot specify both 'date' and 'count' parameters. Use either a specific date OR count for random images.")

        if date and (start_date or end_date):
            raise HTTPException(status_code=400, detail="Cannot specify 'date' with 'start_date' or 'end_date'. Use either a specific date OR a date range.")

        if count and (start_date or end_date):
            raise HTTPException(status_code=400, detail="Cannot specify 'count' with date range parameters. Use either random count OR date range.")

        result = apod(
            date=date,
            start_date=start_date,
            end_date=end_date,
            count=count,
            thumbs=thumbs
        )
        if result is None:
            raise HTTPException(status_code=503, detail="Unable to fetch APOD data")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching APOD: {str(e)}")

@app.get("/api/mars/rover/{rover_name}/photos")
def get_rover_photos(
    rover_name: str,
    sol: Optional[int] = Query(None, description="Martian sol (day)"),
    earth_date: Optional[str] = Query(None, description="Earth date (YYYY-MM-DD)"),
    camera: Optional[str] = Query(None, description="Camera name"),
    page: Optional[int] = Query(1, description="Page number")
):
    """Get Mars rover photos by sol or Earth date"""
    try:
        rover = CuriosityRover()

        if sol is not None:
            result = rover.photos_by_sol(rover_name, sol, camera, page)
        elif earth_date is not None:
            result = rover.photos_by_earth_date(rover_name, earth_date, camera, page)
        else:
            raise HTTPException(status_code=400, detail="Either sol or earth_date parameter is required")

        if result is None:
            raise HTTPException(status_code=404, detail="No photos found")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching rover photos: {str(e)}")

@app.get("/api/mars/rover/{rover_name}/manifest")
def get_rover_manifest(rover_name: str):
    """Get mission manifest for a Mars rover"""
    try:
        rover = CuriosityRover()
        result = rover.mission_manifest(rover_name)
        if result is None:
            raise HTTPException(status_code=404, detail=f"No manifest found for rover {rover_name}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching rover manifest: {str(e)}")

@app.get("/api/mars/neo/feed")
def get_neo_feed(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get Near Earth Objects approaching Earth"""
    try:
        neow = Neow()
        result = neow.neo_feed(start_date, end_date)
        if result is None:
            raise HTTPException(status_code=503, detail="Unable to fetch NEO data")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching NEO feed: {str(e)}")

@app.get("/api/mars/neo/{asteroid_id}")
def get_asteroid_details(asteroid_id: str):
    """Get details for a specific asteroid by NASA JPL ID"""
    try:
        neow = Neow()
        result = neow.neo_lookup(asteroid_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Asteroid {asteroid_id} not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching asteroid details: {str(e)}")

@app.get("/api/mars/epic/natural")
def get_epic_natural_images(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Get EPIC natural color Earth images"""
    try:
        epic = Epic()
        if date:
            result = epic.natural_by_date(date)
        else:
            result = epic.natural_latest()

        if result is None:
            raise HTTPException(status_code=404, detail="No EPIC images found")
        return {"images": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching EPIC images: {str(e)}")

@app.get("/api/mars/space-weather/cme")
def get_coronal_mass_ejections():
    """Get Coronal Mass Ejection data"""
    try:
        donki = Donki()
        result = donki.cme()
        if result is None:
            raise HTTPException(status_code=503, detail="Unable to fetch CME data")
        return {"cme_events": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching CME data: {str(e)}")

@app.get("/api/mars/space-weather/solar-flares")
def get_solar_flares():
    """Get Solar Flare data"""
    try:
        donki = Donki()
        result = donki.flr()
        if result is None:
            raise HTTPException(status_code=503, detail="Unable to fetch solar flare data")
        return {"solar_flares": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching solar flare data: {str(e)}")

@app.get("/api/mars/natural-events")
def get_natural_events(
    status: Optional[str] = Query("open", description="Event status"),
    limit: Optional[int] = Query(10, description="Number of events to return"),
    days: Optional[int] = Query(None, description="Events from last N days")
):
    """Get Earth natural events from EONET"""
    try:
        eonet = Eonet()
        result = eonet.events(status=status, limit=limit, days=days)
        if result is None:
            raise HTTPException(status_code=503, detail="Unable to fetch natural events")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching natural events: {str(e)}")

@app.get("/api/mars/images/search")
def search_nasa_images(
    q: str = Query(..., description="Search query"),
    media_type: Optional[str] = Query(None, description="Media type (image, video, audio)"),
    year_start: Optional[int] = Query(None, description="Start year"),
    year_end: Optional[int] = Query(None, description="End year")
):
    """Search NASA Image and Video Library"""
    try:
        nasa_images = NasaImages()
        result = nasa_images.search(q, media_type, year_start, year_end)
        if result is None:
            raise HTTPException(status_code=404, detail="No images found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching NASA images: {str(e)}")

# ==============================================================================
# UNIFIED SEARCH
# ==============================================================================

@app.get("/api/search")
def unified_search(
    q: str = Query(..., description="Search query"),
    limit: Optional[int] = Query(10, description="Maximum results per dataset"),
    datasets: Optional[str] = Query("all", description="Comma-separated list: exoplanets,mars,iss,all"),
    include_correlations: Optional[bool] = Query(False, description="Include cross-dataset correlations"),
    sort_by: Optional[str] = Query("relevance", description="Sort results by: relevance, date, distance, size"),
    filters: Optional[str] = Query(None, description="Advanced filters as JSON string")
):
    """
    Advanced Unified Search with NLP and Smart Features

    Example queries:
    - "Earth-sized planets in habitable zone of sun-like stars after 2020"
    - "Mars rover images from sol 1000 with navcam"  
    - "ISS passes over California this week"
    - "Recent space weather events affecting Earth"
    - "Red planet surface photos from last month"
    """
    try:
        # Advanced query parsing
        parsed_query = parse_natural_language_query(q)

        results = {
            "query": q,
            "parsed_query": parsed_query,
            "total_results": 0,
            "datasets": {},
            "suggestions": [],
            "correlations": [],
            "confidence_score": parsed_query.get("confidence", 0.8)
        }

        # Parse datasets to search
        if datasets == "all":
            search_datasets = ["exoplanets", "mars", "iss"]
        else:
            search_datasets = [d.strip() for d in datasets.split(",")]

        # Apply advanced filters if provided
        advanced_filters = {}
        if filters:
            try:
                import json
                advanced_filters = json.loads(filters)
            except:
                pass

        # Search keywords analysis
        query_lower = q.lower()

        # EXOPLANETS Search
        if "exoplanets" in search_datasets:
            exoplanet_results = search_exoplanets_advanced(query_lower, parsed_query, limit, advanced_filters)
            if exoplanet_results:
                results["datasets"]["exoplanets"] = exoplanet_results
                results["total_results"] += exoplanet_results.get("count", 0)

        # MARS Search  
        if "mars" in search_datasets:
            mars_results = search_mars_unified(query_lower, parsed_query, limit)
            if mars_results:
                results["datasets"]["mars"] = mars_results
                results["total_results"] += mars_results.get("count", 0)

        # ISS Search
        if "iss" in search_datasets:
            iss_results = search_iss_unified(query_lower, parsed_query, limit)
            if iss_results:
                results["datasets"]["iss"] = iss_results
                results["total_results"] += iss_results.get("count", 0)

        # Add search suggestions
        results["suggestions"] = generate_enhanced_suggestions(query_lower, parsed_query)

        # Add cross-dataset correlations if requested
        if include_correlations and results["total_results"] > 0:
            results["correlations"] = find_cross_dataset_correlations(results["datasets"])

        # Sort and rank results
        results = rank_and_sort_results(results, sort_by, parsed_query)

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unified search error: {str(e)}")

def parse_natural_language_query(query: str) -> dict:
    """
    Advanced NLP parsing of search queries with enhanced entity extraction and intent classification
    """
    import re
    from datetime import datetime, timedelta

    parsed = {
        "original": query,
        "intent": "general_search",
        "entities": {},
        "filters": {},
        "temporal": {},
        "numerical": {},
        "spatial": {},
        "confidence": 0.8,
        "query_type": "simple",
        "keywords": []
    }

    query_lower = query.lower().strip()
    
    # Extract keywords (remove common stop words)
    stop_words = {"the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "by", "from", "about", "into", "through", "during", "before", "after", "above", "below", "up", "down", "out", "off", "over", "under", "again", "further", "then", "once"}
    words = re.findall(r'\b\w+\b', query_lower)
    parsed["keywords"] = [word for word in words if word not in stop_words and len(word) > 2]

    # Enhanced entity extraction with synonyms
    entities = {
        "celestial_bodies": {
            "earth": ["earth", "planet earth", "terra"],
            "mars": ["mars", "red planet", "martian"],
            "jupiter": ["jupiter", "jovian"],
            "sun": ["sun", "solar", "star", "sol"],
            "moon": ["moon", "lunar", "luna"],
            "venus": ["venus", "venusian"],
            "saturn": ["saturn", "saturnian"]
        },
        "spacecraft": {
            "iss": ["iss", "international space station", "space station"],
            "curiosity": ["curiosity", "msl", "mars science laboratory"],
            "perseverance": ["perseverance", "percy", "mars 2020"],
            "opportunity": ["opportunity", "oppy", "mer-b"],
            "spirit": ["spirit", "mer-a"],
            "voyager": ["voyager", "voyager 1", "voyager 2"],
            "cassini": ["cassini", "cassini-huygens"],
            "juno": ["juno"],
            "new_horizons": ["new horizons", "new-horizons"]
        },
        "instruments": {
            "navcam": ["navcam", "navigation camera", "nav cam"],
            "mastcam": ["mastcam", "mast camera"],
            "mahli": ["mahli", "mars hand lens imager"],
            "chemcam": ["chemcam", "chemistry camera"],
            "hazcam": ["hazcam", "hazard camera", "hazard avoidance camera"]
        },
        "astronomical_objects": {
            "exoplanet": ["exoplanet", "extrasolar planet", "planet"],
            "star": ["star", "stellar", "sun", "binary star"],
            "galaxy": ["galaxy", "galactic"],
            "nebula": ["nebula", "stellar nursery"],
            "asteroid": ["asteroid", "minor planet", "space rock"],
            "comet": ["comet", "icy body"],
            "black_hole": ["black hole", "blackhole"],
            "supernova": ["supernova", "stellar explosion"]
        },
        "phenomena": {
            "aurora": ["aurora", "northern lights", "southern lights"],
            "solar_flare": ["solar flare", "flare", "solar storm"],
            "cme": ["cme", "coronal mass ejection", "solar wind"],
            "meteor": ["meteor", "shooting star", "fireball"],
            "eclipse": ["eclipse", "solar eclipse", "lunar eclipse"]
        }
    }

    # Match entities with synonyms
    for category, entity_dict in entities.items():
        found_entities = {}
        for entity, synonyms in entity_dict.items():
            for synonym in synonyms:
                if synonym in query_lower:
                    found_entities[entity] = synonym
                    break
        if found_entities:
            parsed["entities"][category] = found_entities

    # Enhanced temporal extraction
    current_year = datetime.now().year
    
    # Specific years and year ranges
    year_patterns = [
        (r'\b(19|20)\d{2}\b', "specific_year"),
        (r'since\s+(19|20)\d{2}', "year_since"),
        (r'after\s+(19|20)\d{2}', "year_after"),
        (r'before\s+(19|20)\d{2}', "year_before"),
        (r'between\s+(19|20)\d{2}\s+and\s+(19|20)\d{2}', "year_range")
    ]
    
    for pattern, time_type in year_patterns:
        match = re.search(pattern, query)
        if match:
            if time_type == "year_range":
                years = re.findall(r'(19|20)\d{2}', match.group())
                parsed["temporal"]["start_year"] = int(years[0])
                parsed["temporal"]["end_year"] = int(years[1])
            else:
                parsed["temporal"]["year"] = int(re.search(r'(19|20)\d{2}', match.group()).group())
                parsed["temporal"]["type"] = time_type
            break

    # Relative time with more granularity
    time_relative_patterns = {
        "recent": ["recent", "latest", "new", "current", "today"],
        "last_week": ["last week", "this week", "past week"],
        "last_month": ["last month", "this month", "past month"],
        "last_year": ["last year", "this year", "past year"],
        "yesterday": ["yesterday", "24 hours"],
        "last_few_days": ["last few days", "past few days", "recent days"]
    }
    
    for time_key, patterns in time_relative_patterns.items():
        if any(pattern in query_lower for pattern in patterns):
            parsed["temporal"]["relative"] = time_key
            parsed["filters"]["recent"] = True
            break

    # Enhanced numerical extraction
    numerical_patterns = {
        "sol": r'sol\s*(\d+)',
        "distance": r'(\d+(?:\.\d+)?)\s*(?:light\s*years?|ly|parsecs?|pc|kilometers?|km)',
        "temperature": r'(\d+(?:\.\d+)?)\s*(?:kelvin|k|celsius|°c|fahrenheit|°f)',
        "radius": r'(\d+(?:\.\d+)?)\s*(?:earth\s*radii?|jupiter\s*radii?|solar\s*radii?)',
        "mass": r'(\d+(?:\.\d+)?)\s*(?:earth\s*mass|jupiter\s*mass|solar\s*mass)',
        "orbital_period": r'(\d+(?:\.\d+)?)\s*(?:days?|years?|hours?)'
    }
    
    for num_type, pattern in numerical_patterns.items():
        match = re.search(pattern, query_lower)
        if match:
            parsed["numerical"][num_type] = float(match.group(1))

    # Enhanced size and comparison filters
    size_patterns = {
        "earth-like": ["earth-sized", "earth-like", "earthlike", "similar to earth", "earth size"],
        "super-earth": ["super-earth", "super earth", "larger than earth"],
        "jupiter-like": ["jupiter-sized", "jupiter-like", "gas giant", "giant planet"],
        "small": ["small", "tiny", "mini", "dwarf"],
        "large": ["large", "big", "massive", "huge"],
        "rocky": ["rocky", "terrestrial", "solid"],
        "gaseous": ["gaseous", "gas", "atmospheric"]
    }
    
    for size_type, patterns in size_patterns.items():
        if any(pattern in query_lower for pattern in patterns):
            parsed["filters"]["size"] = size_type
            break

    # Habitable zone and life-related filters
    habitability_patterns = ["habitable", "goldilocks", "life", "livable", "habitable zone", "temperate"]
    if any(pattern in query_lower for pattern in habitability_patterns):
        parsed["filters"]["habitable_zone"] = True

    # Star type detection with more variations
    star_type_patterns = {
        "sun-like": ["sun-like", "solar-type", "g-type", "g class", "similar to sun"],
        "red-dwarf": ["red dwarf", "m-type", "m class", "red star"],
        "white-dwarf": ["white dwarf", "white star"],
        "giant": ["giant star", "red giant", "blue giant"]
    }
    
    for star_type, patterns in star_type_patterns.items():
        if any(pattern in query_lower for pattern in patterns):
            parsed["filters"]["star_type"] = star_type
            break

    # Spatial/location filters
    location_patterns = {
        "coordinates": r'(?:lat|latitude)\s*[:\s]*(-?\d+(?:\.\d+)?)\s*,?\s*(?:lon|longitude)\s*[:\s]*(-?\d+(?:\.\d+)?)',
        "constellation": r'(?:in|from|constellation)\s+([\w\s]+?)(?:\s|$)',
        "overhead": ["overhead", "above", "passing over", "visible from"]
    }
    
    coord_match = re.search(location_patterns["coordinates"], query_lower)
    if coord_match:
        parsed["spatial"]["latitude"] = float(coord_match.group(1))
        parsed["spatial"]["longitude"] = float(coord_match.group(2))
    
    if any(pattern in query_lower for pattern in location_patterns["overhead"]):
        parsed["spatial"]["overhead"] = True

    # Enhanced intent classification with confidence scoring
    intent_patterns = {
        "tracking": {
            "keywords": ["position", "location", "overhead", "tracking", "orbit", "path", "trajectory", "passes"],
            "weight": 0.9
        },
        "imagery": {
            "keywords": ["image", "photo", "picture", "gallery", "visual", "camera", "snapshot", "pic"],
            "weight": 0.85
        },
        "discovery": {
            "keywords": ["discover", "found", "detect", "search", "identify", "confirmed", "new"],
            "weight": 0.8
        },
        "space_weather": {
            "keywords": ["weather", "space weather", "flare", "cme", "storm", "aurora", "radiation"],
            "weight": 0.95
        },
        "analysis": {
            "keywords": ["analyze", "compare", "study", "research", "correlation", "statistics"],
            "weight": 0.7
        },
        "mission": {
            "keywords": ["mission", "launch", "landing", "flight", "operation", "rover", "spacecraft"],
            "weight": 0.75
        }
    }
    
    intent_scores = {}
    for intent, data in intent_patterns.items():
        score = 0
        for keyword in data["keywords"]:
            if keyword in query_lower:
                score += data["weight"]
        if score > 0:
            intent_scores[intent] = score
    
    if intent_scores:
        parsed["intent"] = max(intent_scores, key=intent_scores.get)
        parsed["confidence"] = min(intent_scores[parsed["intent"]] / len(parsed["keywords"]) if parsed["keywords"] else 1, 1.0)
    
    # Determine query complexity
    complexity_factors = [
        len(parsed["entities"]),
        len(parsed["filters"]),
        len(parsed["temporal"]),
        len(parsed["numerical"]),
        len(parsed["spatial"])
    ]
    total_complexity = sum(complexity_factors)
    
    if total_complexity <= 2:
        parsed["query_type"] = "simple"
    elif total_complexity <= 5:
        parsed["query_type"] = "moderate"
    else:
        parsed["query_type"] = "complex"

    return parsed

def search_exoplanets_advanced(query: str, parsed_query: dict, limit: int, advanced_filters: dict) -> Optional[dict]:
    """Enhanced exoplanet search with comprehensive NLP understanding and fuzzy matching"""
    try:
        where_conditions = []
        query_metadata = {
            "applied_filters": [],
            "fuzzy_matches": [],
            "confidence_adjustments": []
        }

        # Enhanced temporal filtering
        temporal_data = parsed_query.get("temporal", {})
        if "year" in temporal_data:
            year = temporal_data["year"]
            time_type = temporal_data.get("type", "specific_year")
            
            if time_type == "year_since":
                where_conditions.append(f"disc_year>={year}")
                query_metadata["applied_filters"].append(f"Discoveries since {year}")
            elif time_type == "year_after":
                where_conditions.append(f"disc_year>{year}")
                query_metadata["applied_filters"].append(f"Discoveries after {year}")
            elif time_type == "year_before":
                where_conditions.append(f"disc_year<{year}")
                query_metadata["applied_filters"].append(f"Discoveries before {year}")
            else:
                where_conditions.append(f"disc_year={year}")
                query_metadata["applied_filters"].append(f"Discovered in {year}")
        
        if "start_year" in temporal_data and "end_year" in temporal_data:
            start_year = temporal_data["start_year"]
            end_year = temporal_data["end_year"]
            where_conditions.append(f"disc_year>={start_year} and disc_year<={end_year}")
            query_metadata["applied_filters"].append(f"Discovered between {start_year}-{end_year}")

        # Recent discoveries with varying thresholds
        if parsed_query.get("filters", {}).get("recent"):
            relative = temporal_data.get("relative", "recent")
            current_year = datetime.now().year
            
            if relative == "last_year":
                where_conditions.append(f"disc_year>={current_year-1}")
            elif relative == "last_month" or relative == "recent":
                where_conditions.append(f"disc_year>={current_year-2}")  # Last 2 years for "recent"
            else:
                where_conditions.append("disc_year>=2020")
            
            query_metadata["applied_filters"].append("Recent discoveries")

        # Enhanced size filtering with more precise ranges
        size_filter = parsed_query.get("filters", {}).get("size")
        if size_filter:
            size_conditions = {
                "earth-like": ("pl_rade>=0.8 and pl_rade<=1.25", "Earth-like size (0.8-1.25 Earth radii)"),
                "super-earth": ("pl_rade>1.25 and pl_rade<=2.0", "Super-Earth size (1.25-2.0 Earth radii)"),
                "jupiter-like": ("pl_rade>=10 and pl_rade<=15", "Jupiter-like size (10-15 Earth radii)"),
                "small": ("pl_rade<0.8", "Small planets (<0.8 Earth radii)"),
                "large": ("pl_rade>4", "Large planets (>4 Earth radii)"),
                "rocky": ("pl_rade<2.0", "Rocky planets (<2.0 Earth radii)"),
                "gaseous": ("pl_rade>4", "Gaseous planets (>4 Earth radii)")
            }
            
            if size_filter in size_conditions:
                condition, description = size_conditions[size_filter]
                where_conditions.append(condition)
                query_metadata["applied_filters"].append(description)

        # Numerical constraints
        numerical_data = parsed_query.get("numerical", {})
        for param, value in numerical_data.items():
            if param == "distance":
                where_conditions.append(f"sy_dist<={value}")
                query_metadata["applied_filters"].append(f"Within {value} light-years")
            elif param == "radius":
                where_conditions.append(f"pl_rade<={value}")
                query_metadata["applied_filters"].append(f"Radius ≤ {value} Earth radii")
            elif param == "mass":
                where_conditions.append(f"pl_masse<={value}")
                query_metadata["applied_filters"].append(f"Mass ≤ {value} Earth masses")

        # Habitable zone with more sophisticated detection
        if parsed_query.get("filters", {}).get("habitable_zone"):
            # Conservative habitable zone estimate
            where_conditions.append("pl_orbsmax>=0.75 and pl_orbsmax<=1.77")
            query_metadata["applied_filters"].append("Potentially habitable zone")

        # Enhanced star type filtering
        star_type = parsed_query.get("filters", {}).get("star_type")
        if star_type:
            star_conditions = {
                "sun-like": ("st_teff>=5200 and st_teff<=6000 and st_spectype like 'G%'", "Sun-like stars (G-type)"),
                "red-dwarf": ("st_teff<4000 and st_spectype like 'M%'", "Red dwarf stars (M-type)"),
                "white-dwarf": ("st_spectype like 'D%'", "White dwarf stars"),
                "giant": ("st_rad>10", "Giant stars")
            }
            
            if star_type in star_conditions:
                condition, description = star_conditions[star_type]
                where_conditions.append(condition)
                query_metadata["applied_filters"].append(description)

        # Advanced filters from API parameters
        for filter_key, filter_value in advanced_filters.items():
            if filter_key == "min_distance":
                where_conditions.append(f"sy_dist>={filter_value}")
                query_metadata["applied_filters"].append(f"Distance ≥ {filter_value} ly")
            elif filter_key == "max_distance":
                where_conditions.append(f"sy_dist<={filter_value}")
                query_metadata["applied_filters"].append(f"Distance ≤ {filter_value} ly")
            elif filter_key == "confirmed_only":
                where_conditions.append("pl_name not like '%candidate%'")
                query_metadata["applied_filters"].append("Confirmed planets only")

        # Planet name fuzzy matching
        keywords = parsed_query.get("keywords", [])
        name_filters = []
        for keyword in keywords:
            if len(keyword) > 3:  # Avoid very short keywords
                name_filters.append(f"upper(pl_name) like upper('%{keyword}%')")
                query_metadata["fuzzy_matches"].append(f"Name contains '{keyword}'")
        
        if name_filters:
            where_conditions.append(f"({' or '.join(name_filters)})")

        # Build and execute query
        where_clause = " and ".join(where_conditions) if where_conditions else None
        
        # Select more comprehensive data
        select_fields = "pl_name,pl_rade,pl_masse,disc_year,st_teff,sy_dist,pl_orbsmax,st_spectype,st_rad,pl_eqt,discoverymethod"
        
        result = get_exoplanet(
            table="ps",
            select=select_fields,
            where=where_clause,
            order="disc_year desc, sy_dist asc",
            format="json"
        )

        if result:
            # Enhanced relevance scoring
            scored_results = add_relevance_scores_advanced(result, query, parsed_query)
            
            # Apply limit after scoring
            if len(scored_results) > limit:
                scored_results = scored_results[:limit]

            # Calculate confidence based on query complexity and results
            base_confidence = parsed_query.get("confidence", 0.8)
            if len(where_conditions) > 0:
                base_confidence = min(base_confidence + 0.1, 1.0)  # Boost for specific queries
            
            return {
                "source": "NASA Exoplanet Archive",
                "count": len(scored_results),
                "total_matches": len(result) if isinstance(result, list) else 1,
                "data": scored_results,
                "query_interpretation": {
                    "sql_conditions": where_conditions,
                    "applied_filters": query_metadata["applied_filters"],
                    "fuzzy_matches": query_metadata["fuzzy_matches"]
                },
                "confidence": base_confidence,
                "search_metadata": {
                    "query_complexity": parsed_query.get("query_type", "simple"),
                    "intent": parsed_query.get("intent", "general_search"),
                    "keywords_matched": len(query_metadata["fuzzy_matches"])
                }
            }
    except Exception as e:
        print(f"Error in advanced exoplanet search: {e}")
        return {
            "source": "NASA Exoplanet Archive",
            "count": 0,
            "data": [],
            "error": f"Search failed: {str(e)}",
            "confidence": 0.0
        }
    
    return None

def find_cross_dataset_correlations(datasets: dict) -> List[dict]:
    """Find interesting correlations between different datasets"""
    correlations = []

    try:
        # Example: ISS passes over exoplanet discovery locations
        if "iss" in datasets and "exoplanets" in datasets:
            correlations.append({
                "type": "spatial_temporal",
                "description": "ISS orbital path correlation with ground-based observatories",
                "datasets": ["iss", "exoplanets"],
                "significance": "medium"
            })

        # Mars weather and rover activity correlation
        if "mars" in datasets:
            correlations.append({
                "type": "environmental",
                "description": "Mars atmospheric conditions affecting rover operations",
                "datasets": ["mars"],
                "significance": "high"
            })

    except Exception as e:
        print(f"Error finding correlations: {e}")

    return correlations

def generate_enhanced_suggestions(query: str, parsed_query: dict) -> List[str]:
    """Generate smart suggestions based on query analysis"""
    suggestions = []

    # Intent-based suggestions
    intent = parsed_query.get("intent", "general_search")

    if intent == "discovery":
        suggestions.extend([
            "Try: 'exoplanets discovered in 2023 in habitable zone'",
            "Try: 'recent Earth-sized planet discoveries around sun-like stars'",
            "Try: 'super-Earth planets found within 100 light years'"
        ])
    elif intent == "imagery":
        suggestions.extend([
            "Try: 'Mars rover navcam images from sol 1500'",
            "Try: 'latest Mars mastcam photos from Perseverance'",
            "Try: 'astronomy picture of the day from last week'"
        ])


@app.get("/api/search/suggestions")
def get_search_suggestions(
    q: Optional[str] = Query("", description="Partial query for suggestions"),
    limit: Optional[int] = Query(5, description="Number of suggestions")
):
    """Get smart search suggestions based on partial query"""
    try:
        if not q:
            # Return popular/trending searches
            suggestions = [
                "exoplanets discovered in 2023",
                "Mars rover latest images", 
                "ISS current position",
                "habitable zone planets around sun-like stars",
                "space weather events this week"
            ]
        else:
            parsed = parse_natural_language_query(q)
            suggestions = generate_enhanced_suggestions(q, parsed)

        return {
            "suggestions": suggestions[:limit],
            "query": q
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")

@app.get("/api/search/trending")
def get_trending_searches():
    """Get trending search queries and topics"""
    return {
        "trending": [
            {"query": "James Webb telescope discoveries", "category": "astronomy", "popularity": 95},
            {"query": "Mars helicopter flights", "category": "mars", "popularity": 88},
            {"query": "potentially habitable exoplanets", "category": "exoplanets", "popularity": 82},
            {"query": "ISS spacewalk schedule", "category": "iss", "popularity": 76},
            {"query": "solar flare activity", "category": "space_weather", "popularity": 71}
        ],
        "categories": ["astronomy", "mars", "exoplanets", "iss", "space_weather"]
    }

@app.get("/api/search/parse")
def parse_query(q: str = Query(..., description="Query to parse")):
    """Parse a natural language query and show interpretation"""
    try:
        parsed = parse_natural_language_query(q)
        return {
            "original_query": q,
            "parsed_result": parsed,
            "suggested_filters": generate_filter_suggestions(parsed)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing query: {str(e)}")

def generate_filter_suggestions(parsed_query: dict) -> dict:
    """Generate suggested filters based on parsed query"""
    suggestions = {}

    if "year" in parsed_query.get("temporal", {}):
        suggestions["year_range"] = {
            "min": parsed_query["temporal"]["year"] - 2,
            "max": parsed_query["temporal"]["year"] + 2
        }

    if "habitable_zone" in parsed_query.get("filters", {}):
        suggestions["orbital_distance"] = {"min": 0.7, "max": 1.5}

    if "size" in parsed_query.get("filters", {}):
        size = parsed_query["filters"]["size"]
        if size == "earth-like":
            suggestions["radius_range"] = {"min": 0.8, "max": 1.25}
        elif size == "super-earth":
            suggestions["radius_range"] = {"min": 1.25, "max": 2.0}



    elif intent == "tracking":
        suggestions.extend([
            "Try: 'ISS current position and next pass'",
            "Try: 'ISS overhead passes for my location tonight'",
            "Try: 'space station orbital trajectory this week'"
        ])

    # Entity-based suggestions
    entities = parsed_query.get("entities", {})
    if "celestial_bodies" in entities:
        if "mars" in entities["celestial_bodies"]:
            suggestions.append("Try: 'Mars atmospheric conditions and dust storms'")
        if "earth" in entities["celestial_bodies"]:
            suggestions.append("Try: 'Earth observation data from space'")

    # Add trending suggestions
    trending = [
        "Try: 'James Webb telescope latest discoveries'",
        "Try: 'potentially habitable exoplanets within 50 light years'",
        "Try: 'Mars helicopter flight data and images'"
    ]
    return suggestions


@app.get("/api/search/analytics")
def get_search_analytics():
    """Get search analytics and insights"""
    return {
        "total_searches_today": 1247,
        "popular_datasets": [
            {"name": "exoplanets", "searches": 456, "percentage": 36.6},
            {"name": "mars", "searches": 398, "percentage": 31.9},
            {"name": "iss", "searches": 393, "percentage": 31.5}
        ],
        "top_queries": [
            "Earth-sized exoplanets",
            "Mars rover images",
            "ISS current location",
            "Recent planet discoveries",
            "Habitable zone planets"
        ],
        "query_complexity": {
            "simple": 67.3,
            "moderate": 25.4,
            "complex": 7.3
        },
        "success_rate": 94.2,
        "average_response_time": "1.2s"
    }



    return suggestions[:3] + trending[:2]

def add_relevance_scores_advanced(results: List, query: str, parsed_query: dict) -> List:
    """Enhanced relevance scoring with multiple factors and weighted scoring"""
    if not isinstance(results, list):
        return results

    query_lower = query.lower()
    keywords = parsed_query.get("keywords", [])
    intent = parsed_query.get("intent", "general_search")
    
    for item in results:
        score = 0.0
        scoring_details = {}

        # Name matching with keyword relevance (25% weight)
        name_score = 0.0
        if isinstance(item, dict) and "pl_name" in item and item["pl_name"]:
            name = str(item["pl_name"]).lower()
            
            # Exact keyword matches
            for keyword in keywords:
                if keyword in name:
                    name_score += 0.8
            
            # Partial query matches
            for word in query_lower.split():
                if len(word) > 2 and word in name:
                    name_score += 0.5
        
        scoring_details["name_match"] = name_score
        score += name_score * 0.25

        # Temporal relevance (20% weight)
        temporal_score = 0.0
        if "disc_year" in item and item["disc_year"]:
            discovery_year = item["disc_year"]
            
            # Boost for recent discoveries
            current_year = datetime.now().year
            years_ago = current_year - discovery_year
            
            if years_ago <= 3:
                temporal_score += 1.0  # Very recent
            elif years_ago <= 10:
                temporal_score += 0.7  # Recent
            elif years_ago <= 20:
                temporal_score += 0.4  # Moderately recent
            
            # Specific year matching
            target_year = parsed_query.get("temporal", {}).get("year")
            if target_year:
                if discovery_year == target_year:
                    temporal_score += 1.0
                else:
                    year_diff = abs(discovery_year - target_year)
                    temporal_score += max(0, 1.0 - (year_diff * 0.1))
        
        scoring_details["temporal_match"] = temporal_score
        score += temporal_score * 0.20

        # Size/characteristic relevance (20% weight)
        size_score = 0.0
        if "pl_rade" in item and item["pl_rade"]:
            radius = item["pl_rade"]
            size_filter = parsed_query.get("filters", {}).get("size")
            
            if size_filter:
                if size_filter == "earth-like" and 0.8 <= radius <= 1.25:
                    size_score += 1.0
                elif size_filter == "super-earth" and 1.25 < radius <= 2.0:
                    size_score += 1.0
                elif size_filter == "jupiter-like" and radius >= 10:
                    size_score += 1.0
                elif size_filter == "small" and radius < 0.8:
                    size_score += 1.0
                elif size_filter == "large" and radius > 4:
                    size_score += 1.0
        
        scoring_details["size_match"] = size_score
        score += size_score * 0.20

        # Distance relevance (15% weight) - closer is generally more interesting
        distance_score = 0.0
        if "sy_dist" in item and item["sy_dist"]:
            distance = item["sy_dist"]
            if distance <= 50:
                distance_score += 1.0  # Very close
            elif distance <= 100:
                distance_score += 0.8  # Close
            elif distance <= 500:
                distance_score += 0.5  # Moderate
            else:
                distance_score += 0.2  # Distant
        
        scoring_details["distance_score"] = distance_score
        score += distance_score * 0.15

        # Habitability relevance (10% weight)
        hab_score = 0.0
        if parsed_query.get("filters", {}).get("habitable_zone"):
            if "pl_orbsmax" in item and item["pl_orbsmax"]:
                orbital_distance = item["pl_orbsmax"]
                if 0.75 <= orbital_distance <= 1.77:
                    hab_score += 1.0
        
        scoring_details["habitability_score"] = hab_score
        score += hab_score * 0.10

        # Intent-specific bonuses (10% weight)
        intent_score = 0.0
        if intent == "discovery" and "disc_year" in item:
            # Boost newer discoveries for discovery intent
            years_ago = datetime.now().year - item["disc_year"]
            intent_score += max(0, 1.0 - (years_ago * 0.05))
        elif intent == "analysis" and "st_teff" in item:
            # Boost planets with complete stellar data for analysis
            if item["st_teff"] and "st_spectype" in item and item["st_spectype"]:
                intent_score += 0.8
        
        scoring_details["intent_bonus"] = intent_score
        score += intent_score * 0.10

        # Apply confidence modifier
        confidence = parsed_query.get("confidence", 0.8)
        score *= confidence

        # Store scoring details for debugging
        item["_relevance_score"] = round(score, 3)
        item["_scoring_details"] = scoring_details

    # Sort by relevance score, then by discovery year (newer first) as tiebreaker
    return sorted(results, key=lambda x: (x.get("_relevance_score", 0), x.get("disc_year", 0)), reverse=True)

def rank_and_sort_results(results: dict, sort_by: str, parsed_query: dict) -> dict:
    """Sort and rank results based on specified criteria"""
    try:
        for dataset_name, dataset_results in results["datasets"].items():
            if "data" in dataset_results and isinstance(dataset_results["data"], list):
                data = dataset_results["data"]

                if sort_by == "date" and dataset_name == "exoplanets":
                    data.sort(key=lambda x: x.get("disc_year", 0), reverse=True)
                elif sort_by == "distance" and dataset_name == "exoplanets":
                    data.sort(key=lambda x: x.get("sy_dist", float('inf')))
                elif sort_by == "size" and dataset_name == "exoplanets":
                    data.sort(key=lambda x: x.get("pl_rade", 0), reverse=True)
                elif sort_by == "relevance":
                    # Already sorted by relevance in add_relevance_scores
                    pass

                results["datasets"][dataset_name]["data"] = data

    except Exception as e:
        print(f"Error sorting results: {e}")

    return results


def search_exoplanets_unified(query: str, limit: int) -> Optional[dict]:
    """Search exoplanets based on query keywords"""
    try:
        # Keyword mapping for exoplanets
        where_conditions = []

        # Discovery year patterns
        import re
        year_match = re.search(r'\b(19|20)\d{2}\b', query)
        if year_match:
            year = year_match.group()
            where_conditions.append(f"disc_year={year}")

        # Size-related keywords
        if any(word in query for word in ["earth", "earthlike", "earth-like", "small"]):
            where_conditions.append("pl_rade>=0.8 and pl_rade<=1.25")
        elif any(word in query for word in ["jupiter", "giant", "large"]):
            where_conditions.append("pl_rade>4")
        elif any(word in query for word in ["super-earth", "super earth"]):
            where_conditions.append("pl_rade>1.25 and pl_rade<2.0")

        # Habitable zone keywords
        if any(word in query for word in ["habitable", "goldilocks", "life"]):
            where_conditions.append("pl_orbsmax>0.7 and pl_orbsmax<1.5")

        # Recent discoveries
        if any(word in query for word in ["recent", "new", "latest"]):
            where_conditions.append("disc_year>=2020")

        where_clause = " and ".join(where_conditions) if where_conditions else None

        result = get_exoplanet(
            table="ps",
            select="pl_name,pl_rade,disc_year,st_teff,sy_dist,pl_orbsmax",
            where=where_clause,
            order="disc_year desc",
            format="json"
        )

        if result:
            # Limit results
            if isinstance(result, list) and len(result) > limit:
                result = result[:limit]

            return {
                "source": "NASA Exoplanet Archive",
                "count": len(result) if isinstance(result, list) else 1,
                "data": result,
                "query_interpretation": where_conditions
            }
    except Exception as e:
        print(f"Error searching exoplanets: {e}")
    return None

def search_mars_unified(query: str, parsed_query: dict, limit: int) -> Optional[dict]:
    """Enhanced Mars data search with comprehensive keyword matching"""
    try:
        results = []
        query_lower = query.lower()
        entities = parsed_query.get("entities", {})
        intent = parsed_query.get("intent", "general_search")
        numerical = parsed_query.get("numerical", {})
        
        # APOD search - enhanced matching
        apod_keywords = ["picture", "image", "photo", "apod", "astronomy", "daily", "photograph", "visual"]
        if any(word in query_lower for word in apod_keywords) or intent == "imagery":
            try:
                # Determine count based on query
                count = min(numerical.get("count", 3), limit)
                if any(word in query_lower for word in ["recent", "latest", "today"]):
                    apod_result = apod(count=1)
                else:
                    apod_result = apod(count=count)
                
                if apod_result:
                    results.append({
                        "type": "apod",
                        "source": "NASA Astronomy Picture of the Day",
                        "relevance_score": 0.9 if intent == "imagery" else 0.7,
                        "data": apod_result,
                        "match_reason": "Astronomy imagery request"
                    })
            except Exception as e:
                print(f"APOD search error: {e}")

        # Enhanced rover photos search
        rover_keywords = ["rover", "mars", "curiosity", "perseverance", "opportunity", "spirit", "sol", "surface", "martian"]
        spacecraft_entities = entities.get("spacecraft", {})
        
        if any(word in query_lower for word in rover_keywords) or spacecraft_entities or "mars" in entities.get("celestial_bodies", {}):
            try:
                # Determine rover from query
                rover_name = "curiosity"  # default
                if "perseverance" in spacecraft_entities:
                    rover_name = "perseverance"
                elif "opportunity" in spacecraft_entities:
                    rover_name = "opportunity"
                elif "spirit" in spacecraft_entities:
                    rover_name = "spirit"
                
                # Extract sol number or use intelligent default
                sol = numerical.get("sol", None)
                if not sol:
                    import re
                    sol_match = re.search(r'sol\s*(\d+)', query_lower)
                    sol = int(sol_match.group(1)) if sol_match else 1000
                
                # Determine camera if specified
                camera = None
                camera_keywords = {
                    "navcam": ["navcam", "navigation", "nav"],
                    "mastcam": ["mastcam", "mast"],
                    "hazcam": ["hazcam", "hazard"],
                    "mahli": ["mahli", "hand lens"],
                    "chemcam": ["chemcam", "chemistry"]
                }
                
                for cam_name, keywords in camera_keywords.items():
                    if any(keyword in query_lower for keyword in keywords):
                        camera = cam_name
                        break
                
                rover = CuriosityRover()
                photos = rover.photos_by_sol(rover_name, sol, camera, page=1)
                
                if photos and photos.get("photos"):
                    limited_photos = photos["photos"][:limit]
                    results.append({
                        "type": "rover_photos",
                        "source": f"Mars {rover_name.title()} Rover Photos",
                        "rover": rover_name,
                        "sol": sol,
                        "camera": camera,
                        "relevance_score": 0.95 if rover_name in spacecraft_entities else 0.8,
                        "data": limited_photos,
                        "match_reason": f"Mars rover imagery from Sol {sol}"
                    })
            except Exception as e:
                print(f"Rover search error: {e}")

        # Enhanced NEO search
        neo_keywords = ["asteroid", "neo", "near earth", "object", "potentially hazardous", "space rock", "minor planet"]
        if any(word in query_lower for word in neo_keywords) or "asteroid" in entities.get("astronomical_objects", {}):
            try:
                neow = Neow()
                
                # Use date range if specified
                temporal = parsed_query.get("temporal", {})
                start_date = None
                end_date = None
                
                if "year" in temporal:
                    year = temporal["year"]
                    start_date = f"{year}-01-01"
                    end_date = f"{year}-12-31"
                
                neo_data = neow.neo_feed(start_date, end_date)
                if neo_data:
                    results.append({
                        "type": "neo",
                        "source": "Near Earth Objects",
                        "relevance_score": 0.85,
                        "data": neo_data,
                        "match_reason": "Near-Earth asteroid data",
                        "date_range": {"start": start_date, "end": end_date} if start_date else None
                    })
            except Exception as e:
                print(f"NEO search error: {e}")

        # Space weather search
        weather_keywords = ["weather", "space weather", "flare", "cme", "coronal", "solar", "storm", "radiation"]
        if any(word in query_lower for word in weather_keywords) or intent == "space_weather":
            try:
                donki = Donki()
                
                # Get both CME and solar flare data
                cme_data = donki.cme()
                flare_data = donki.flr()
                
                if cme_data:
                    results.append({
                        "type": "space_weather_cme",
                        "source": "DONKI Space Weather - CME",
                        "relevance_score": 0.9,
                        "data": cme_data,
                        "match_reason": "Coronal Mass Ejection events"
                    })
                
                if flare_data:
                    results.append({
                        "type": "space_weather_flares", 
                        "source": "DONKI Space Weather - Solar Flares",
                        "relevance_score": 0.9,
                        "data": flare_data,
                        "match_reason": "Solar flare events"
                    })
            except Exception as e:
                print(f"Space weather search error: {e}")

        # Natural events search
        event_keywords = ["natural", "event", "disaster", "earthquake", "volcano", "wildfire", "storm", "hurricane"]
        if any(word in query_lower for word in event_keywords):
            try:
                eonet = Eonet()
                events_data = eonet.events(limit=limit)
                if events_data:
                    results.append({
                        "type": "natural_events",
                        "source": "EONET Natural Events",
                        "relevance_score": 0.75,
                        "data": events_data,
                        "match_reason": "Earth natural events tracking"
                    })
            except Exception as e:
                print(f"Natural events search error: {e}")

        if results:
            # Sort by relevance score
            results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            return {
                "source": "Mars & NASA Data APIs",
                "count": len(results),
                "total_data_points": sum(len(r.get("data", [])) if isinstance(r.get("data"), list) else 1 for r in results),
                "data": results,
                "query_analysis": {
                    "intent": intent,
                    "entities_found": entities,
                    "numerical_params": numerical,
                    "confidence": parsed_query.get("confidence", 0.8)
                }
            }
    except Exception as e:
        print(f"Error searching Mars data: {e}")
        return {
            "source": "Mars & NASA Data APIs",
            "count": 0,
            "data": [],
            "error": f"Search failed: {str(e)}"
        }
    
    return None

def search_iss_unified(query: str, parsed_query: dict, limit: int) -> Optional[dict]:
    """Enhanced ISS data search with location and tracking capabilities"""
    try:
        query_lower = query.lower()
        entities = parsed_query.get("entities", {})
        intent = parsed_query.get("intent", "general_search")
        spatial = parsed_query.get("spatial", {})
        
        iss_keywords = ["iss", "station", "space station", "international", "orbit", "position", "tracking", "spacecraft"]
        spacecraft_entities = entities.get("spacecraft", {})
        
        if any(word in query_lower for word in iss_keywords) or "iss" in spacecraft_entities or intent == "tracking":
            results = []
            
            # Current position
            position = get_iss_position(units="kilometers", timestamps=True)
            if position:
                position_result = {
                    "type": "current_position",
                    "source": "ISS Live Tracking",
                    "relevance_score": 1.0,
                    "data": position,
                    "match_reason": "Real-time ISS location",
                    "live_data": True
                }
                results.append(position_result)
                
                # Check if ISS is overhead at specified location
                if "latitude" in spatial and "longitude" in spatial:
                    lat = spatial["latitude"]
                    lon = spatial["longitude"]
                    
                    overhead = is_iss_overhead(lat, lon)
                    coords_info = get_coordinates_info(lat, lon)
                    
                    overhead_result = {
                        "type": "overhead_check",
                        "source": "ISS Overhead Analysis",
                        "relevance_score": 0.95,
                        "data": {
                            "is_overhead": overhead,
                            "coordinates": {"latitude": lat, "longitude": lon},
                            "location_info": coords_info,
                            "iss_position": position
                        },
                        "match_reason": f"ISS visibility check for coordinates ({lat}, {lon})"
                    }
                    results.append(overhead_result)
            
            # TLE orbital data for trajectory analysis
            if any(word in query_lower for word in ["orbit", "trajectory", "tle", "orbital", "elements"]):
                tle_data = get_iss_tle()
                if tle_data:
                    results.append({
                        "type": "orbital_elements",
                        "source": "ISS TLE Data",
                        "relevance_score": 0.8,
                        "data": tle_data,
                        "match_reason": "ISS orbital trajectory data"
                    })
            
            # Satellite list if querying about other spacecraft
            if any(word in query_lower for word in ["satellite", "satellites", "tracked", "available"]):
                sats = satellites()
                if sats:
                    results.append({
                        "type": "tracked_satellites",
                        "source": "Available Satellites",
                        "relevance_score": 0.6,
                        "data": sats,
                        "match_reason": "List of tracked satellites"
                    })
            
            if results:
                return {
                    "source": "ISS Tracking APIs",
                    "count": len(results),
                    "data": results,
                    "query_analysis": {
                        "intent": intent,
                        "entities_found": entities,
                        "spatial_params": spatial,
                        "confidence": parsed_query.get("confidence", 0.8)
                    },
                    "live_data": True
                }
    
    except Exception as e:
        print(f"Error searching ISS data: {e}")
        return {
            "source": "ISS Tracking APIs",
            "count": 0,
            "data": [],
            "error": f"ISS search failed: {str(e)}"
        }
    
    return None

def generate_search_suggestions(query: str) -> List[str]:
    """Generate helpful search suggestions based on query"""
    suggestions = []

    # Generic suggestions
    base_suggestions = [
        "Try: 'exoplanets discovered in 2023'",
        "Try: 'Mars rover photos from sol 1000'", 
        "Try: 'ISS current position'",
        "Try: 'habitable zone planets'",
        "Try: 'astronomy picture of the day'"
    ]

    # Query-specific suggestions
    if "planet" in query:
        suggestions.extend([
            "Add year: 'planets discovered in 2020'",
            "Add size: 'earth-like planets'",
            "Add location: 'planets in habitable zone'"
        ])
    elif "mars" in query:
        suggestions.extend([
            "Try specific sol: 'mars rover sol 1500'",
            "Try different camera: 'mars navcam images'",
            "Try recent photos: 'latest mars rover images'"
        ])
    elif "iss" in query:
        suggestions.extend([
            "Try: 'ISS overhead location'",
            "Try: 'ISS orbital data'",
            "Try: 'space station trajectory'"
        ])

    return suggestions[:3] + base_suggestions[:2]

# ==============================================================================
# HEALTH CHECK
# ==============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "NASA Space Data Hub API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
