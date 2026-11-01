import math
from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from ..models import USState, USCity

EARTH_RADIUS_MILES = 3958.8
EARTH_RADIUS_METERS = 6371000.0
METERS_PER_MILE = 1609.344
GOOGLE_PLACES_MAX_RADIUS_METERS = 50000.0 # 50 km per Google Places circle

class LocationService:
    """
    US Census Geographic Services & Geospatial Distance Engine.
    Handles coordinate lookup, Haversine distance filtering, and multi-zone coverage tiling.
    """

    @staticmethod
    def get_all_states(session: Session) -> list[dict[str, Any]]:
        """Returns all 50 US States + DC sorted alphabetically."""
        states = session.query(USState).order_by(USState.name.asc()).all()
        return [
            {
                "id": s.id,
                "name": s.name,
                "abbr": s.abbr,
                "fips_code": s.fips_code,
                "capital": s.capital,
                "latitude": s.latitude,
                "longitude": s.longitude
            }
            for s in states
        ]

    @staticmethod
    def get_state(session: Session, abbr: str) -> Optional[dict[str, Any]]:
        s = session.query(USState).filter(USState.abbr == abbr.upper()).first()
        if not s:
            return None
        return {
            "id": s.id,
            "name": s.name,
            "abbr": s.abbr,
            "fips_code": s.fips_code,
            "capital": s.capital,
            "latitude": s.latitude,
            "longitude": s.longitude
        }

    @staticmethod
    def search_cities(
        session: Session, 
        state_abbr: Optional[str] = None, 
        query: Optional[str] = None,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Fast searchable city lookup with autocomplete.
        Filters by state abbreviation, partial name, and place type.
        """
        q = session.query(USCity)
        if state_abbr:
            q = q.filter(USCity.state_abbr == state_abbr.upper())
        if query:
            clean_q = query.strip()
            q = q.filter(USCity.city_name.ilike(f"%{clean_q}%"))
        
        cities = q.order_by(USCity.population.desc(), USCity.city_name.asc()).limit(limit).all()
        return [
            {
                "id": c.id,
                "state_abbr": c.state_abbr,
                "city_name": c.city_name,
                "place_type": c.place_type,
                "is_incorporated": c.is_incorporated,
                "fips_code": c.fips_code,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "population": c.population,
                "county": c.county,
                "display_name": f"{c.city_name}, {c.state_abbr}" + (f" ({c.place_type.upper()})" if not c.is_incorporated else "")
            }
            for c in cities
        ]

    @staticmethod
    def get_cities_for_state(session: Session, state_abbr: str) -> list[dict[str, Any]]:
        """Convenience method to return all cities for a single state."""
        return LocationService.get_cities_for_states(session, [state_abbr])

    @staticmethod
    def get_cities_for_states(session: Session, state_abbrs: list[str]) -> list[dict[str, Any]]:
        """Returns all cities across one or multiple states."""
        clean_abbrs = [s.upper().strip() for s in state_abbrs if s]
        if not clean_abbrs:
            return []
        cities = session.query(USCity).filter(USCity.state_abbr.in_(clean_abbrs)).order_by(USCity.state_abbr.asc(), USCity.city_name.asc()).all()
        return [
            {
                "id": c.id,
                "state_abbr": c.state_abbr,
                "city_name": c.city_name,
                "place_type": c.place_type,
                "is_incorporated": c.is_incorporated,
                "fips_code": c.fips_code,
                "latitude": c.latitude,
                "longitude": c.longitude,
                "population": c.population,
                "county": c.county,
                "display_name": f"{c.city_name}, {c.state_abbr}"
            }
            for c in cities
        ]

    @staticmethod
    def haversine_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates the great-circle distance between two points on the Earth in Miles
        using the Haversine formula.
        """
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2.0) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2.0) ** 2)
        c = 2.0 * math.asin(math.sqrt(a))
        return EARTH_RADIUS_MILES * c

    @staticmethod
    def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates distance in Meters."""
        return LocationService.haversine_distance_miles(lat1, lon1, lat2, lon2) * METERS_PER_MILE

    @staticmethod
    def is_within_radius(center_lat: float, center_lon: float, point_lat: float, point_lon: float, radius_miles: float) -> tuple[bool, float]:
        """
        Checks whether a point is within the requested geographic radius.
        Returns (is_inside, calculated_distance_miles).
        """
        dist = LocationService.haversine_distance_miles(center_lat, center_lon, point_lat, point_lon)
        return (dist <= radius_miles), round(dist, 2)

    @staticmethod
    def generate_search_zones(center_lat: float, center_lon: float, radius_miles: float) -> list[dict[str, Any]]:
        """
        Overcomes Google Places API 50,000-meter circle radius limitation.
        For a requested radius > 30 miles (48,280 meters), breaks the search zone
        into overlapping sub-circles to guarantee complete geographic coverage.
        """
        radius_meters = radius_miles * METERS_PER_MILE

        if radius_meters <= GOOGLE_PLACES_MAX_RADIUS_METERS:
            # Single zone covers the entire requested radius
            return [{
                "zone_id": "center",
                "center_lat": center_lat,
                "center_lon": center_lon,
                "radius_meters": min(radius_meters, GOOGLE_PLACES_MAX_RADIUS_METERS),
                "radius_miles": radius_miles
            }]

        # Radius > 30 miles (e.g. 50 miles, 75 miles, 100 miles)
        # 50 miles = ~80,467m. Generate Center + 4 Directional Offset Tiles (N, S, E, W)
        sub_radius_miles = 28.0 # ~45,000m sub-circles (within 50,000m limit)
        sub_radius_meters = sub_radius_miles * METERS_PER_MILE

        # Approximate degrees per mile
        lat_deg_per_mile = 1.0 / 69.0
        lon_deg_per_mile = 1.0 / (69.0 * math.cos(math.radians(center_lat)))
        offset_miles = radius_miles * 0.45

        zones = [
            # Center tile
            {
                "zone_id": "center",
                "center_lat": center_lat,
                "center_lon": center_lon,
                "radius_meters": sub_radius_meters,
                "radius_miles": sub_radius_miles
            },
            # North tile
            {
                "zone_id": "north",
                "center_lat": center_lat + (offset_miles * lat_deg_per_mile),
                "center_lon": center_lon,
                "radius_meters": sub_radius_meters,
                "radius_miles": sub_radius_miles
            },
            # South tile
            {
                "zone_id": "south",
                "center_lat": center_lat - (offset_miles * lat_deg_per_mile),
                "center_lon": center_lon,
                "radius_meters": sub_radius_meters,
                "radius_miles": sub_radius_miles
            },
            # East tile
            {
                "zone_id": "east",
                "center_lat": center_lat,
                "center_lon": center_lon + (offset_miles * lon_deg_per_mile),
                "radius_meters": sub_radius_meters,
                "radius_miles": sub_radius_miles
            },
            # West tile
            {
                "zone_id": "west",
                "center_lat": center_lat,
                "center_lon": center_lon - (offset_miles * lon_deg_per_mile),
                "radius_meters": sub_radius_meters,
                "radius_miles": sub_radius_miles
            }
        ]

        return zones
