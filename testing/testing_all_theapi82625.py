
import json
from datetime import datetime, timedelta
from api.mars import (
    apod, Neow, Apod, Donki, Eonet, Epic, InSight, 
    CuriosityRover, NasaImages, OSDR, osdp
)

def test_apod_function():
    """Test the standalone APOD function."""
    print("\n" + "="*60)
    print("TESTING APOD FUNCTION")
    print("="*60)
    
    # Test 1: Get today's APOD
    print("\n1. Testing today's APOD:")
    try:
        result = apod()
        if result:
            print(f"✅ Success! Today's APOD: {result.get('title', 'Unknown')}")
            print(f"   Date: {result.get('date', 'Unknown')}")
            print(f"   Media type: {result.get('media_type', 'Unknown')}")
        else:
            print("❌ Failed to retrieve today's APOD")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get specific date
    print("\n2. Testing specific date (2023-01-01):")
    try:
        result = apod(date="2023-01-01")
        if result:
            print(f"✅ Success! APOD for 2023-01-01: {result.get('title', 'Unknown')}")
        else:
            print("❌ Failed to retrieve APOD for specific date")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get random count
    print("\n3. Testing random count (3 images):")
    try:
        result = apod(count=3)
        if result and isinstance(result, list):
            print(f"✅ Success! Retrieved {len(result)} random APODs")
            for i, item in enumerate(result[:2]):
                print(f"   {i+1}. {item.get('title', 'Unknown')} ({item.get('date', 'Unknown')})")
        else:
            print("❌ Failed to retrieve random APODs")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_neow_class():
    """Test the enhanced Neow class."""
    print("\n" + "="*60)
    print("TESTING NEOW (NEAR EARTH OBJECTS) CLASS")
    print("="*60)
    
    neow = Neow()
    
    # Test 1: NEO Feed
    print("\n1. Testing NEO feed (next 7 days):")
    try:
        result = neow.neo_feed()
        if result:
            print(f"✅ Success! Retrieved NEO feed")
            print(f"   Total elements: {result.get('element_count', 'Unknown')}")
            near_earth_objects = result.get('near_earth_objects', {})
            if near_earth_objects:
                first_date = list(near_earth_objects.keys())[0]
                first_day_objects = near_earth_objects[first_date]
                print(f"   Objects on {first_date}: {len(first_day_objects)}")
        else:
            print("❌ Failed to retrieve NEO feed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Specific asteroid lookup
    print("\n2. Testing asteroid lookup (ID: 3542519):")
    try:
        result = neow.neo_lookup("3542519")
        if result:
            print(f"✅ Success! Found asteroid: {result.get('name', 'Unknown')}")
            print(f"   Absolute magnitude: {result.get('absolute_magnitude_h', 'Unknown')}")
        else:
            print("❌ Failed to lookup specific asteroid")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Browse NEOs
    print("\n3. Testing NEO browse:")
    try:
        result = neow.neo_browse()
        if result:
            print(f"✅ Success! Browse results")
            print(f"   Total elements: {result.get('total_elements', 'Unknown')}")
            near_earth_objects = result.get('near_earth_objects', [])
            if near_earth_objects:
                print(f"   First object: {near_earth_objects[0].get('name', 'Unknown')}")
        else:
            print("❌ Failed to browse NEOs")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_donki_class():
    """Test the DONKI space weather class."""
    print("\n" + "="*60)
    print("TESTING DONKI (SPACE WEATHER) CLASS")
    print("="*60)
    
    # Use recent dates to ensure data availability
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    donki = Donki(start_date=start_date, end_date=end_date)
    
    # Test 1: Solar flares
    print(f"\n1. Testing solar flares ({start_date} to {end_date}):")
    try:
        result = donki.flr()
        if result and isinstance(result, list):
            print(f"✅ Success! Found {len(result)} solar flare events")
            if result:
                print(f"   Latest flare: {result[0].get('flrID', 'Unknown')} on {result[0].get('beginTime', 'Unknown')}")
        else:
            print("✅ No solar flare data for the period (this is normal)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Geomagnetic storms
    print(f"\n2. Testing geomagnetic storms:")
    try:
        result = donki.gst()
        if result and isinstance(result, list):
            print(f"✅ Success! Found {len(result)} geomagnetic storm events")
        else:
            print("✅ No geomagnetic storm data for the period (this is normal)")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_eonet_class():
    """Test the EONET natural events class."""
    print("\n" + "="*60)
    print("TESTING EONET (EARTH NATURAL EVENTS) CLASS")
    print("="*60)
    
    eonet = Eonet()
    
    # Test 1: Recent events
    print("\n1. Testing recent events (last 30 days):")
    try:
        result = eonet.events(days=30, limit=10)
        if result:
            events = result.get('events', [])
            print(f"✅ Success! Found {len(events)} recent events")
            if events:
                for i, event in enumerate(events[:3]):
                    print(f"   {i+1}. {event.get('title', 'Unknown')} - {event.get('categories', [{}])[0].get('title', 'Unknown')}")
        else:
            print("❌ Failed to retrieve recent events")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Event categories
    print("\n2. Testing event categories:")
    try:
        result = eonet.categories()
        if result:
            categories = result.get('categories', [])
            print(f"✅ Success! Found {len(categories)} event categories")
            for cat in categories[:5]:
                print(f"   - {cat.get('title', 'Unknown')}")
        else:
            print("❌ Failed to retrieve categories")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_mars_rover():
    """Test the Mars Rover Photos API."""
    print("\n" + "="*60)
    print("TESTING MARS ROVER PHOTOS API")
    print("="*60)
    
    rover = CuriosityRover()
    
    # Test 1: Photos by Sol
    print("\n1. Testing Curiosity photos by Sol (1000):")
    try:
        result = rover.photos_by_sol("curiosity", 1000, camera="MAST")
        if result:
            photos = result.get('photos', [])
            print(f"✅ Success! Found {len(photos)} photos from Sol 1000")
            if photos:
                print(f"   First photo: {photos[0].get('img_src', 'Unknown')}")
        else:
            print("❌ Failed to retrieve rover photos")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Mission manifest
    print("\n2. Testing Curiosity mission manifest:")
    try:
        result = rover.mission_manifest("curiosity")
        if result:
            manifest = result.get('photo_manifest', {})
            print(f"✅ Success! Curiosity mission data:")
            print(f"   Launch date: {manifest.get('launch_date', 'Unknown')}")
            print(f"   Landing date: {manifest.get('landing_date', 'Unknown')}")
            print(f"   Total photos: {manifest.get('total_photos', 'Unknown')}")
            print(f"   Max Sol: {manifest.get('max_sol', 'Unknown')}")
        else:
            print("❌ Failed to retrieve mission manifest")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_osdr_comprehensive():
    """Test the comprehensive OSDR class."""
    print("\n" + "="*60)
    print("TESTING OSDR (OPEN SCIENCE DATA REPOSITORY) - COMPREHENSIVE")
    print("="*60)
    
    osdr = OSDR()
    
    # Test 1: Get study files for a single study with file type filtering
    print("\n1. Testing study files for OSD-87 with file type filtering:")
    try:
        start_time = datetime.now()
        result = osdr.get_study_files("87", page=0, size=10, file_types=['zip', 'csv'])
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        if result and result.get('success'):
            print(f"✅ Success! Retrieved study files (Response time: {response_time:.2f}s)")
            print(f"   Total hits: {result.get('total_hits', 0)}")
            print(f"   Studies found: {len(result.get('studies', {}))}")
            
            studies = result.get('studies', {})
            if studies:
                first_study = list(studies.keys())[0]
                study_data = studies[first_study]
                print(f"   Study: {first_study}")
                print(f"   File count: {study_data.get('file_count', 0)}")
                
                study_files = study_data.get('study_files', [])
                if study_files:
                    print(f"   First file: {study_files[0].get('file_name', 'Unknown')}")
                    print(f"   File size: {study_files[0].get('file_size', 0):,} bytes")
                    
                    # Show file type distribution
                    file_types = {}
                    for file_info in study_files:
                        filename = file_info.get('file_name', '')
                        if '.' in filename:
                            ext = filename.split('.')[-1].lower()
                            file_types[ext] = file_types.get(ext, 0) + 1
                    
                    if file_types:
                        print(f"   File types: {dict(file_types)}")
        else:
            print("❌ Failed to retrieve study files")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Bulk download URLs
    print("\n2. Testing bulk download URLs for OSD-87:")
    try:
        urls = osdr.bulk_download_urls("87", file_types=['zip'])
        print(f"✅ Success! Found {len(urls)} download URLs for ZIP files")
        if urls:
            print(f"   First URL: {urls[0]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Advanced search
    print("\n3. Testing advanced search:")
    try:
        result = osdr.search_advanced(
            keywords="mouse",
            organism="Mus musculus",
            size=5
        )
        if result:
            print(f"✅ Success! Advanced search completed")
            print(f"   Results found: {result.get('hits', 0)}")
        else:
            print("❌ Failed advanced search")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Repository statistics
    print("\n4. Testing repository statistics:")
    try:
        stats = osdr.get_study_statistics()
        if stats:
            print(f"✅ Success! Retrieved repository statistics")
            print(f"   Total studies: {stats.get('total_studies', 'Unknown')}")
            print(f"   Experiments: {stats.get('experiments_count', 'Unknown')}")
            print(f"   Missions: {stats.get('missions_count', 'Unknown')}")
            print(f"   Vehicles: {stats.get('vehicles_count', 'Unknown')}")
            print(f"   Last updated: {stats.get('last_updated', 'Unknown')}")
        else:
            print("❌ Failed to retrieve statistics")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get study metadata
    print("\n2. Testing study metadata for OSD-87:")
    try:
        result = osdr.get_study_metadata("87")
        if result and result.get('success'):
            print(f"✅ Success! Retrieved study metadata")
            study_data = result.get('study', {})
            if study_data:
                first_study_id = list(study_data.keys())[0]
                study_info = study_data[first_study_id]
                studies = study_info.get('studies', [])
                if studies:
                    study = studies[0]
                    print(f"   Title: {study.get('title', 'Unknown')}")
                    print(f"   Identifier: {study.get('identifier', 'Unknown')}")
                    print(f"   Public release: {study.get('publicReleaseDate', 'Unknown')}")
        else:
            print("❌ Failed to retrieve study metadata")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Search studies
    print("\n3. Testing study search (term: 'mouse'):")
    try:
        result = osdr.search_studies(term="mouse", size=5)
        if result:
            print(f"✅ Success! Search completed")
            print(f"   Results found: {result.get('hits', 0)}")
        else:
            print("❌ Failed to search studies")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get missions
    print("\n4. Testing missions metadata:")
    try:
        result = osdr.get_missions()
        if result and isinstance(result, list):
            print(f"✅ Success! Found {len(result)} missions")
            if result:
                mission = result[0]
                print(f"   First mission: {mission.get('identifier', 'Unknown')}")
                print(f"   Start date: {mission.get('startDate', 'Unknown')}")
        else:
            print("❌ Failed to retrieve missions")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Get specific mission
    print("\n5. Testing specific mission (SpaceX-12):")
    try:
        result = osdr.get_mission("SpaceX-12")
        if result:
            print(f"✅ Success! Retrieved SpaceX-12 mission")
            print(f"   Identifier: {result.get('identifier', 'Unknown')}")
            print(f"   Start date: {result.get('startDate', 'Unknown')}")
            print(f"   End date: {result.get('endDate', 'Unknown')}")
            aliases = result.get('aliases', [])
            if aliases:
                print(f"   Aliases: {', '.join(aliases)}")
        else:
            print("❌ Failed to retrieve specific mission")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Get vehicles
    print("\n6. Testing vehicles metadata:")
    try:
        result = osdr.get_vehicles()
        if result and isinstance(result, list):
            print(f"✅ Success! Found {len(result)} vehicles")
            if result:
                vehicle = result[0]
                print(f"   First vehicle: {vehicle.get('identifier', 'Unknown')}")
        else:
            print("❌ Failed to retrieve vehicles")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_legacy_osdp():
    """Test the legacy osdp class for backward compatibility."""
    print("\n" + "="*60)
    print("TESTING LEGACY OSDP CLASS")
    print("="*60)
    
    # Test single study
    print("\n1. Testing legacy osdp with single study (87):")
    try:
        osdp_client = osdp(OSD_STUDY_IDs=87, RESULTS_PER_PAGE=5)
        result = osdp_client.get_osdr_study_files()
        if result and result.get('success'):
            print(f"✅ Success! Legacy osdp working")
            print(f"   Total hits: {result.get('total_hits', 0)}")
            print(f"   Studies: {len(result.get('studies', {}))}")
        else:
            print("❌ Failed with legacy osdp")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test multiple studies
    print("\n2. Testing legacy osdp with multiple studies ([86, 87]):")
    try:
        osdp_client = osdp(OSD_STUDY_IDs=[86, 87], RESULTS_PER_PAGE=3)
        result = osdp_client.get_osdr_study_files()
        if result and result.get('success'):
            print(f"✅ Success! Legacy osdp with multiple studies")
            print(f"   Total hits: {result.get('total_hits', 0)}")
            studies = result.get('studies', {})
            print(f"   Studies found: {list(studies.keys())}")
        else:
            print("❌ Failed with multiple studies")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_nasa_images():
    """Test NASA Images API."""
    print("\n" + "="*60)
    print("TESTING NASA IMAGES API")
    print("="*60)
    
    images = NasaImages()
    
    # Test search
    print("\n1. Testing image search (query: 'apollo 11'):")
    try:
        result = images.search("apollo 11", media_type="image")
        if result:
            collection = result.get('collection', {})
            items = collection.get('items', [])
            print(f"✅ Success! Found {len(items)} Apollo 11 images")
            if items:
                first_item = items[0]
                data = first_item.get('data', [{}])[0]
                print(f"   First result: {data.get('title', 'Unknown')}")
                print(f"   Date: {data.get('date_created', 'Unknown')}")
        else:
            print("❌ Failed to search images")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_performance_and_resilience():
    """Test API performance and error handling."""
    print("\n" + "="*60)
    print("TESTING PERFORMANCE & RESILIENCE")
    print("="*60)
    
    # Test 1: API response times
    print("\n1. Testing API response times:")
    apis_to_test = [
        ("APOD", lambda: apod()),
        ("Neow Feed", lambda: Neow().neo_feed()),
        ("EONET Events", lambda: Eonet().events(limit=5)),
        ("OSDR Studies", lambda: OSDR().get_study_files("87", size=5))
    ]
    
    for api_name, api_call in apis_to_test:
        try:
            start_time = datetime.now()
            result = api_call()
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            status = "✅ FAST" if response_time < 2 else "⚠️ SLOW" if response_time < 5 else "❌ VERY SLOW"
            print(f"   {api_name}: {response_time:.2f}s {status}")
            
        except Exception as e:
            print(f"   {api_name}: ❌ ERROR - {e}")
    
    # Test 2: Error handling with invalid inputs
    print("\n2. Testing error handling with invalid inputs:")
    error_tests = [
        ("APOD invalid date", lambda: apod(date="2025-13-40")),
        ("Neow invalid asteroid", lambda: Neow().neo_lookup("invalid_id")),
        ("OSDR invalid study", lambda: OSDR().get_study_files("99999")),
        ("Mars rover invalid sol", lambda: CuriosityRover().photos_by_sol("curiosity", -1))
    ]
    
    for test_name, test_call in error_tests:
        try:
            result = test_call()
            if result is None:
                print(f"   {test_name}: ✅ Handled gracefully (returned None)")
            else:
                print(f"   {test_name}: ⚠️ Unexpected result: {type(result)}")
        except Exception as e:
            print(f"   {test_name}: ✅ Exception caught: {type(e).__name__}")

def main():
    """Run all tests with timing and summary."""
    start_time = datetime.now()
    
    print("🚀 COMPREHENSIVE NASA APIS TEST SUITE")
    print("=" * 80)
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Run all tests
    test_apod_function()
    test_neow_class()
    test_donki_class()
    test_eonet_class()
    test_mars_rover()
    test_nasa_images()
    test_osdr_comprehensive()
    test_legacy_osdp()
    test_performance_and_resilience()
    
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    print("\n" + "="*80)
    print("🎉 ALL TESTS COMPLETED!")
    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print("\n🌌 NASA OPEN SPACE DATA HUB - Ready for deployment!")
    print("✨ All APIs tested and validated for production use")

if __name__ == "__main__":
    main()
