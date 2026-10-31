"""
US Census Bureau Geographic Dataset & Seeder.
Provides all 50 US States + District of Columbia and comprehensive cities, incorporated places, and CDPs
with official FIPS codes, place types, and geographic latitude/longitude coordinates.
"""

from typing import Any
from sqlalchemy.orm import Session
from ..models import USState, USCity

# Complete 50 US States + DC with official Census FIPS codes and representative coordinates
US_STATES_DATA = [
    {"abbr": "AL", "name": "Alabama", "fips_code": "01", "capital": "Montgomery", "latitude": 32.7794, "longitude": -86.8287},
    {"abbr": "AK", "name": "Alaska", "fips_code": "02", "capital": "Juneau", "latitude": 64.0685, "longitude": -152.2782},
    {"abbr": "AZ", "name": "Arizona", "fips_code": "04", "capital": "Phoenix", "latitude": 34.2744, "longitude": -111.6602},
    {"abbr": "AR", "name": "Arkansas", "fips_code": "05", "capital": "Little Rock", "latitude": 34.8938, "longitude": -92.4426},
    {"abbr": "CA", "name": "California", "fips_code": "06", "capital": "Sacramento", "latitude": 36.7783, "longitude": -119.4179},
    {"abbr": "CO", "name": "Colorado", "fips_code": "08", "capital": "Denver", "latitude": 39.5501, "longitude": -105.7821},
    {"abbr": "CT", "name": "Connecticut", "fips_code": "09", "capital": "Hartford", "latitude": 41.6032, "longitude": -73.0877},
    {"abbr": "DE", "name": "Delaware", "fips_code": "10", "capital": "Dover", "latitude": 38.9108, "longitude": -75.5277},
    {"abbr": "FL", "name": "Florida", "fips_code": "12", "capital": "Tallahassee", "latitude": 27.6648, "longitude": -81.5158},
    {"abbr": "GA", "name": "Georgia", "fips_code": "13", "capital": "Atlanta", "latitude": 32.1656, "longitude": -82.9001},
    {"abbr": "HI", "name": "Hawaii", "fips_code": "15", "capital": "Honolulu", "latitude": 19.8968, "longitude": -155.5828},
    {"abbr": "ID", "name": "Idaho", "fips_code": "16", "capital": "Boise", "latitude": 44.0682, "longitude": -114.7420},
    {"abbr": "IL", "name": "Illinois", "fips_code": "17", "capital": "Springfield", "latitude": 40.6331, "longitude": -89.3985},
    {"abbr": "IN", "name": "Indiana", "fips_code": "18", "capital": "Indianapolis", "latitude": 40.2672, "longitude": -86.1349},
    {"abbr": "IA", "name": "Iowa", "fips_code": "19", "capital": "Des Moines", "latitude": 41.8780, "longitude": -93.0977},
    {"abbr": "KS", "name": "Kansas", "fips_code": "20", "capital": "Topeka", "latitude": 39.0119, "longitude": -98.4842},
    {"abbr": "KY", "name": "Kentucky", "fips_code": "21", "capital": "Frankfort", "latitude": 37.8393, "longitude": -84.2700},
    {"abbr": "LA", "name": "Louisiana", "fips_code": "22", "capital": "Baton Rouge", "latitude": 30.9843, "longitude": -91.9623},
    {"abbr": "ME", "name": "Maine", "fips_code": "23", "capital": "Augusta", "latitude": 45.2538, "longitude": -69.4455},
    {"abbr": "MD", "name": "Maryland", "fips_code": "24", "capital": "Annapolis", "latitude": 39.0458, "longitude": -76.6413},
    {"abbr": "MA", "name": "Massachusetts", "fips_code": "25", "capital": "Boston", "latitude": 42.4072, "longitude": -71.3824},
    {"abbr": "MI", "name": "Michigan", "fips_code": "26", "capital": "Lansing", "latitude": 44.3148, "longitude": -85.6024},
    {"abbr": "MN", "name": "Minnesota", "fips_code": "27", "capital": "Saint Paul", "latitude": 46.7296, "longitude": -94.6859},
    {"abbr": "MS", "name": "Mississippi", "fips_code": "28", "capital": "Jackson", "latitude": 32.3547, "longitude": -89.3985},
    {"abbr": "MO", "name": "Missouri", "fips_code": "29", "capital": "Jefferson City", "latitude": 37.9643, "longitude": -91.8318},
    {"abbr": "MT", "name": "Montana", "fips_code": "30", "capital": "Helena", "latitude": 46.8797, "longitude": -110.3626},
    {"abbr": "NE", "name": "Nebraska", "fips_code": "31", "capital": "Lincoln", "latitude": 41.4925, "longitude": -99.9018},
    {"abbr": "NV", "name": "Nevada", "fips_code": "32", "capital": "Carson City", "latitude": 38.8026, "longitude": -116.4194},
    {"abbr": "NH", "name": "New Hampshire", "fips_code": "33", "capital": "Concord", "latitude": 43.1939, "longitude": -71.5724},
    {"abbr": "NJ", "name": "New Jersey", "fips_code": "34", "capital": "Trenton", "latitude": 40.0583, "longitude": -74.4057},
    {"abbr": "NM", "name": "New Mexico", "fips_code": "35", "capital": "Santa Fe", "latitude": 34.5199, "longitude": -105.8701},
    {"abbr": "NY", "name": "New York", "fips_code": "36", "capital": "Albany", "latitude": 43.2994, "longitude": -74.2179},
    {"abbr": "NC", "name": "North Carolina", "fips_code": "37", "capital": "Raleigh", "latitude": 35.7596, "longitude": -79.0193},
    {"abbr": "ND", "name": "North Dakota", "fips_code": "38", "capital": "Bismarck", "latitude": 47.5515, "longitude": -101.0020},
    {"abbr": "OH", "name": "Ohio", "fips_code": "39", "capital": "Columbus", "latitude": 40.4173, "longitude": -82.9071},
    {"abbr": "OK", "name": "Oklahoma", "fips_code": "40", "capital": "Oklahoma City", "latitude": 35.0078, "longitude": -97.0929},
    {"abbr": "OR", "name": "Oregon", "fips_code": "41", "capital": "Salem", "latitude": 43.8041, "longitude": -120.5542},
    {"abbr": "PA", "name": "Pennsylvania", "fips_code": "42", "capital": "Harrisburg", "latitude": 41.2033, "longitude": -77.1945},
    {"abbr": "RI", "name": "Rhode Island", "fips_code": "44", "capital": "Providence", "latitude": 41.5801, "longitude": -71.4774},
    {"abbr": "SC", "name": "South Carolina", "fips_code": "45", "capital": "Columbia", "latitude": 33.8361, "longitude": -81.1637},
    {"abbr": "SD", "name": "South Dakota", "fips_code": "46", "capital": "Pierre", "latitude": 43.9695, "longitude": -99.9018},
    {"abbr": "TN", "name": "Tennessee", "fips_code": "47", "capital": "Nashville", "latitude": 35.5175, "longitude": -86.5804},
    {"abbr": "TX", "name": "Texas", "fips_code": "48", "capital": "Austin", "latitude": 31.9686, "longitude": -99.9018},
    {"abbr": "UT", "name": "Utah", "fips_code": "49", "capital": "Salt Lake City", "latitude": 39.3210, "longitude": -111.0937},
    {"abbr": "VT", "name": "Vermont", "fips_code": "50", "capital": "Montpelier", "latitude": 44.5588, "longitude": -72.5778},
    {"abbr": "VA", "name": "Virginia", "fips_code": "51", "capital": "Richmond", "latitude": 37.4316, "longitude": -78.6569},
    {"abbr": "WA", "name": "Washington", "fips_code": "53", "capital": "Olympia", "latitude": 47.7511, "longitude": -120.7401},
    {"abbr": "WV", "name": "West Virginia", "fips_code": "54", "capital": "Charleston", "latitude": 38.5976, "longitude": -80.4549},
    {"abbr": "WI", "name": "Wisconsin", "fips_code": "55", "capital": "Madison", "latitude": 43.7844, "longitude": -88.7879},
    {"abbr": "WY", "name": "Wyoming", "fips_code": "56", "capital": "Cheyenne", "latitude": 43.0760, "longitude": -107.2903},
    {"abbr": "DC", "name": "District of Columbia", "fips_code": "11", "capital": "Washington", "latitude": 38.9072, "longitude": -77.0369}
]

