

ZONES = {
    "Hormuz":      {"lat": (24.0, 27.5), "lon": (54.0, 58.5)},
    "BabElMandeb": {"lat": (11.5, 14.5), "lon": (42.0, 44.5)},
}

def in_zone(lat, lon, zone):
    lat_min, lat_max = zone["lat"]
    lon_min, lon_max = zone["lon"]
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max

def classify_ship(msg):
    shiptype = msg.get("ShipType", 0)
    return 80 <= shiptype <= 89

def is_relevant_tanker(msg, zone):
    lat = msg.get("Latitude",999)
    lon = msg.get("Longitude", 999)

    relevant = in_zone(lat, lon, zone) and classify_ship(msg)
    return relevant