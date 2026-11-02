import pytest
from unittest.mock import MagicMock, patch
from backend.app.engine.discovery.google_places_discovery import GooglePlacesDiscoveryAdapter
from backend.app.engine.discovery.base import DiscoveredLead

def test_google_places_configuration():
    adapter_empty = GooglePlacesDiscoveryAdapter(api_key="")
    assert not adapter_empty.is_configured

    adapter_short = GooglePlacesDiscoveryAdapter(api_key="12345")
    assert not adapter_short.is_configured

    adapter_valid = GooglePlacesDiscoveryAdapter(api_key="AIzaSyA1234567890abcdef1234567890")
    assert adapter_valid.is_configured


def test_google_places_fetch_details():
    adapter = GooglePlacesDiscoveryAdapter(api_key="AIzaSyA1234567890abcdef1234567890")
    
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "formatted_phone_number": "(512) 555-0199",
            "website": "https://austintexproofers.com",
            "business_status": "OPERATIONAL",
            "formatted_address": "123 Congress Ave, Austin, TX 78701"
        }
    }
    mock_client.get.return_value = mock_resp

    details = adapter.fetch_place_details_sync(mock_client, "ChIJN1t_tDeuEmsRUsoyG83frY4")
    assert details["formatted_phone_number"] == "(512) 555-0199"
    assert details["website"] == "https://austintexproofers.com"
    assert details["business_status"] == "OPERATIONAL"
    
    # Verify exact field masking was used to minimize Google Cloud billing
    mock_client.get.assert_called_once()
    called_params = mock_client.get.call_args[1]["params"]
    assert "formatted_phone_number" in called_params["fields"]
    assert "website" in called_params["fields"]
    assert "business_status" in called_params["fields"]


def test_google_places_deduplication_and_closed_filter():
    adapter = GooglePlacesDiscoveryAdapter(api_key="AIzaSyA1234567890abcdef1234567890")

    # Sample responses: 1 operational place, 1 closed place, 1 duplicate place
    sample_textsearch_data = {
        "results": [
            {
                "place_id": "place_001",
                "name": "Apex Roofing Pros",
                "business_status": "OPERATIONAL",
                "formatted_address": "100 Main St, Austin, TX",
                "geometry": {"location": {"lat": 30.2672, "lng": -97.7431}},
                "rating": 4.8,
                "user_ratings_total": 95
            },
            {
                "place_id": "place_002_closed",
                "name": "Defunct Roofers Inc",
                "business_status": "CLOSED_PERMANENTLY",
                "formatted_address": "200 Abandoned Rd, Austin, TX",
                "geometry": {"location": {"lat": 30.2672, "lng": -97.7431}}
            },
            {
                "place_id": "place_001", # Duplicate of place_001 in overlapping zone
                "name": "Apex Roofing Pros",
                "business_status": "OPERATIONAL",
                "formatted_address": "100 Main St, Austin, TX",
                "geometry": {"location": {"lat": 30.2672, "lng": -97.7431}}
            }
        ],
        "next_page_token": None
    }

    mock_details_data = {
        "result": {
            "formatted_phone_number": "(512) 555-7788",
            "website": "https://apexroofingpros.com",
            "business_status": "OPERATIONAL",
            "formatted_address": "100 Main St, Suite 200, Austin, TX 78701"
        }
    }

    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value.__enter__.return_value
        
        def mock_get(url, params=None, timeout=None):
            resp = MagicMock()
            resp.status_code = 200
            if "textsearch" in url:
                resp.json.return_value = sample_textsearch_data
            elif "details" in url:
                resp.json.return_value = mock_details_data
            return resp

        mock_client.get.side_effect = mock_get

        leads = adapter.discover_sync(
            industry="Roofing Contractors",
            trade="Roofing",
            city="Austin",
            state="TX",
            center_lat=30.2672,
            center_lon=-97.7431,
            radius_miles=25.0,
            limit=10
        )

        # Out of 3 places:
        # place_001 is accepted (operational, new)
        # place_002_closed is rejected (CLOSED_PERMANENTLY)
        # place_001 duplicate is rejected (seen_place_ids)
        assert len(leads) == 1

        lead = leads[0]
        assert lead.name == "Apex Roofing Pros"
        assert lead.provider_place_id == "place_001"
        assert lead.phone == "(512) 555-7788"
        assert lead.website == "https://apexroofingpros.com"
        assert lead.rating == 4.8
        assert lead.reviews_count == 95
        assert lead.address == "100 Main St, Suite 200, Austin, TX 78701"
        assert lead.provider == "Google Places API"
