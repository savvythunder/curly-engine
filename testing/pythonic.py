
from api.iss import (
    get_iss_position, 
    get_iss_tle, 
    satellites, 
    get_coordinates_info,
    is_iss_overhead,
    ISS_ID
)
import time

def test_iss_api():
    print("Testing Enhanced ISS API...")
    print("=" * 50)
    
    # Test 1: Get current ISS position
    print(f"\n1. Testing current ISS position (ID: {ISS_ID}):")
    try:
        position = get_iss_position(units="kilometers")
        if position:
            print(f"✅ Success! ISS is currently at:")
            print(f"   Latitude: {position['latitude']:.2f}°")
            print(f"   Longitude: {position['longitude']:.2f}°")
            print(f"   Altitude: {position['altitude']:.2f} km")
            print(f"   Velocity: {position['velocity']:.2f} km/h")
            print(f"   Visibility: {position['visibility']}")
        else:
            print("❌ Failed to get ISS position")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get ISS TLE data
    print(f"\n2. Testing ISS TLE data:")
    try:
        tle_data = get_iss_tle()
        if tle_data:
            print(f"✅ Success! TLE data retrieved:")
            print(f"   Satellite: {tle_data['name']}")
            print(f"   TLE Timestamp: {tle_data['tle_timestamp']}")
            print(f"   Line 1: {tle_data['line1'][:50]}...")
        else:
            print("❌ Failed to get TLE data")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Check if ISS is overhead (example location: London)
    print(f"\n3. Testing ISS overhead check (London: 51.5074, -0.1278):")
    try:
        london_lat, london_lon = 51.5074, -0.1278
        overhead = is_iss_overhead(london_lat, london_lon)
        if overhead:
            print("✅ ISS is overhead London!")
        else:
            print("✅ ISS is not currently overhead London")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get coordinate information
    print(f"\n4. Testing coordinate information for ISS current position:")
    try:
        position = get_iss_position()
        if position:
            coord_info = get_coordinates_info(position['latitude'], position['longitude'])
            if coord_info:
                print(f"✅ Success! ISS is currently over:")
                print(f"   Country: {coord_info.get('country_code', 'Unknown')}")
                print(f"   Timezone: {coord_info.get('timezone_id', 'Unknown')}")
            else:
                print("❌ Failed to get coordinate info")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: List all available satellites
    print(f"\n5. Testing satellites list:")
    try:
        sats = satellites()
        if sats:
            print(f"✅ Success! Available satellites:")
            for sat in sats:
                print(f"   {sat['name']} (ID: {sat['id']})")
        else:
            print("❌ Failed to get satellites list")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("ISS API testing complete!")

if __name__ == "__main__":
    test_iss_api()
