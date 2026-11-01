import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.database import init_db, SessionLocal
from backend.app.core.location_service import LocationService

def test_locations():
    init_db()
    with SessionLocal() as s:
        states = LocationService.get_all_states(s)
        print(f"Total US States & Territories Seeded: {len(states)}")
        assert len(states) >= 50, "Expected at least 50 states"
        
        tx_cities = LocationService.search_cities(s, "TX", limit=10)
        print(f"Sample Texas Cities: {[c['city_name'] for c in tx_cities]}")
        assert len(tx_cities) > 0, "No TX cities found"

        ca_cities = LocationService.search_cities(s, "CA", limit=5)
        print(f"Sample California Cities: {[c['city_name'] for c in ca_cities]}")
        assert len(ca_cities) > 0

        # Haversine distance test: Houston to Austin (~146 miles)
        dist = LocationService.haversine_distance_miles(29.7604, -95.3698, 30.2672, -97.7431)
        print(f"Calculated Haversine distance Houston to Austin: {round(dist, 1)} miles")
        assert 135 <= dist <= 165, f"Expected ~146 miles, got {dist}"

        # Google Places 50km radius zone splitting test
        zones_25 = LocationService.generate_search_zones(29.7604, -95.3698, 25.0)
        print(f"25-mile request generated {len(zones_25)} zone(s)")
        assert len(zones_25) == 1

        zones_50 = LocationService.generate_search_zones(29.7604, -95.3698, 50.0)
        print(f"50-mile request generated {len(zones_50)} overlapping zones (bypassing Google 50km limit)")
        assert len(zones_50) == 5

    print("\n[SUCCESS] Location Service & Geospatial Seeding Verified!")

if __name__ == "__main__":
    test_locations()

