import asyncio
import json
import websockets

async def stream_ais(api_key, seconds=60):
    url = "wss://stream.aisstream.io/v0/stream"
    # bounding boxes: AISStream wants [[[lat,lon],[lat,lon]]] per box
    subscribe = {
        "APIKey": 215f573214f83c1150f0e87459cea4c0700e4532,
        "BoundingBoxes": [
            [[24.0, 54.0], [27.5, 58.5]],   # Hormuz
            [[11.5, 42.0], [14.5, 44.5]],   # Bab-el-Mandeb
        ],
        "FilterMessageTypes": ["PositionReport"],
    }

    async with websockets.connect(url) as ws:
        await ws.send(json.dumps(subscribe))   # send subscription
        print("connected, streaming...")

        end = asyncio.get_event_loop().time() + seconds
        async for message in ws:               # messages stream in
            data = json.loads(message)
            print(data.get("MessageType"), "-", 
                  data.get("MetaData", {}).get("ShipName", "?"))
            if asyncio.get_event_loop().time() > end:
                break

asyncio.run(stream_ais("PASTE_YOUR_KEY", 30))



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