# Comprehensive City, Incorporated Place & CDP database across ALL 50 states + DC
# Each record contains official Census coordinates, place type, incorporation status, and FIPS
US_CITIES_DATA = [
    # --- TEXAS (TX) ---
    {"state": "TX", "city": "Houston", "type": "city", "inc": True, "fips": "4835000", "lat": 29.7604, "lon": -95.3698, "pop": 2304580, "county": "Harris"},
    {"state": "TX", "city": "Dallas", "type": "city", "inc": True, "fips": "4819000", "lat": 32.7767, "lon": -96.7970, "pop": 1304379, "county": "Dallas"},
    {"state": "TX", "city": "Austin", "type": "city", "inc": True, "fips": "4805000", "lat": 30.2672, "lon": -97.7431, "pop": 961855, "county": "Travis"},
    {"state": "TX", "city": "San Antonio", "type": "city", "inc": True, "fips": "4865000", "lat": 29.4241, "lon": -98.4936, "pop": 1434625, "county": "Bexar"},
    {"state": "TX", "city": "Fort Worth", "type": "city", "inc": True, "fips": "4827000", "lat": 32.7555, "lon": -97.3308, "pop": 918915, "county": "Tarrant"},
    {"state": "TX", "city": "El Paso", "type": "city", "inc": True, "fips": "4824000", "lat": 31.7619, "lon": -106.4850, "pop": 678815, "county": "El Paso"},
    {"state": "TX", "city": "Arlington", "type": "city", "inc": True, "fips": "4804000", "lat": 32.7357, "lon": -97.1081, "pop": 394266, "county": "Tarrant"},
    {"state": "TX", "city": "Corpus Christi", "type": "city", "inc": True, "fips": "4817000", "lat": 27.8006, "lon": -97.3964, "pop": 317863, "county": "Nueces"},
    {"state": "TX", "city": "Plano", "type": "city", "inc": True, "fips": "4858016", "lat": 33.0198, "lon": -96.6989, "pop": 285494, "county": "Collin"},
    {"state": "TX", "city": "Lubbock", "type": "city", "inc": True, "fips": "4845000", "lat": 33.5779, "lon": -101.8552, "pop": 257141, "county": "Lubbock"},
    {"state": "TX", "city": "Irving", "type": "city", "inc": True, "fips": "4837000", "lat": 32.8140, "lon": -96.9489, "pop": 256684, "county": "Dallas"},
    {"state": "TX", "city": "Laredo", "type": "city", "inc": True, "fips": "4841464", "lat": 27.5036, "lon": -99.5076, "pop": 255205, "county": "Webb"},
    {"state": "TX", "city": "Garland", "type": "city", "inc": True, "fips": "4829000", "lat": 32.9126, "lon": -96.6389, "pop": 246018, "county": "Dallas"},
    {"state": "TX", "city": "Frisco", "type": "city", "inc": True, "fips": "4827684", "lat": 33.1507, "lon": -96.8236, "pop": 200509, "county": "Collin"},
    {"state": "TX", "city": "McKinney", "type": "city", "inc": True, "fips": "4845744", "lat": 33.1972, "lon": -96.6397, "pop": 195308, "county": "Collin"},
    {"state": "TX", "city": "Round Rock", "type": "city", "inc": True, "fips": "4863500", "lat": 30.5083, "lon": -97.6789, "pop": 119468, "county": "Williamson"},
    {"state": "TX", "city": "The Woodlands", "type": "CDP", "inc": False, "fips": "4872656", "lat": 30.1658, "lon": -95.4613, "pop": 118402, "county": "Montgomery"},
    {"state": "TX", "city": "Sugar Land", "type": "city", "inc": True, "fips": "4870808", "lat": 29.6197, "lon": -95.6349, "pop": 111026, "county": "Fort Bend"},
    {"state": "TX", "city": "Pearland", "type": "city", "inc": True, "fips": "4856348", "lat": 29.5636, "lon": -95.2860, "pop": 125828, "county": "Brazoria"},
    {"state": "TX", "city": "Waco", "type": "city", "inc": True, "fips": "4876000", "lat": 31.5493, "lon": -97.1467, "pop": 138486, "county": "McLennan"},
    {"state": "TX", "city": "Denton", "type": "city", "inc": True, "fips": "4819972", "lat": 33.2148, "lon": -97.1331, "pop": 139869, "county": "Denton"},
    {"state": "TX", "city": "Midland", "type": "city", "inc": True, "fips": "4848072", "lat": 31.9973, "lon": -102.0779, "pop": 132524, "county": "Midland"},
    {"state": "TX", "city": "Odessa", "type": "city", "inc": True, "fips": "4853388", "lat": 31.8457, "lon": -102.3676, "pop": 114428, "county": "Ector"},
    {"state": "TX", "city": "Beaumont", "type": "city", "inc": True, "fips": "4807000", "lat": 30.0802, "lon": -94.1266, "pop": 115282, "county": "Jefferson"},
    {"state": "TX", "city": "College Station", "type": "city", "inc": True, "fips": "4815976", "lat": 30.6280, "lon": -96.3344, "pop": 120511, "county": "Brazos"},
    {"state": "TX", "city": "Tyler", "type": "city", "inc": True, "fips": "4874144", "lat": 32.3513, "lon": -95.3011, "pop": 105995, "county": "Smith"},

    # --- CALIFORNIA (CA) ---
    {"state": "CA", "city": "Los Angeles", "type": "city", "inc": True, "fips": "0644000", "lat": 34.0522, "lon": -118.2437, "pop": 3898747, "county": "Los Angeles"},
    {"state": "CA", "city": "San Diego", "type": "city", "inc": True, "fips": "0666000", "lat": 32.7157, "lon": -117.1611, "pop": 1386932, "county": "San Diego"},
    {"state": "CA", "city": "San Jose", "type": "city", "inc": True, "fips": "0668000", "lat": 37.3382, "lon": -121.8863, "pop": 1013240, "county": "Santa Clara"},
    {"state": "CA", "city": "San Francisco", "type": "city", "inc": True, "fips": "0667000", "lat": 37.7749, "lon": -122.4194, "pop": 873965, "county": "San Francisco"},
    {"state": "CA", "city": "Fresno", "type": "city", "inc": True, "fips": "0627000", "lat": 36.7468, "lon": -119.7726, "pop": 542107, "county": "Fresno"},
    {"state": "CA", "city": "Sacramento", "type": "city", "inc": True, "fips": "0664000", "lat": 38.5816, "lon": -121.4944, "pop": 524943, "county": "Sacramento"},
    {"state": "CA", "city": "Long Beach", "type": "city", "inc": True, "fips": "0643000", "lat": 33.7701, "lon": -118.1937, "pop": 466742, "county": "Los Angeles"},
    {"state": "CA", "city": "Oakland", "type": "city", "inc": True, "fips": "0653000", "lat": 37.8044, "lon": -122.2712, "pop": 440646, "county": "Alameda"},
    {"state": "CA", "city": "Bakersfield", "type": "city", "inc": True, "fips": "0603526", "lat": 35.3733, "lon": -119.0187, "pop": 403455, "county": "Kern"},
    {"state": "CA", "city": "Anaheim", "type": "city", "inc": True, "fips": "0602000", "lat": 33.8366, "lon": -117.9143, "pop": 346824, "county": "Orange"},
    {"state": "CA", "city": "Santa Ana", "type": "city", "inc": True, "fips": "0669000", "lat": 33.7455, "lon": -117.8677, "pop": 310227, "county": "Orange"},
    {"state": "CA", "city": "Riverside", "type": "city", "inc": True, "fips": "0662000", "lat": 33.9806, "lon": -117.3755, "pop": 314998, "county": "Riverside"},
    {"state": "CA", "city": "Irvine", "type": "city", "inc": True, "fips": "0636770", "lat": 33.6846, "lon": -117.8265, "pop": 307670, "county": "Orange"},
    {"state": "CA", "city": "Stockton", "type": "city", "inc": True, "fips": "0675000", "lat": 37.9577, "lon": -121.2908, "pop": 320804, "county": "San Joaquin"},

    # --- FLORIDA (FL) ---
    {"state": "FL", "city": "Jacksonville", "type": "city", "inc": True, "fips": "1235000", "lat": 30.3322, "lon": -81.6557, "pop": 949611, "county": "Duval"},
    {"state": "FL", "city": "Miami", "type": "city", "inc": True, "fips": "1245000", "lat": 25.7617, "lon": -80.1918, "pop": 442241, "county": "Miami-Dade"},
    {"state": "FL", "city": "Tampa", "type": "city", "inc": True, "fips": "1271000", "lat": 27.9506, "lon": -82.4572, "pop": 384959, "county": "Hillsborough"},
    {"state": "FL", "city": "Orlando", "type": "city", "inc": True, "fips": "1253000", "lat": 28.5383, "lon": -81.3792, "pop": 307573, "county": "Orange"},
    {"state": "FL", "city": "St. Petersburg", "type": "city", "inc": True, "fips": "1263000", "lat": 27.7676, "lon": -82.6403, "pop": 258308, "county": "Pinellas"},
    {"state": "FL", "city": "Hialeah", "type": "city", "inc": True, "fips": "1230000", "lat": 25.8576, "lon": -80.2781, "pop": 223109, "county": "Miami-Dade"},
    {"state": "FL", "city": "Fort Lauderdale", "type": "city", "inc": True, "fips": "1224000", "lat": 26.1224, "lon": -80.1373, "pop": 182760, "county": "Broward"},
    {"state": "FL", "city": "Tallahassee", "type": "city", "inc": True, "fips": "1270600", "lat": 30.4383, "lon": -84.2807, "pop": 196169, "county": "Leon"},
    {"state": "FL", "city": "Cape Coral", "type": "city", "inc": True, "fips": "1210275", "lat": 26.5629, "lon": -81.9495, "pop": 194016, "county": "Lee"},
    {"state": "FL", "city": "Pembroke Pines", "type": "city", "inc": True, "fips": "1255775", "lat": 26.0078, "lon": -80.2963, "pop": 171178, "county": "Broward"},
    {"state": "FL", "city": "Sarasota", "type": "city", "inc": True, "fips": "1264175", "lat": 27.3364, "lon": -82.5307, "pop": 54842, "county": "Sarasota"},
    {"state": "FL", "city": "Naples", "type": "city", "inc": True, "fips": "1247625", "lat": 26.1420, "lon": -81.7948, "pop": 19115, "county": "Collier"},

    # --- NEW YORK (NY) ---
    {"state": "NY", "city": "New York", "type": "city", "inc": True, "fips": "3651000", "lat": 40.7128, "lon": -74.0060, "pop": 8804190, "county": "New York"},
    {"state": "NY", "city": "Buffalo", "type": "city", "inc": True, "fips": "3611000", "lat": 42.8864, "lon": -78.8784, "pop": 278349, "county": "Erie"},
    {"state": "NY", "city": "Rochester", "type": "city", "inc": True, "fips": "3663000", "lat": 43.1566, "lon": -77.6088, "pop": 211328, "county": "Monroe"},
    {"state": "NY", "city": "Yonkers", "type": "city", "inc": True, "fips": "3684000", "lat": 40.9312, "lon": -73.8987, "pop": 211569, "county": "Westchester"},
    {"state": "NY", "city": "Syracuse", "type": "city", "inc": True, "fips": "3673000", "lat": 43.0481, "lon": -76.1474, "pop": 148620, "county": "Onondaga"},
    {"state": "NY", "city": "Albany", "type": "city", "inc": True, "fips": "3601000", "lat": 42.6526, "lon": -73.7562, "pop": 99224, "county": "Albany"},

    # --- ILLINOIS (IL) ---
    {"state": "IL", "city": "Chicago", "type": "city", "inc": True, "fips": "1714000", "lat": 41.8781, "lon": -87.6298, "pop": 2746388, "county": "Cook"},
    {"state": "IL", "city": "Aurora", "type": "city", "inc": True, "fips": "1703012", "lat": 41.7606, "lon": -88.3201, "pop": 180542, "county": "Kane"},
    {"state": "IL", "city": "Naperville", "type": "city", "inc": True, "fips": "1751622", "lat": 41.7508, "lon": -88.1535, "pop": 149540, "county": "DuPage"},
    {"state": "IL", "city": "Joliet", "type": "city", "inc": True, "fips": "1738570", "lat": 41.5250, "lon": -88.0817, "pop": 150362, "county": "Will"},
    {"state": "IL", "city": "Rockford", "type": "city", "inc": True, "fips": "1765000", "lat": 42.2711, "lon": -89.0940, "pop": 148655, "county": "Winnebago"},
    {"state": "IL", "city": "Springfield", "type": "city", "inc": True, "fips": "1772000", "lat": 39.7817, "lon": -89.6501, "pop": 114394, "county": "Sangamon"},

    # --- GEORGIA (GA) ---
    {"state": "GA", "city": "Atlanta", "type": "city", "inc": True, "fips": "1304000", "lat": 33.7490, "lon": -84.3880, "pop": 498715, "county": "Fulton"},
    {"state": "GA", "city": "Columbus", "type": "city", "inc": True, "fips": "1319000", "lat": 32.4610, "lon": -84.9877, "pop": 206922, "county": "Muscogee"},
    {"state": "GA", "city": "Augusta", "type": "city", "inc": True, "fips": "1304204", "lat": 33.4735, "lon": -82.0105, "pop": 202081, "county": "Richmond"},
    {"state": "GA", "city": "Macon", "type": "city", "inc": True, "fips": "1349000", "lat": 32.8407, "lon": -83.6324, "pop": 157346, "county": "Bibb"},
    {"state": "GA", "city": "Savannah", "type": "city", "inc": True, "fips": "1369000", "lat": 32.0809, "lon": -81.0912, "pop": 147780, "county": "Chatham"},
    {"state": "GA", "city": "Athens", "type": "city", "inc": True, "fips": "1303436", "lat": 33.9519, "lon": -83.3576, "pop": 127315, "county": "Clarke"},

    # --- NORTH CAROLINA (NC) ---
    {"state": "NC", "city": "Charlotte", "type": "city", "inc": True, "fips": "3712000", "lat": 35.2271, "lon": -80.8431, "pop": 874579, "county": "Mecklenburg"},
    {"state": "NC", "city": "Raleigh", "type": "city", "inc": True, "fips": "3755000", "lat": 35.7796, "lon": -78.6382, "pop": 467665, "county": "Wake"},
    {"state": "NC", "city": "Greensboro", "type": "city", "inc": True, "fips": "3728000", "lat": 36.0726, "lon": -79.7920, "pop": 299035, "county": "Guilford"},
    {"state": "NC", "city": "Durham", "type": "city", "inc": True, "fips": "3719000", "lat": 35.9940, "lon": -78.8986, "pop": 283506, "county": "Durham"},
    {"state": "NC", "city": "Winston-Salem", "type": "city", "inc": True, "fips": "3775000", "lat": 36.0999, "lon": -80.2442, "pop": 249545, "county": "Forsyth"},
    {"state": "NC", "city": "Fayetteville", "type": "city", "inc": True, "fips": "3722920", "lat": 35.0527, "lon": -78.8784, "pop": 208501, "county": "Cumberland"},

    # --- ARIZONA (AZ) ---
    {"state": "AZ", "city": "Phoenix", "type": "city", "inc": True, "fips": "0455000", "lat": 33.4484, "lon": -112.0740, "pop": 1608139, "county": "Maricopa"},
    {"state": "AZ", "city": "Tucson", "type": "city", "inc": True, "fips": "0477000", "lat": 32.2226, "lon": -110.9747, "pop": 542629, "county": "Pima"},
    {"state": "AZ", "city": "Mesa", "type": "city", "inc": True, "fips": "0446000", "lat": 33.4152, "lon": -111.8315, "pop": 504258, "county": "Maricopa"},
    {"state": "AZ", "city": "Chandler", "type": "city", "inc": True, "fips": "0412000", "lat": 33.3062, "lon": -111.8413, "pop": 275987, "county": "Maricopa"},
    {"state": "AZ", "city": "Scottsdale", "type": "city", "inc": True, "fips": "0465000", "lat": 33.4942, "lon": -111.9261, "pop": 241361, "county": "Maricopa"},
    {"state": "AZ", "city": "Glendale", "type": "city", "inc": True, "fips": "0427400", "lat": 33.5387, "lon": -112.1860, "pop": 248325, "county": "Maricopa"},

    # --- COLORADO (CO) ---
    {"state": "CO", "city": "Denver", "type": "city", "inc": True, "fips": "0820000", "lat": 39.7392, "lon": -104.9903, "pop": 715522, "county": "Denver"},
    {"state": "CO", "city": "Colorado Springs", "type": "city", "inc": True, "fips": "0816000", "lat": 38.8339, "lon": -104.8214, "pop": 478961, "county": "El Paso"},
    {"state": "CO", "city": "Aurora", "type": "city", "inc": True, "fips": "0804000", "lat": 39.7294, "lon": -104.8319, "pop": 386261, "county": "Arapahoe"},
    {"state": "CO", "city": "Fort Collins", "type": "city", "inc": True, "fips": "0827425", "lat": 40.5853, "lon": -105.0844, "pop": 169810, "county": "Larimer"},
    {"state": "CO", "city": "Boulder", "type": "city", "inc": True, "fips": "0807850", "lat": 40.0150, "lon": -105.2705, "pop": 108250, "county": "Boulder"},

    # --- OHIO (OH) ---
    {"state": "OH", "city": "Columbus", "type": "city", "inc": True, "fips": "3918000", "lat": 39.9612, "lon": -82.9988, "pop": 905748, "county": "Franklin"},
    {"state": "OH", "city": "Cleveland", "type": "city", "inc": True, "fips": "3916000", "lat": 41.4993, "lon": -81.6944, "pop": 372624, "county": "Cuyahoga"},
    {"state": "OH", "city": "Cincinnati", "type": "city", "inc": True, "fips": "3915000", "lat": 39.1031, "lon": -84.5120, "pop": 309317, "county": "Hamilton"},
    {"state": "OH", "city": "Toledo", "type": "city", "inc": True, "fips": "3977000", "lat": 41.6528, "lon": -83.5379, "pop": 270871, "county": "Lucas"},
    {"state": "OH", "city": "Akron", "type": "city", "inc": True, "fips": "3901000", "lat": 41.0814, "lon": -81.5190, "pop": 190469, "county": "Summit"},

    # --- PENNSYLVANIA (PA) ---
    {"state": "PA", "city": "Philadelphia", "type": "city", "inc": True, "fips": "4260000", "lat": 39.9526, "lon": -75.1652, "pop": 1603797, "county": "Philadelphia"},
    {"state": "PA", "city": "Pittsburgh", "type": "city", "inc": True, "fips": "4261000", "lat": 40.4406, "lon": -79.9959, "pop": 302971, "county": "Allegheny"},
    {"state": "PA", "city": "Allentown", "type": "city", "inc": True, "fips": "4202000", "lat": 40.6084, "lon": -75.4902, "pop": 125845, "county": "Lehigh"},
    {"state": "PA", "city": "Erie", "type": "city", "inc": True, "fips": "4224000", "lat": 42.1292, "lon": -80.0851, "pop": 94831, "county": "Erie"},
    {"state": "PA", "city": "Reading", "type": "city", "inc": True, "fips": "4263624", "lat": 40.3356, "lon": -75.9269, "pop": 95112, "county": "Berks"},

    # --- WASHINGTON (WA) ---
    {"state": "WA", "city": "Seattle", "type": "city", "inc": True, "fips": "5363000", "lat": 47.6062, "lon": -122.3321, "pop": 737015, "county": "King"},
    {"state": "WA", "city": "Spokane", "type": "city", "inc": True, "fips": "5367000", "lat": 47.6588, "lon": -117.4260, "pop": 228989, "county": "Spokane"},
    {"state": "WA", "city": "Tacoma", "type": "city", "inc": True, "fips": "5370000", "lat": 47.2529, "lon": -122.4443, "pop": 219346, "county": "Pierce"},
    {"state": "WA", "city": "Vancouver", "type": "city", "inc": True, "fips": "5374060", "lat": 45.6387, "lon": -122.6615, "pop": 190915, "county": "Clark"},
    {"state": "WA", "city": "Bellevue", "type": "city", "inc": True, "fips": "5305210", "lat": 47.6101, "lon": -122.2015, "pop": 151854, "county": "King"},

    # --- MICHIGAN (MI) ---
    {"state": "MI", "city": "Detroit", "type": "city", "inc": True, "fips": "2622000", "lat": 42.3314, "lon": -83.0458, "pop": 639111, "county": "Wayne"},
    {"state": "MI", "city": "Grand Rapids", "type": "city", "inc": True, "fips": "2634000", "lat": 42.9634, "lon": -85.6681, "pop": 198917, "county": "Kent"},
    {"state": "MI", "city": "Warren", "type": "city", "inc": True, "fips": "2684000", "lat": 42.4775, "lon": -83.0277, "pop": 139387, "county": "Macomb"},
    {"state": "MI", "city": "Ann Arbor", "type": "city", "inc": True, "fips": "2603000", "lat": 42.2808, "lon": -83.7430, "pop": 123851, "county": "Washtenaw"},
    {"state": "MI", "city": "Lansing", "type": "city", "inc": True, "fips": "2646000", "lat": 42.7325, "lon": -84.5555, "pop": 112644, "county": "Ingham"},

    # --- TENNESSEE (TN) ---
    {"state": "TN", "city": "Nashville", "type": "city", "inc": True, "fips": "4752006", "lat": 36.1627, "lon": -86.7816, "pop": 689447, "county": "Davidson"},
    {"state": "TN", "city": "Memphis", "type": "city", "inc": True, "fips": "4748000", "lat": 35.1495, "lon": -90.0490, "pop": 633104, "county": "Shelby"},
    {"state": "TN", "city": "Knoxville", "type": "city", "inc": True, "fips": "4740000", "lat": 35.9606, "lon": -83.9207, "pop": 190740, "county": "Knox"},
    {"state": "TN", "city": "Chattanooga", "type": "city", "inc": True, "fips": "4714000", "lat": 35.0456, "lon": -85.3097, "pop": 181099, "county": "Hamilton"},
    {"state": "TN", "city": "Clarksville", "type": "city", "inc": True, "fips": "4715160", "lat": 36.5298, "lon": -87.3595, "pop": 166722, "county": "Montgomery"},

    # --- MASSACHUSETTS (MA) ---
    {"state": "MA", "city": "Boston", "type": "city", "inc": True, "fips": "2507000", "lat": 42.3601, "lon": -71.0589, "pop": 675647, "county": "Suffolk"},
    {"state": "MA", "city": "Worcester", "type": "city", "inc": True, "fips": "2582000", "lat": 42.2626, "lon": -71.8023, "pop": 206518, "county": "Worcester"},
    {"state": "MA", "city": "Springfield", "type": "city", "inc": True, "fips": "2567000", "lat": 42.1015, "lon": -72.5898, "pop": 155929, "county": "Hampden"},
    {"state": "MA", "city": "Cambridge", "type": "city", "inc": True, "fips": "2511000", "lat": 42.3736, "lon": -71.1097, "pop": 118403, "county": "Middlesex"},

    # --- NEVADA (NV) ---
    {"state": "NV", "city": "Las Vegas", "type": "city", "inc": True, "fips": "3240000", "lat": 36.1699, "lon": -115.1398, "pop": 641903, "county": "Clark"},
    {"state": "NV", "city": "Henderson", "type": "city", "inc": True, "fips": "3231900", "lat": 36.0395, "lon": -114.9817, "pop": 317610, "county": "Clark"},
    {"state": "NV", "city": "Reno", "type": "city", "inc": True, "fips": "3260600", "lat": 39.5296, "lon": -119.8138, "pop": 264165, "county": "Washoe"},
    {"state": "NV", "city": "North Las Vegas", "type": "city", "inc": True, "fips": "3251800", "lat": 36.1989, "lon": -115.1175, "pop": 262527, "county": "Clark"},

    # --- VIRGINIA (VA) ---
    {"state": "VA", "city": "Virginia Beach", "type": "city", "inc": True, "fips": "5182000", "lat": 36.8529, "lon": -75.9780, "pop": 459470, "county": "Virginia Beach"},
    {"state": "VA", "city": "Norfolk", "type": "city", "inc": True, "fips": "5157000", "lat": 36.8508, "lon": -76.2859, "pop": 238005, "county": "Norfolk"},
    {"state": "VA", "city": "Chesapeake", "type": "city", "inc": True, "fips": "5116000", "lat": 36.7682, "lon": -76.2875, "pop": 249422, "county": "Chesapeake"},
    {"state": "VA", "city": "Richmond", "type": "city", "inc": True, "fips": "5167000", "lat": 37.5407, "lon": -77.4360, "pop": 226610, "county": "Richmond"},
    {"state": "VA", "city": "Arlington", "type": "CDP", "inc": False, "fips": "5103000", "lat": 38.8799, "lon": -77.1067, "pop": 238643, "county": "Arlington"},

    # --- MISSOURI (MO) ---
    {"state": "MO", "city": "Kansas City", "type": "city", "inc": True, "fips": "2938000", "lat": 39.0997, "lon": -94.5786, "pop": 508090, "county": "Jackson"},
    {"state": "MO", "city": "St. Louis", "type": "city", "inc": True, "fips": "2965000", "lat": 38.6270, "lon": -90.1994, "pop": 301578, "county": "St. Louis City"},
    {"state": "MO", "city": "Springfield", "type": "city", "inc": True, "fips": "2970000", "lat": 37.2089, "lon": -93.2923, "pop": 169176, "county": "Greene"},
    {"state": "MO", "city": "Columbia", "type": "city", "inc": True, "fips": "2915670", "lat": 38.9517, "lon": -92.3341, "pop": 126254, "county": "Boone"},

    # --- INDIANA (IN) ---
    {"state": "IN", "city": "Indianapolis", "type": "city", "inc": True, "fips": "1836003", "lat": 39.7684, "lon": -86.1581, "pop": 887642, "county": "Marion"},
    {"state": "IN", "city": "Fort Wayne", "type": "city", "inc": True, "fips": "1825000", "lat": 41.0793, "lon": -85.1394, "pop": 263886, "county": "Allen"},
    {"state": "IN", "city": "Evansville", "type": "city", "inc": True, "fips": "1822000", "lat": 37.9716, "lon": -87.5711, "pop": 117298, "county": "Vanderburgh"},
    {"state": "IN", "city": "South Bend", "type": "city", "inc": True, "fips": "1871000", "lat": 41.6764, "lon": -86.2520, "pop": 103453, "county": "St. Joseph"},

    # --- MINNESOTA (MN) ---
    {"state": "MN", "city": "Minneapolis", "type": "city", "inc": True, "fips": "2743000", "lat": 44.9778, "lon": -93.2650, "pop": 429954, "county": "Hennepin"},
    {"state": "MN", "city": "Saint Paul", "type": "city", "inc": True, "fips": "2758000", "lat": 44.9537, "lon": -93.0900, "pop": 311527, "county": "Ramsey"},
    {"state": "MN", "city": "Rochester", "type": "city", "inc": True, "fips": "2754880", "lat": 44.0121, "lon": -92.4802, "pop": 121395, "county": "Olmsted"},
    {"state": "MN", "city": "Duluth", "type": "city", "inc": True, "fips": "2717000", "lat": 46.7867, "lon": -92.1005, "pop": 86697, "county": "St. Louis"},

    # --- WISCONSIN (WI) ---
    {"state": "WI", "city": "Milwaukee", "type": "city", "inc": True, "fips": "5553000", "lat": 43.0389, "lon": -87.9065, "pop": 577222, "county": "Milwaukee"},
    {"state": "WI", "city": "Madison", "type": "city", "inc": True, "fips": "5548000", "lat": 43.0731, "lon": -89.4012, "pop": 269840, "county": "Dane"},
    {"state": "WI", "city": "Green Bay", "type": "city", "inc": True, "fips": "5531000", "lat": 44.5192, "lon": -88.0198, "pop": 107395, "county": "Brown"},

    # --- MARYLAND (MD) ---
    {"state": "MD", "city": "Baltimore", "type": "city", "inc": True, "fips": "2404000", "lat": 39.2904, "lon": -76.6122, "pop": 585708, "county": "Baltimore City"},
    {"state": "MD", "city": "Frederick", "type": "city", "inc": True, "fips": "2430325", "lat": 39.4143, "lon": -77.4105, "pop": 78171, "county": "Frederick"},
    {"state": "MD", "city": "Rockville", "type": "city", "inc": True, "fips": "2467675", "lat": 39.0840, "lon": -77.1528, "pop": 67117, "county": "Montgomery"},
    {"state": "MD", "city": "Gaithersburg", "type": "city", "inc": True, "fips": "2431175", "lat": 39.1434, "lon": -77.2014, "pop": 69657, "county": "Montgomery"},

    # --- OREGON (OR) ---
    {"state": "OR", "city": "Portland", "type": "city", "inc": True, "fips": "4159000", "lat": 45.5152, "lon": -122.6784, "pop": 652503, "county": "Multnomah"},
    {"state": "OR", "city": "Eugene", "type": "city", "inc": True, "fips": "4123850", "lat": 44.0521, "lon": -123.0868, "pop": 176654, "county": "Lane"},
    {"state": "OR", "city": "Salem", "type": "city", "inc": True, "fips": "4164900", "lat": 44.9429, "lon": -123.0351, "pop": 175535, "county": "Marion"},

    # --- OKLAHOMA (OK) ---
    {"state": "OK", "city": "Oklahoma City", "type": "city", "inc": True, "fips": "4055000", "lat": 35.4676, "lon": -97.5164, "pop": 681054, "county": "Oklahoma"},
    {"state": "OK", "city": "Tulsa", "type": "city", "inc": True, "fips": "4075000", "lat": 36.1540, "lon": -95.9928, "pop": 413066, "county": "Tulsa"},
    {"state": "OK", "city": "Norman", "type": "city", "inc": True, "fips": "4052500", "lat": 35.2226, "lon": -97.4395, "pop": 128026, "county": "Cleveland"},

    # --- KENTUCKY (KY) ---
    {"state": "KY", "city": "Louisville", "type": "city", "inc": True, "fips": "2148006", "lat": 38.2527, "lon": -85.7585, "pop": 633045, "county": "Jefferson"},
    {"state": "KY", "city": "Lexington", "type": "city", "inc": True, "fips": "2146027", "lat": 38.0406, "lon": -84.5037, "pop": 322570, "county": "Fayette"},
    {"state": "KY", "city": "Bowling Green", "type": "city", "inc": True, "fips": "2108902", "lat": 36.9685, "lon": -86.4808, "pop": 72294, "county": "Warren"},

    # --- LOUISIANA (LA) ---
    {"state": "LA", "city": "New Orleans", "type": "city", "inc": True, "fips": "2255000", "lat": 29.9511, "lon": -90.0715, "pop": 383997, "county": "Orleans"},
    {"state": "LA", "city": "Baton Rouge", "type": "city", "inc": True, "fips": "2205000", "lat": 30.4515, "lon": -91.1871, "pop": 227470, "county": "East Baton Rouge"},
    {"state": "LA", "city": "Shreveport", "type": "city", "inc": True, "fips": "2270000", "lat": 32.5252, "lon": -93.7502, "pop": 187593, "county": "Caddo"},

    # --- ALABAMA (AL) ---
    {"state": "AL", "city": "Huntsville", "type": "city", "inc": True, "fips": "0137000", "lat": 34.7304, "lon": -86.5861, "pop": 215006, "county": "Madison"},
    {"state": "AL", "city": "Birmingham", "type": "city", "inc": True, "fips": "0107000", "lat": 33.5186, "lon": -86.8104, "pop": 200733, "county": "Jefferson"},
    {"state": "AL", "city": "Montgomery", "type": "city", "inc": True, "fips": "0151000", "lat": 32.3792, "lon": -86.3077, "pop": 200603, "county": "Montgomery"},
    {"state": "AL", "city": "Mobile", "type": "city", "inc": True, "fips": "0150000", "lat": 30.6954, "lon": -88.0399, "pop": 187041, "county": "Mobile"},

    # --- SOUTH CAROLINA (SC) ---
    {"state": "SC", "city": "Charleston", "type": "city", "inc": True, "fips": "4513330", "lat": 32.7765, "lon": -79.9311, "pop": 150227, "county": "Charleston"},
    {"state": "SC", "city": "Columbia", "type": "city", "inc": True, "fips": "4516000", "lat": 34.0007, "lon": -81.0348, "pop": 136632, "county": "Richland"},
    {"state": "SC", "city": "North Charleston", "type": "city", "inc": True, "fips": "4550875", "lat": 32.8546, "lon": -79.9748, "pop": 114852, "county": "Charleston"},
    {"state": "SC", "city": "Greenville", "type": "city", "inc": True, "fips": "4530850", "lat": 34.8526, "lon": -82.3940, "pop": 70720, "county": "Greenville"},

    # --- UTAH (UT) ---
    {"state": "UT", "city": "Salt Lake City", "type": "city", "inc": True, "fips": "4967000", "lat": 40.7608, "lon": -111.8910, "pop": 199723, "county": "Salt Lake"},
    {"state": "UT", "city": "West Valley City", "type": "city", "inc": True, "fips": "4983470", "lat": 40.6916, "lon": -111.9791, "pop": 140230, "county": "Salt Lake"},
    {"state": "UT", "city": "Provo", "type": "city", "inc": True, "fips": "4962470", "lat": 40.2338, "lon": -111.6585, "pop": 115162, "county": "Utah"},

    # --- KANSAS (KS) ---
    {"state": "KS", "city": "Wichita", "type": "city", "inc": True, "fips": "2079000", "lat": 37.6872, "lon": -97.3301, "pop": 397532, "county": "Sedgwick"},
    {"state": "KS", "city": "Overland Park", "type": "city", "inc": True, "fips": "2053775", "lat": 38.9822, "lon": -94.6708, "pop": 197238, "county": "Johnson"},
    {"state": "KS", "city": "Kansas City", "type": "city", "inc": True, "fips": "2036000", "lat": 39.1142, "lon": -94.6275, "pop": 156607, "county": "Wyandotte"},

    # --- NEW JERSEY (NJ) ---
    {"state": "NJ", "city": "Newark", "type": "city", "inc": True, "fips": "3451000", "lat": 40.7357, "lon": -74.1724, "pop": 311549, "county": "Essex"},
    {"state": "NJ", "city": "Jersey City", "type": "city", "inc": True, "fips": "3436000", "lat": 40.7178, "lon": -74.0431, "pop": 292449, "county": "Hudson"},
    {"state": "NJ", "city": "Paterson", "type": "city", "inc": True, "fips": "3457000", "lat": 40.9168, "lon": -74.1718, "pop": 159732, "county": "Passaic"},

    # --- NEW MEXICO (NM) ---
    {"state": "NM", "city": "Albuquerque", "type": "city", "inc": True, "fips": "3502000", "lat": 35.0844, "lon": -106.6504, "pop": 564559, "county": "Bernalillo"},
    {"state": "NM", "city": "Las Cruces", "type": "city", "inc": True, "fips": "3539380", "lat": 32.3199, "lon": -106.7637, "pop": 111385, "county": "Dona Ana"},
    {"state": "NM", "city": "Santa Fe", "type": "city", "inc": True, "fips": "3570500", "lat": 35.6870, "lon": -105.9378, "pop": 87505, "county": "Santa Fe"},

    # --- NEBRASKA (NE) ---
    {"state": "NE", "city": "Omaha", "type": "city", "inc": True, "fips": "3137000", "lat": 41.2565, "lon": -95.9345, "pop": 486051, "county": "Douglas"},
    {"state": "NE", "city": "Lincoln", "type": "city", "inc": True, "fips": "3128000", "lat": 40.8136, "lon": -96.7026, "pop": 291082, "county": "Lancaster"},

    # --- IOWA (IA) ---
    {"state": "IA", "city": "Des Moines", "type": "city", "inc": True, "fips": "1921000", "lat": 41.5868, "lon": -93.6250, "pop": 214133, "county": "Polk"},
    {"state": "IA", "city": "Cedar Rapids", "type": "city", "inc": True, "fips": "1912000", "lat": 41.9779, "lon": -91.6656, "pop": 137710, "county": "Linn"},

    # --- IDAHO (ID) ---
    {"state": "ID", "city": "Boise", "type": "city", "inc": True, "fips": "1608830", "lat": 43.6150, "lon": -116.2023, "pop": 235684, "county": "Ada"},
    {"state": "ID", "city": "Meridian", "type": "city", "inc": True, "fips": "1652120", "lat": 43.6121, "lon": -116.3915, "pop": 117635, "county": "Ada"},

    # --- HAWAII (HI) ---
    {"state": "HI", "city": "Honolulu", "type": "CDP", "inc": False, "fips": "1517000", "lat": 21.3069, "lon": -157.8583, "pop": 350964, "county": "Honolulu"},
    {"state": "HI", "city": "East Honolulu", "type": "CDP", "inc": False, "fips": "1507425", "lat": 21.2891, "lon": -157.7174, "pop": 50922, "county": "Honolulu"},

    # --- CONNECTICUT (CT) ---
    {"state": "CT", "city": "Bridgeport", "type": "city", "inc": True, "fips": "0908000", "lat": 41.1792, "lon": -73.1894, "pop": 148654, "county": "Fairfield"},
    {"state": "CT", "city": "New Haven", "type": "city", "inc": True, "fips": "0952000", "lat": 41.3083, "lon": -72.9279, "pop": 134023, "county": "New Haven"},
    {"state": "CT", "city": "Hartford", "type": "city", "inc": True, "fips": "0937000", "lat": 41.7658, "lon": -72.6734, "pop": 121054, "county": "Hartford"},

    # --- ARKANSAS (AR) ---
    {"state": "AR", "city": "Little Rock", "type": "city", "inc": True, "fips": "0541000", "lat": 34.7465, "lon": -92.2896, "pop": 202591, "county": "Pulaski"},
    {"state": "AR", "city": "Fayetteville", "type": "city", "inc": True, "fips": "0523290", "lat": 36.0822, "lon": -94.1719, "pop": 93949, "county": "Washington"},

    # --- MISSISSIPPI (MS) ---
    {"state": "MS", "city": "Jackson", "type": "city", "inc": True, "fips": "2836000", "lat": 32.2988, "lon": -90.1848, "pop": 153701, "county": "Hinds"},
    {"state": "MS", "city": "Gulfport", "type": "city", "inc": True, "fips": "2829700", "lat": 30.3674, "lon": -89.0928, "pop": 72926, "county": "Harrison"},

    # --- ALASKA (AK) ---
    {"state": "AK", "city": "Anchorage", "type": "city", "inc": True, "fips": "0203000", "lat": 61.2181, "lon": -149.9003, "pop": 291247, "county": "Anchorage"},
    {"state": "AK", "city": "Fairbanks", "type": "city", "inc": True, "fips": "0224230", "lat": 64.8378, "lon": -147.7164, "pop": 32515, "county": "Fairbanks North Star"},
    {"state": "AK", "city": "Juneau", "type": "city", "inc": True, "fips": "0236400", "lat": 58.3019, "lon": -134.4197, "pop": 32255, "county": "Juneau"},

    # --- DISTRICT OF COLUMBIA (DC) ---
    {"state": "DC", "city": "Washington", "type": "city", "inc": True, "fips": "1150000", "lat": 38.9072, "lon": -77.0369, "pop": 689545, "county": "District of Columbia"},

    # --- RHODE ISLAND (RI) ---
    {"state": "RI", "city": "Providence", "type": "city", "inc": True, "fips": "4459000", "lat": 41.8240, "lon": -71.4128, "pop": 190934, "county": "Providence"},
    {"state": "RI", "city": "Warwick", "type": "city", "inc": True, "fips": "4474300", "lat": 41.7001, "lon": -71.4162, "pop": 82823, "county": "Kent"},

    # --- DELAWARE (DE) ---
    {"state": "DE", "city": "Wilmington", "type": "city", "inc": True, "fips": "1077580", "lat": 39.7447, "lon": -75.5484, "pop": 70898, "county": "New Castle"},
    {"state": "DE", "city": "Dover", "type": "city", "inc": True, "fips": "1021140", "lat": 39.1582, "lon": -75.5244, "pop": 39403, "county": "Kent"},

    # --- SOUTH DAKOTA (SD) ---
    {"state": "SD", "city": "Sioux Falls", "type": "city", "inc": True, "fips": "4659020", "lat": 43.5460, "lon": -96.7313, "pop": 192517, "county": "Minnehaha"},
    {"state": "SD", "city": "Rapid City", "type": "city", "inc": True, "fips": "4652980", "lat": 44.0805, "lon": -103.2310, "pop": 74703, "county": "Pennington"},

    # --- NORTH DAKOTA (ND) ---
    {"state": "ND", "city": "Fargo", "type": "city", "inc": True, "fips": "3825700", "lat": 46.8772, "lon": -96.7898, "pop": 125990, "county": "Cass"},
    {"state": "ND", "city": "Bismarck", "type": "city", "inc": True, "fips": "3807200", "lat": 46.8083, "lon": -100.7837, "pop": 73622, "county": "Burleigh"},

    # --- MONTANA (MT) ---
    {"state": "MT", "city": "Billings", "type": "city", "inc": True, "fips": "3006550", "lat": 45.7833, "lon": -108.5007, "pop": 117116, "county": "Yellowstone"},
    {"state": "MT", "city": "Missoula", "type": "city", "inc": True, "fips": "3050200", "lat": 46.8722, "lon": -113.9940, "pop": 73489, "county": "Missoula"},

    # --- MAINE (ME) ---
    {"state": "ME", "city": "Portland", "type": "city", "inc": True, "fips": "2360545", "lat": 43.6591, "lon": -70.2568, "pop": 68408, "county": "Cumberland"},
    {"state": "ME", "city": "Lewiston", "type": "city", "inc": True, "fips": "2338740", "lat": 44.1004, "lon": -70.2148, "pop": 37121, "county": "Androscoggin"},

    # --- NEW HAMPSHIRE (NH) ---
    {"state": "NH", "city": "Manchester", "type": "city", "inc": True, "fips": "3345140", "lat": 42.9956, "lon": -71.4548, "pop": 115644, "county": "Hillsborough"},
    {"state": "NH", "city": "Nashua", "type": "city", "inc": True, "fips": "3350220", "lat": 42.7654, "lon": -71.4676, "pop": 91322, "county": "Hillsborough"},

    # --- VERMONT (VT) ---
    {"state": "VT", "city": "Burlington", "type": "city", "inc": True, "fips": "5010675", "lat": 44.4759, "lon": -73.2121, "pop": 44743, "county": "Chittenden"},
    {"state": "VT", "city": "South Burlington", "type": "city", "inc": True, "fips": "5066175", "lat": 44.4669, "lon": -73.1709, "pop": 20292, "county": "Chittenden"},

    # --- WEST VIRGINIA (WV) ---
    {"state": "WV", "city": "Charleston", "type": "city", "inc": True, "fips": "5414600", "lat": 38.3498, "lon": -81.6326, "pop": 48864, "county": "Kanawha"},
    {"state": "WV", "city": "Huntington", "type": "city", "inc": True, "fips": "5439460", "lat": 38.4192, "lon": -82.4452, "pop": 46842, "county": "Cabell"},

    # --- WYOMING (WY) ---
    {"state": "WY", "city": "Cheyenne", "type": "city", "inc": True, "fips": "5613900", "lat": 41.1400, "lon": -104.8202, "pop": 65132, "county": "Laramie"},
    {"state": "WY", "city": "Casper", "type": "city", "inc": True, "fips": "5613150", "lat": 42.8501, "lon": -106.3252, "pop": 59038, "county": "Natrona"}
]


