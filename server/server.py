
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
    description="Unified API for NASA Exoplanets, ISS tracking, and Mars data",
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
# HEALTH CHECK
# ==============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "NASA Space Data Hub API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
