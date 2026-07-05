"""Reference list of 30 global metro cities for the Climate-Economic Risk Explorer.

Selected for: geographic spread across continents, mix of coastal/inland,
mix of developed/emerging economies, and availability in World Bank + EM-DAT data.
"""

CITIES = [
    # (name, country, lat, lon)
    ("New York",      "USA",           40.7128,   -74.0060),
    ("Los Angeles",   "USA",           34.0522,  -118.2437),
    ("Miami",         "USA",           25.7617,   -80.1918),
    ("Mexico City",   "Mexico",        19.4326,   -99.1332),
    ("Sao Paulo",     "Brazil",       -23.5505,   -46.6333),
    ("Buenos Aires",  "Argentina",    -34.6037,   -58.3816),
    ("London",        "UK",            51.5072,    -0.1276),
    ("Paris",         "France",        48.8566,     2.3522),
    ("Berlin",        "Germany",       52.5200,    13.4050),
    ("Madrid",        "Spain",         40.4168,    -3.7038),
    ("Rome",          "Italy",         41.9028,    12.4964),
    ("Moscow",        "Russia",        55.7558,    37.6173),
    ("Istanbul",      "Turkey",        41.0082,    28.9784),
    ("Cairo",         "Egypt",         30.0444,    31.2357),
    ("Lagos",         "Nigeria",        6.5244,     3.3792),
    ("Nairobi",       "Kenya",         -1.2921,    36.8219),
    ("Johannesburg",  "South Africa", -26.2041,    28.0473),
    ("Mumbai",        "India",         19.0760,    72.8777),
    ("Delhi",         "India",         28.7041,    77.1025),
    ("Dhaka",         "Bangladesh",    23.8103,    90.4125),
    ("Bangkok",       "Thailand",      13.7563,   100.5018),
    ("Jakarta",       "Indonesia",     -6.2088,   106.8456),
    ("Manila",        "Philippines",   14.5995,   120.9842),
    ("Shanghai",      "China",         31.2304,   121.4737),
    ("Beijing",       "China",         39.9042,   116.4074),
    ("Tokyo",         "Japan",         35.6762,   139.6503),
    ("Seoul",         "South Korea",   37.5665,   126.9780),
    ("Sydney",        "Australia",    -33.8688,   151.2093),
    ("Melbourne",     "Australia",    -37.8136,   144.9631),
    ("Singapore",     "Singapore",     1.3521,    103.8198),
]

assert len(CITIES) == 30, f"Expected 30 cities, got {len(CITIES)}"
