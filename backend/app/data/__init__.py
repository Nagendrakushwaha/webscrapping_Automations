"""
Compatibility proxy for seed_us_locations. Canonical source is backend.app.seeds.
"""
from ..seeds.us_locations_seed import seed_us_locations, US_STATES, TEXAS_KEY_CITIES

__all__ = ["seed_us_locations", "US_STATES", "TEXAS_KEY_CITIES"]
