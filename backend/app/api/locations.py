from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..core.location_service import LocationService

router = APIRouter(prefix="/api/locations", tags=["Locations"])

@router.get("/states")
def get_all_states(db: Session = Depends(get_db)):
    """
    Returns all 50 US States + District of Columbia with official Census FIPS codes and capitals.
    """
    return LocationService.get_all_states(db)

@router.get("/cities")
def search_cities(
    state: Optional[str] = Query(None, description="State abbreviation e.g. TX, CA"),
    q: Optional[str] = Query(None, description="Partial city name search query"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Fast searchable US cities and Census-designated places (CDPs) with autocomplete.
    """
    return LocationService.search_cities(db, state_abbr=state, query=q, limit=limit)

@router.get("/cities-by-states")
def get_cities_by_states(
    states: str = Query(..., description="Comma-separated state abbreviations e.g. TX,CA,FL"),
    db: Session = Depends(get_db)
):
    """
    Returns incorporated cities and places across one or multiple US states.
    """
    state_list = [s.strip().upper() for s in states.split(",") if s.strip()]
    return LocationService.get_cities_for_states(db, state_list)

@router.post("/distance")
def calculate_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
):
    """
    Calculates great-circle Haversine distance between two coordinates in Miles and Meters.
    """
    miles = LocationService.haversine_distance_miles(lat1, lon1, lat2, lon2)
    meters = LocationService.haversine_distance_meters(lat1, lon1, lat2, lon2)
    return {
        "distance_miles": round(miles, 2),
        "distance_meters": round(meters, 1)
    }
