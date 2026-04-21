"""
Onlink-Clone: Geographic Data

Hardcoded real-world locations for airports, seaports, and cities
to support the transport layer routing on the WebGIS map.
"""

AIRPORTS = {
    "LHR": {"name": "Heathrow Airport", "city": "London", "lat": 51.4700, "lon": -0.4543},
    "JFK": {"name": "JFK International", "city": "New York", "lat": 40.6413, "lon": -73.7781},
    "HND": {"name": "Haneda Airport", "city": "Tokyo", "lat": 35.5494, "lon": 139.7798},
    "DXB": {"name": "Dubai International", "city": "Dubai", "lat": 25.2532, "lon": 55.3657},
    "SYD": {"name": "Sydney Airport", "city": "Sydney", "lat": -33.9399, "lon": 151.1753},
    "CDG": {"name": "Charles de Gaulle", "city": "Paris", "lat": 49.0097, "lon": 2.5479},
    "LAX": {"name": "Los Angeles International", "city": "Los Angeles", "lat": 33.9416, "lon": -118.4085},
    "FRA": {"name": "Charles de Gaulle", "city": "Paris", "lat": 49.0097, "lon": 2.5479},
    "CHC": {"name": "Christchurch International", "city": "Christchurch", "lat": -43.4864, "lon": 172.5369},
}

SEAPORTS = {
    "SGH": {"name": "Port of Shanghai", "city": "Shanghai", "lat": 31.2304, "lon": 121.4737},
    "ROT": {"name": "Port of Rotterdam", "city": "Rotterdam", "lat": 51.9225, "lon": 4.4791},
    "LA": {"name": "Port of Los Angeles", "city": "Los Angeles", "lat": 33.7292, "lon": -118.2620},
    "SGP": {"name": "Port of Singapore", "city": "Singapore", "lat": 1.2640, "lon": 103.8400},
    "HAM": {"name": "Port of Hamburg", "city": "Hamburg", "lat": 53.5435, "lon": 9.9853},
    "NYC": {"name": "Port of New York", "city": "New York", "lat": 40.6700, "lon": -74.0000},
    "TYO": {"name": "Port of Tokyo", "city": "Tokyo", "lat": 35.6200, "lon": 139.7700},
    "LTN": {"name": "Port of Lyttelton", "city": "Christchurch", "lat": -43.6060, "lon": 172.7130},
}
