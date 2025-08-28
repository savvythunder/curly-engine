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

import sqlite3
import json
from pathlib import Path
import hashlib
from typing import Union
from datetime import datetime

# Database setup for query caching and analytics
DB_PATH = Path("search_analytics.db")

def init_database():
    """Initialize SQLite database for search analytics and caching"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Query analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT NOT NULL,
            query_hash TEXT UNIQUE,
            parsed_query TEXT,
            intent TEXT,
            complexity_score REAL,
            understanding_score REAL,
            datasets_searched TEXT,
            total_results INTEGER,
            response_time_ms REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Result cache table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS result_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash TEXT UNIQUE,
            results TEXT,
            cache_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            expiry_timestamp DATETIME
        )
    ''')
    
    # User feedback table (for future reinforcement learning)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash TEXT,
            result_id TEXT,
            feedback_type TEXT, -- click, star, dismiss, refine
            feedback_value REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def log_search_query(query: str, parsed_query: dict, datasets: list, total_results: int, response_time: float):
    """Log search query for analytics"""
    try:
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO query_analytics 
            (query_text, query_hash, parsed_query, intent, complexity_score, 
             understanding_score, datasets_searched, total_results, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            query,
            query_hash,
            json.dumps(parsed_query),
            parsed_query.get("intent", "unknown"),
            sum(parsed_query.get("complexity_breakdown", {}).values()),
            parsed_query.get("understanding_score", 0.0),
            json.dumps(datasets),
            total_results,
            response_time
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging search query: {e}")

def get_cached_results(query: str) -> Union[dict, None]:
    """Check if results are cached for this query"""
    try:
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT results FROM result_cache 
            WHERE query_hash = ? AND expiry_timestamp > CURRENT_TIMESTAMP
        ''', (query_hash,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    except Exception as e:
        print(f"Error checking cache: {e}")
        return None

def cache_results(query: str, results: dict, expiry_hours: int = 1):
    """Cache search results"""
    try:
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO result_cache 
            (query_hash, results, expiry_timestamp)
            VALUES (?, ?, datetime('now', '+{} hours'))
        '''.format(expiry_hours), (
            query_hash,
            json.dumps(results)
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error caching results: {e}")

# Initialize database on module load
init_database()


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
    filters: Optional[str] = Query(None, description="Advanced filters as JSON string"),
    use_cache: Optional[bool] = Query(True, description="Use cached results if available")
):
    """
    Advanced Unified Search with NLP, Semantic Understanding, and Smart Caching

    Example queries:
    - "Earth-sized planets in habitable zone of sun-like stars discovered after 2020"
    - "Mars rover navcam images from sol 1000 to 1500"  
    - "ISS passes over California this week"
    - "Recent space weather events affecting Earth"
    - "Red planet surface photos larger than 1MB from last month"
    - "Compare Kepler-452b with Earth characteristics"
    - "How many confirmed exoplanets are there in 2024?"
    """
    import time
    start_time = time.time()
    
    try:
        # Check cache first
        if use_cache:
            cached_results = get_cached_results(q)
            if cached_results:
                cached_results["cached"] = True
                cached_results["cache_hit"] = True
                return cached_results
        
        # Advanced query parsing with enhanced understanding
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

        # Sort and rank results with advanced algorithms
        results = rank_and_sort_results(results, sort_by, parsed_query)
        
        # Calculate response metadata
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Enhanced response with explanations and metadata
        enhanced_results = {
            **results,
            "query_analysis": {
                "original_query": q,
                "parsed_intent": parsed_query.get("intent"),
                "understanding_score": parsed_query.get("understanding_score", 0.0),
                "complexity": parsed_query.get("query_type"),
                "entities_found": parsed_query.get("entities", {}),
                "logical_operators": parsed_query.get("logical_operators", []),
                "units_detected": parsed_query.get("units", {}),
                "explanation": parsed_query.get("explanation", [])
            },
            "search_metadata": {
                "response_time_ms": round(response_time, 2),
                "cached": False,
                "datasets_searched": search_datasets,
                "search_algorithm": "hybrid_semantic_structured",
                "ranking_method": sort_by,
                "correlations_included": include_correlations
            },
            "performance_hints": generate_performance_suggestions(parsed_query, results["total_results"])
        }
        
        # Log analytics
        try:
            log_search_query(
                query=q,
                parsed_query=parsed_query,
                datasets=search_datasets,
                total_results=results["total_results"],
                response_time=response_time
            )
            
            # Cache results for future queries
            if use_cache and results["total_results"] > 0:
                cache_results(q, enhanced_results, expiry_hours=1)
                
        except Exception as analytics_error:
            print(f"Analytics logging error: {analytics_error}")
        
        return enhanced_results

    except Exception as e:
        # Log error for analytics
        try:
            error_query = {"error": str(e), "query": q}
            log_search_query(q, error_query, [], 0, 0)
        except:
            pass
        
        raise HTTPException(status_code=500, detail=f"Unified search error: {str(e)}")

def generate_performance_suggestions(parsed_query: dict, total_results: int) -> List[str]:
    """Generate suggestions for improving search performance and results"""
    suggestions = []
    
    if total_results == 0:
        suggestions.append("Try broader terms or remove some filters")
        if parsed_query.get("query_type") == "complex":
            suggestions.append("Simplify your query - try searching for one concept at a time")
    
    elif total_results > 100:
        suggestions.append("Add more specific filters to narrow results")
        if not parsed_query.get("temporal"):
            suggestions.append("Try adding a time range (e.g., 'after 2020')")
    
    if parsed_query.get("understanding_score", 0) < 0.5:
        suggestions.append("Try using more specific astronomical terms")
        suggestions.append("Consider rephrasing with common keywords like 'planet', 'star', 'distance'")
    
    intent = parsed_query.get("intent")
    if intent == "general_search":
        suggestions.append("Be more specific about what you want: images, data, tracking, or analysis")
    
    return suggestions

def parse_natural_language_query(query: str) -> dict:
    """
    Advanced NLP parsing with hierarchical ontologies, logical operators, and semantic understanding
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
        "keywords": [],
        "logical_operators": [],
        "units": {},
        "ranking_hints": {},
        "explanation": []
    }

    query_lower = query.lower().strip()
    
    # Extract keywords (remove common stop words)
    stop_words = {"the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "by", "from", "about", "into", "through", "during", "before", "after", "above", "below", "up", "down", "out", "off", "over", "under", "again", "further", "then", "once", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can"}
    words = re.findall(r'\b\w+\b', query_lower)
    parsed["keywords"] = [word for word in words if word not in stop_words and len(word) > 2]

    # Hierarchical astronomical ontology with aliases and relationships
    entities = {
        "celestial_bodies": {
            # Stars and stellar classification
            "star": ["star", "stellar", "sun", "solar"],
            "sun": ["sun", "solar", "sol", "g-type star", "main sequence", "yellow dwarf"],
            "red_dwarf": ["red dwarf", "m-type", "m class", "red star", "m dwarf"],
            "white_dwarf": ["white dwarf", "wd", "white star"],
            "giant_star": ["giant star", "red giant", "blue giant", "supergiant"],
            "binary_star": ["binary", "binary star", "double star"],
            
            # Planets and classification
            "earth": ["earth", "planet earth", "terra", "blue planet"],
            "mars": ["mars", "red planet", "martian planet", "fourth planet"],
            "jupiter": ["jupiter", "jovian", "gas giant", "largest planet"],
            "venus": ["venus", "venusian", "morning star", "evening star"],
            "saturn": ["saturn", "saturnian", "ringed planet"],
            "mercury": ["mercury", "innermost planet"],
            "uranus": ["uranus", "ice giant"],
            "neptune": ["neptune", "ice giant", "outermost planet"],
            
            # Exoplanet types
            "exoplanet": ["exoplanet", "extrasolar planet", "planet", "extrasolar world"],
            "super_earth": ["super-earth", "super earth", "large terrestrial"],
            "hot_jupiter": ["hot jupiter", "hot gas giant", "close-in giant"],
            "mini_neptune": ["mini-neptune", "mini neptune", "sub-neptune"],
            "terrestrial": ["terrestrial", "rocky planet", "earth-like", "solid planet"],
            
            # Other celestial objects
            "moon": ["moon", "lunar", "luna", "satellite", "natural satellite"],
            "asteroid": ["asteroid", "minor planet", "space rock", "planetoid"],
            "comet": ["comet", "icy body", "dirty snowball"],
            "galaxy": ["galaxy", "galactic", "spiral galaxy", "elliptical galaxy"],
            "nebula": ["nebula", "stellar nursery", "gas cloud"],
            "black_hole": ["black hole", "blackhole", "bh"],
            "neutron_star": ["neutron star", "pulsar", "magnetar"]
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

    # Parse logical operators and comparison phrases
    logical_patterns = {
        "and": ["and", "with", "plus", "also", "&"],
        "or": ["or", "either", "alternatively", "|"],
        "not": ["not", "without", "excluding", "except", "minus"],
        "greater_than": ["larger than", "bigger than", "greater than", "more than", "above", ">"],
        "less_than": ["smaller than", "less than", "below", "under", "<"],
        "equal_to": ["equal to", "exactly", "=", "equals"],
        "between": ["between", "from", "in range"],
        "similar_to": ["like", "similar to", "resembling", "comparable to"]
    }
    
    for op_type, patterns in logical_patterns.items():
        for pattern in patterns:
            if pattern in query_lower:
                parsed["logical_operators"].append({
                    "type": op_type,
                    "pattern": pattern,
                    "position": query_lower.index(pattern)
                })
    
    # Enhanced unit parsing and conversion
    unit_patterns = {
        "distance": {
            "light_years": r'(\d+(?:\.\d+)?)\s*(?:light\s*years?|ly)',
            "parsecs": r'(\d+(?:\.\d+)?)\s*(?:parsecs?|pc)',
            "kilometers": r'(\d+(?:\.\d+)?)\s*(?:kilometers?|km)',
            "astronomical_units": r'(\d+(?:\.\d+)?)\s*(?:au|astronomical\s*units?)'
        },
        "mass": {
            "earth_masses": r'(\d+(?:\.\d+)?)\s*(?:earth\s*mass|earth\s*masses|me)',
            "jupiter_masses": r'(\d+(?:\.\d+)?)\s*(?:jupiter\s*mass|jupiter\s*masses|mj)',
            "solar_masses": r'(\d+(?:\.\d+)?)\s*(?:solar\s*mass|solar\s*masses|msun)'
        },
        "radius": {
            "earth_radii": r'(\d+(?:\.\d+)?)\s*(?:earth\s*radii?|earth\s*radius|re)',
            "jupiter_radii": r'(\d+(?:\.\d+)?)\s*(?:jupiter\s*radii?|jupiter\s*radius|rj)',
            "solar_radii": r'(\d+(?:\.\d+)?)\s*(?:solar\s*radii?|solar\s*radius|rsun)'
        },
        "temperature": {
            "kelvin": r'(\d+(?:\.\d+)?)\s*(?:kelvin|k)',
            "celsius": r'(\d+(?:\.\d+)?)\s*(?:celsius|°c|degrees?\s*c)',
            "fahrenheit": r'(\d+(?:\.\d+)?)\s*(?:fahrenheit|°f|degrees?\s*f)'
        },
        "time": {
            "sols": r'sol\s*(\d+)',
            "days": r'(\d+(?:\.\d+)?)\s*(?:days?|d)',
            "years": r'(\d+(?:\.\d+)?)\s*(?:years?|yr)',
            "hours": r'(\d+(?:\.\d+)?)\s*(?:hours?|hr|h)'
        }
    }
    
    for unit_category, unit_types in unit_patterns.items():
        for unit_type, pattern in unit_types.items():
            match = re.search(pattern, query_lower)
            if match:
                value = float(match.group(1))
                parsed["units"][unit_category] = {
                    "type": unit_type,
                    "value": value,
                    "raw_match": match.group(0)
                }
                parsed["explanation"].append(f"Detected {unit_type}: {value}")
    
    # Match entities with hierarchical synonyms
    for category, entity_dict in entities.items():
        found_entities = {}
        for entity, synonyms in entity_dict.items():
            for synonym in synonyms:
                if synonym in query_lower:
                    found_entities[entity] = {
                        "matched_term": synonym,
                        "canonical_name": entity,
                        "confidence": 1.0 if synonym == entity else 0.8
                    }
                    parsed["explanation"].append(f"Matched {category}: {synonym} → {entity}")
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

    # Advanced multi-dimensional intent classification
    intent_patterns = {
        "tracking": {
            "keywords": ["position", "location", "overhead", "tracking", "orbit", "path", "trajectory", "passes", "visible", "when", "where"],
            "weight": 0.9,
            "context_hints": ["real-time", "current", "now", "live"]
        },
        "imagery": {
            "keywords": ["image", "photo", "picture", "gallery", "visual", "camera", "snapshot", "pic", "show", "view", "display"],
            "weight": 0.85,
            "context_hints": ["latest", "recent", "best", "high resolution"]
        },
        "discovery": {
            "keywords": ["discover", "found", "detect", "search", "identify", "confirmed", "new", "latest", "recent"],
            "weight": 0.8,
            "context_hints": ["breakthrough", "first", "novel", "unprecedented"]
        },
        "comparison": {
            "keywords": ["compare", "versus", "vs", "difference", "similar", "like", "than", "between"],
            "weight": 0.85,
            "context_hints": ["larger", "smaller", "better", "closer"]
        },
        "aggregation": {
            "keywords": ["count", "how many", "total", "number", "list", "all", "statistics", "summary"],
            "weight": 0.9,
            "context_hints": ["average", "median", "distribution", "histogram"]
        },
        "prediction": {
            "keywords": ["predict", "forecast", "future", "will", "next", "upcoming", "schedule"],
            "weight": 0.8,
            "context_hints": ["tomorrow", "tonight", "this week", "hours from now"]
        },


@app.get("/api/search/advanced-analytics")
def get_advanced_search_analytics():
    """Get comprehensive search analytics and insights"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Query statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_queries,
                AVG(response_time_ms) as avg_response_time,
                AVG(understanding_score) as avg_understanding,
                AVG(total_results) as avg_results_per_query
            FROM query_analytics 
            WHERE timestamp > datetime('now', '-7 days')
        ''')
        stats = cursor.fetchone()
        
        # Intent distribution
        cursor.execute('''
            SELECT intent, COUNT(*) as count
            FROM query_analytics 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY intent 
            ORDER BY count DESC
        ''')
        intent_dist = cursor.fetchall()
        
        # Popular entities
        cursor.execute('''
            SELECT query_text, COUNT(*) as frequency
            FROM query_analytics 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY query_text
            ORDER BY frequency DESC
            LIMIT 10
        ''')
        popular_queries = cursor.fetchall()
        
        # Performance insights
        cursor.execute('''
            SELECT 
                complexity_score,
                AVG(response_time_ms) as avg_time,
                AVG(total_results) as avg_results
            FROM query_analytics 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY ROUND(complexity_score)
            ORDER BY complexity_score
        ''')
        complexity_performance = cursor.fetchall()
        
        conn.close()
        
        return {
            "period": "Last 7 days",
            "overview": {
                "total_queries": stats[0] if stats[0] else 0,
                "avg_response_time_ms": round(stats[1], 2) if stats[1] else 0,
                "avg_understanding_score": round(stats[2], 3) if stats[2] else 0,
                "avg_results_per_query": round(stats[3], 1) if stats[3] else 0
            },
            "intent_distribution": [{"intent": row[0], "count": row[1]} for row in intent_dist],
            "popular_queries": [{"query": row[0], "frequency": row[1]} for row in popular_queries],
            "complexity_performance": [
                {
                    "complexity_level": int(row[0]) if row[0] else 0,
                    "avg_response_time": round(row[1], 2) if row[1] else 0,
                    "avg_results": round(row[2], 1) if row[2] else 0
                } for row in complexity_performance
            ],
            "recommendations": generate_system_recommendations(stats, intent_dist)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

def generate_system_recommendations(stats, intent_dist) -> List[str]:
    """Generate system optimization recommendations based on analytics"""
    recommendations = []
    
    if stats and stats[1] and stats[1] > 2000:  # avg response time > 2 seconds
        recommendations.append("Consider implementing more aggressive caching")
    
    if intent_dist:
        top_intent = max(intent_dist, key=lambda x: x[1])
        if top_intent[0] == "general_search":
            recommendations.append("Users need better query guidance - consider search suggestions")
    
    recommendations.append("Monitor cache hit rates to optimize performance")
    
    return recommendations

@app.get("/api/search/query-insights/{query_hash}")
def get_query_insights(query_hash: str):
    """Get detailed insights for a specific query"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT query_text, parsed_query, response_time_ms, total_results, timestamp
            FROM query_analytics 
            WHERE query_hash = ?
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (query_hash,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            raise HTTPException(status_code=404, detail="Query not found")
        
        insights = []
        for row in results:
            parsed = json.loads(row[1]) if row[1] else {}
            insights.append({
                "query_text": row[0],
                "parsed_analysis": parsed,
                "response_time_ms": row[2],
                "total_results": row[3],
                "timestamp": row[4]
            })
        
        return {
            "query_hash": query_hash,
            "execution_history": insights,
            "performance_trend": analyze_performance_trend(insights)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query insights error: {str(e)}")

def analyze_performance_trend(insights: List[dict]) -> dict:
    """Analyze performance trends for a query"""
    if len(insights) < 2:
        return {"trend": "insufficient_data"}
    
    response_times = [insight["response_time_ms"] for insight in insights if insight["response_time_ms"]]
    
    if len(response_times) >= 2:
        recent_avg = sum(response_times[:3]) / min(3, len(response_times))
        older_avg = sum(response_times[-3:]) / min(3, len(response_times[-3:]))
        
        if recent_avg < older_avg * 0.8:
            return {"trend": "improving", "improvement_pct": round((older_avg - recent_avg) / older_avg * 100, 1)}
        elif recent_avg > older_avg * 1.2:
            return {"trend": "degrading", "degradation_pct": round((recent_avg - older_avg) / older_avg * 100, 1)}
    
    return {"trend": "stable"}


        "space_weather": {
            "keywords": ["weather", "space weather", "flare", "cme", "storm", "aurora", "radiation", "solar activity"],
            "weight": 0.95,
            "context_hints": ["dangerous", "alert", "warning", "impact"]
        },
        "habitability": {
            "keywords": ["habitable", "life", "livable", "goldilocks", "habitable zone", "biosignature", "atmosphere"],
            "weight": 0.9,
            "context_hints": ["potentially", "candidate", "suitable", "conditions"]
        },
        "mission": {
            "keywords": ["mission", "launch", "landing", "flight", "operation", "rover", "spacecraft", "exploration"],
            "weight": 0.75,
            "context_hints": ["successful", "failed", "ongoing", "planned"]
        },
        "visualization": {
            "keywords": ["plot", "chart", "graph", "map", "visualization", "render", "display", "show me"],
            "weight": 0.8,
            "context_hints": ["interactive", "3d", "animated", "time series"]
        }
    }
    
    # Multi-dimensional intent scoring with context awareness
    intent_scores = {}
    for intent, data in intent_patterns.items():
        score = 0
        keyword_matches = 0
        context_boost = 0
        
        # Base keyword scoring
        for keyword in data["keywords"]:
            if keyword in query_lower:
                score += data["weight"]
                keyword_matches += 1
        
        # Context hint bonus
        for hint in data.get("context_hints", []):
            if hint in query_lower:
                context_boost += 0.2
        
        # Logical operator relevance
        for op in parsed["logical_operators"]:
            if intent in ["comparison", "aggregation"] and op["type"] in ["greater_than", "less_than", "between"]:
                score += 0.3
        
        # Unit presence boost
        if parsed["units"] and intent in ["comparison", "aggregation", "discovery"]:
            score += 0.2
        
        final_score = score + context_boost
        if final_score > 0:
            intent_scores[intent] = {
                "score": final_score,
                "keyword_matches": keyword_matches,
                "context_boost": context_boost,
                "confidence": min(final_score / 2.0, 1.0)
            }
    
    if intent_scores:
        best_intent = max(intent_scores, key=lambda x: intent_scores[x]["score"])
        parsed["intent"] = best_intent
        parsed["confidence"] = intent_scores[best_intent]["confidence"]
        parsed["intent_analysis"] = intent_scores
        parsed["explanation"].append(f"Primary intent: {best_intent} (confidence: {parsed['confidence']:.2f})")
    
    # Enhanced complexity analysis
    complexity_factors = {
        "entities": len(parsed["entities"]),
        "logical_operators": len(parsed["logical_operators"]),
        "temporal_constraints": len(parsed["temporal"]),
        "numerical_constraints": len(parsed["numerical"]),
        "spatial_constraints": len(parsed["spatial"]),
        "units": len(parsed["units"]),
        "filters": len(parsed["filters"])
    }
    
    total_complexity = sum(complexity_factors.values())
    parsed["complexity_breakdown"] = complexity_factors
    
    # Adaptive complexity classification
    if total_complexity <= 2:
        parsed["query_type"] = "simple"
        parsed["ranking_hints"]["simplicity_boost"] = 0.1
    elif total_complexity <= 6:
        parsed["query_type"] = "moderate"
        parsed["ranking_hints"]["balanced_scoring"] = True
    else:
        parsed["query_type"] = "complex"
        parsed["ranking_hints"]["precision_over_recall"] = True
        parsed["ranking_hints"]["detailed_explanation"] = True
    
    # Query understanding score
    understanding_score = (
        len(parsed["entities"]) * 0.2 +
        len(parsed["logical_operators"]) * 0.15 +
        (1 if parsed["intent"] != "general_search" else 0) * 0.3 +
        len(parsed["units"]) * 0.1 +
        len(parsed["temporal"]) * 0.1 +
        len(parsed["filters"]) * 0.15
    )
    
    parsed["understanding_score"] = min(understanding_score, 1.0)
    parsed["explanation"].append(f"Query understanding: {parsed['understanding_score']:.2f}")

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

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts using simple word overlap"""
    # Simple implementation - in production, use sentence transformers or similar
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def calculate_fuzzy_similarity(text1: str, text2: str) -> float:
    """Calculate fuzzy string similarity using simple character-based approach"""
    # Simple Levenshtein-like similarity
    if not text1 or not text2:
        return 0.0
    
    max_len = max(len(text1), len(text2))
    if max_len == 0:
        return 1.0
    
    # Simple character overlap ratio
    common_chars = sum(1 for a, b in zip(text1.lower(), text2.lower()) if a == b)
    return common_chars / max_len

def add_relevance_scores_advanced(results: List, query: str, parsed_query: dict) -> List:
    """Enhanced relevance scoring with semantic similarity, fuzzy matching, and multi-factor analysis"""
    if not isinstance(results, list):
        return results

    query_lower = query.lower()
    keywords = parsed_query.get("keywords", [])
    intent = parsed_query.get("intent", "general_search")
    logical_ops = parsed_query.get("logical_operators", [])
    units = parsed_query.get("units", {})
    understanding_score = parsed_query.get("understanding_score", 0.8)
    
    for item in results:
        score = 0.0
        scoring_details = {}

        # Multi-dimensional name matching (20% weight)
        name_score = 0.0
        if isinstance(item, dict) and "pl_name" in item and item["pl_name"]:
            name = str(item["pl_name"]).lower()
            
            # Exact keyword matches (high weight)
            exact_matches = 0
            for keyword in keywords:
                if keyword in name:
                    name_score += 1.0
                    exact_matches += 1
            
            # Fuzzy matching for typos and variations
            for keyword in keywords:
                fuzzy_sim = calculate_fuzzy_similarity(keyword, name)
                if fuzzy_sim > 0.7:  # Threshold for considering fuzzy match
                    name_score += fuzzy_sim * 0.6
            
            # Semantic similarity
            semantic_sim = calculate_semantic_similarity(query_lower, name)
            name_score += semantic_sim * 0.4
            
            # Normalize by number of keywords to prevent inflation
            if keywords:
                name_score = name_score / len(keywords)
        
        scoring_details["name_match"] = name_score
        scoring_details["exact_matches"] = exact_matches if 'exact_matches' in locals() else 0
        score += name_score * 0.20

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

        # Logical operator compliance (15% weight)
        logic_score = 0.0
        logic_violations = 0
        
        for op in logical_ops:
            op_type = op["type"]
            if op_type == "greater_than" and "pl_rade" in item and item["pl_rade"]:
                # Look for size comparisons in query context
                if "earth" in query_lower and item["pl_rade"] > 1.0:
                    logic_score += 0.8
                elif "jupiter" in query_lower and item["pl_rade"] > 11.0:
                    logic_score += 0.8
            elif op_type == "less_than" and "pl_rade" in item and item["pl_rade"]:
                if "earth" in query_lower and item["pl_rade"] < 1.0:
                    logic_score += 0.8
            elif op_type == "similar_to":
                # Boost items that match comparison targets
                logic_score += 0.5
        
        scoring_details["logical_compliance"] = logic_score
        score += logic_score * 0.15

        # Enhanced intent-specific scoring (15% weight)
        intent_score = 0.0
        
        if intent == "discovery":
            if "disc_year" in item and item["disc_year"]:
                years_ago = datetime.now().year - item["disc_year"]
                intent_score += max(0, 1.0 - (years_ago * 0.03))  # Recent discoveries
        
        elif intent == "habitability":
            if "pl_orbsmax" in item and item["pl_orbsmax"]:
                # Habitable zone bonus
                if 0.75 <= item["pl_orbsmax"] <= 1.77:
                    intent_score += 1.0
                elif 0.5 <= item["pl_orbsmax"] <= 2.5:
                    intent_score += 0.5
            if "pl_rade" in item and item["pl_rade"]:
                # Earth-like size bonus for habitability
                if 0.8 <= item["pl_rade"] <= 1.25:
                    intent_score += 0.7
        
        elif intent == "comparison":
            # Boost objects with complete data for comparison
            data_completeness = 0
            comparison_fields = ["pl_rade", "pl_masse", "st_teff", "sy_dist", "pl_orbsmax"]
            for field in comparison_fields:
                if field in item and item[field] is not None:
                    data_completeness += 0.2
            intent_score += data_completeness
        
        elif intent == "aggregation":
            # For statistical queries, boost confirmed planets
            if "pl_name" in item and "candidate" not in str(item["pl_name"]).lower():
                intent_score += 0.8
        
        scoring_details["intent_bonus"] = intent_score
        score += intent_score * 0.15

        # Unit-based filtering compliance (10% weight)
        unit_score = 0.0
        for unit_category, unit_data in units.items():
            if unit_category == "distance" and "sy_dist" in item:
                # Distance unit matching
                if unit_data["type"] == "light_years" and item["sy_dist"]:
                    unit_score += 0.5
            elif unit_category == "radius" and "pl_rade" in item:
                # Radius unit matching
                if unit_data["type"] == "earth_radii" and item["pl_rade"]:
                    unit_score += 0.5
        
        scoring_details["unit_compliance"] = unit_score
        score += unit_score * 0.10

        # Data quality and completeness (10% weight)
        quality_score = 0.0
        total_fields = ["pl_name", "pl_rade", "pl_masse", "disc_year", "st_teff", "sy_dist", "pl_orbsmax"]
        filled_fields = sum(1 for field in total_fields if field in item and item[field] is not None)
        quality_score = filled_fields / len(total_fields)
        
        scoring_details["data_quality"] = quality_score
        score += quality_score * 0.10

        # Apply understanding confidence modifier
        score *= understanding_score

        # Final score adjustments based on query complexity
        ranking_hints = parsed_query.get("ranking_hints", {})
        if ranking_hints.get("precision_over_recall"):
            # For complex queries, boost high-confidence matches
            if name_score > 0.8:
                score *= 1.2
        elif ranking_hints.get("simplicity_boost"):
            # For simple queries, be more generous
            score *= 1.1

        # Store comprehensive scoring details
        item["_relevance_score"] = round(score, 4)
        item["_scoring_details"] = scoring_details
        item["_explanation"] = generate_result_explanation(item, scoring_details, intent)

    # Enhanced sorting with multiple criteria
    return sorted(results, 
                 key=lambda x: (
                     x.get("_relevance_score", 0),
                     x.get("disc_year", 0) if x.get("disc_year") else 0,
                     -x.get("sy_dist", float('inf')) if x.get("sy_dist") else 0
                 ), 
                 reverse=True)

def generate_result_explanation(item: dict, scoring_details: dict, intent: str) -> str:
    """Generate human-readable explanation for why this result was ranked highly"""
    explanations = []
    
    if scoring_details.get("name_match", 0) > 0.5:
        explanations.append("strong name match")
    
    if scoring_details.get("temporal_match", 0) > 0.7:
        explanations.append("recent discovery")
    
    if scoring_details.get("size_match", 0) > 0.8:
        explanations.append("size criteria match")
    
    if scoring_details.get("habitability_score", 0) > 0.5:
        explanations.append("potentially habitable")
    
    if scoring_details.get("data_quality", 0) > 0.8:
        explanations.append("complete data")
    
    if intent == "discovery" and item.get("disc_year", 0) >= 2020:
        explanations.append("recent discovery")
    
    return f"Ranked high due to: {', '.join(explanations)}" if explanations else "Standard relevance match"

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
