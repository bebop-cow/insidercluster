import asyncio
import json
import websockets

async def stream_ais(api_key, seconds=90):
    url = "wss://stream.aisstream.io/v0/stream"
    subscribe = {
        "APIKey": api_key,
        "BoundingBoxes": [
            [[24.0, 54.0], [27.5, 58.5]],   # Hormuz  (SW, NE) = (lat,lon)
            [[11.5, 42.0], [14.5, 44.5]],   # Bab-el-Mandeb
        ],
        "FilterMessageTypes": ["PositionReport"],
    }
    count = 0
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps(subscribe))
        print("connected, streaming...")
        try:
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=seconds)
                msg = json.loads(raw)
                if msg["messageType"] != "PositionReport":
                    continue
                # position data is NESTED, not top-level:
                pr = msg["Message"]["PositionReport"]
                meta = msg["MetaData"]
                count += 1
                print(count, meta.get("ShipName", "?").strip(),
                      round(pr["Latitude"], 3), round(pr["Longitude"], 3))
        except asyncio.TimeoutError:
            print(f"quiet for {seconds}s")
    print("total:", count)

asyncio.run(stream_ais("215f573214f83c1150f0e87459cea4c0700e4532", 30))



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
