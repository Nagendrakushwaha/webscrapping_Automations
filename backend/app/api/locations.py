from typing import Optional, Union
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
    states = LocationService.get_all_states(db)
    return {"states": states, "total": len(states)}

@router.get("/cities")
def search_cities(
    state: Optional[str] = Query(None, description="State abbreviation e.g. TX, CA"),
    q: Optional[str] = Query(None, description="Partial city name search query"),
    limit: int = Query(250, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Fast searchable US cities and Census-designated places (CDPs) with autocomplete.
    """
    cities = LocationService.search_cities(db, state_abbr=state, query=q, limit=limit)
    return {"cities": cities, "total": len(cities)}

@router.get("/cities/multi")
@router.get("/cities-by-states")
def get_cities_by_states(
    states: Optional[list[str]] = Query(None, description="State abbreviations e.g. ?states=TX&states=CA or ?states=TX,CA"),
    limit: int = Query(500, ge=1, le=2000),
    db: Session = Depends(get_db)
):
    """
    Returns incorporated cities and places across one or multiple US states.
    Accepts repeated ?states=TX&states=CA or comma-separated ?states=TX,CA.
    """
    parsed_states = []
    if states:
        for item in states:
            parsed_states.extend([s.strip().upper() for s in item.split(",") if s.strip()])
    
    if not parsed_states:
        parsed_states = ["TX"] # Default fallback
        
    cities = LocationService.get_cities_for_states(db, parsed_states)
    return {"cities": cities[:limit], "total": len(cities)}

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