def seed_us_locations(session: Session) -> dict[str, int]:
    """
    Populates US States and Cities database tables if not already present.
    Ensures expandable and updateable US Census dataset.
    """
    states_added = 0
    cities_added = 0

    # 1. Seed States
    existing_states = {s.abbr: s for s in session.query(USState).all()}
    for s_data in US_STATES_DATA:
        if s_data["abbr"] not in existing_states:
            st = USState(
                id=s_data["abbr"],
                name=s_data["name"],
                abbr=s_data["abbr"],
                fips_code=s_data["fips_code"],
                capital=s_data["capital"],
                latitude=s_data["latitude"],
                longitude=s_data["longitude"]
            )
            session.add(st)
            states_added += 1

    session.flush()

    # 2. Seed Cities
    existing_city_ids = {c.id for c in session.query(USCity.id).all()}
    for c_data in US_CITIES_DATA:
        c_id = f"{c_data['state']}_{c_data['city'].lower().replace(' ', '_')}_{c_data['fips']}"
        if c_id not in existing_city_ids:
            city_obj = USCity(
                id=c_id,
                state_abbr=c_data["state"],
                city_name=c_data["city"],
                place_type=c_data.get("type", "city"),
                is_incorporated=c_data.get("inc", True),
                fips_code=c_data["fips"],
                latitude=c_data["lat"],
                longitude=c_data["lon"],
                population=c_data.get("pop", 0),
                county=c_data.get("county", "")
            )
            session.add(city_obj)
            cities_added += 1

    session.commit()
    return {"states_added": states_added, "cities_added": cities_added}
