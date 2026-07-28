ZONES = {
    "Hormuz":      {"lat": (24.0, 27.5), "lon": (54.0, 58.5)},
    "BabElMandeb": {"lat": (11.5, 14.5), "lon": (42.0, 44.5)},
}

def in_zone(lat, lon, zone):
    lat_min, lat_max = zone["lat"]
    lon_min, lon_max = zone["lon"]
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max