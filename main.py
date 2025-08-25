
import json
from api.exoplanets import get_exoplanet

def test_exoplanets_api():
    print("Testing NASA Exoplanet Archive API...")
    print("=" * 50)
    
    # Test 1: Basic query for confirmed planets
    print("\n1. Testing basic query for confirmed planets (pscomppars table):")
    try:
        result = get_exoplanet(
            table="pscomppars",
            select="pl_name,pl_rade,disc_year,st_teff",
            format="json"
        )
        if result:
            print(f"✅ Success! Retrieved {len(result)} exoplanets")
            if len(result) > 0:
                print(f"Sample planet: {result[0].get('pl_name', 'Unknown')}")
                print(f"Radius: {result[0].get('pl_rade', 'N/A')} Earth radii")
                print(f"Discovery year: {result[0].get('disc_year', 'N/A')}")
        else:
            print("❌ Failed to retrieve data")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Query with filters
    print("\n2. Testing query with filters (planets discovered after 2020):")
    try:
        result = get_exoplanet(
            table="pscomppars",
            select="pl_name,disc_year,pl_rade",
            where="disc_year>2020",
            order="disc_year desc",
            format="json"
        )
        if result:
            print(f"✅ Success! Found {len(result)} planets discovered after 2020")
            if len(result) > 0:
                for i, planet in enumerate(result[:3]):  # Show first 3
                    print(f"  {i+1}. {planet.get('pl_name', 'Unknown')} ({planet.get('disc_year', 'N/A')})")
        else:
            print("❌ No data or failed query")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Count query
    print("\n3. Testing count query:")
    try:
        result = get_exoplanet(
            table="pscomppars",
            select="count(*)",
            format="json"
        )
        if result:
            print(f"✅ Success! Total confirmed exoplanets: {result[0]['count(*)'] if result else 'Unknown'}")
        else:
            print("❌ Failed to get count")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Invalid table (should fail gracefully)
    print("\n4. Testing invalid table (error handling):")
    try:
        result = get_exoplanet(
            table="invalid_table",
            format="json"
        )
        if result is None:
            print("✅ Good! Function properly returned None for invalid table")
        else:
            print("⚠️ Unexpected: Function returned data for invalid table")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Testing complete!")

if __name__ == "__main__":
    test_exoplanets_api()
