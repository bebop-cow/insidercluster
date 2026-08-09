import asyncio, json, websockets

async def stream_ais(api_key, seconds=120):
    url = "wss://stream.aisstream.io/v0/stream"
    subscribe = {
        "APIKey": api_key,
        "BoundingBoxes": [
            [[24.0, 54.0], [27.5, 58.5]],   # Hormuz
            [[11.5, 42.0], [14.5, 44.5]],   # Bab-el-Mandeb
        ],
        "FilterMessageTypes": ["PositionReport"],
    }
    count = 0
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps(subscribe))
        print("connected, waiting up to", seconds, "s...")
        try:
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=seconds)
                msg = json.loads(raw)
                mtype = msg.get("MessageType")
                if mtype not in ("PositionReport", "StandardClassBPositionReport"):
                    continue
                # the nested key matches the type name:
                pr = msg["Message"][mtype]
                meta = msg["MetaData"]
                count += 1
                print(count, meta.get("ShipName", "?").strip(),
                      round(pr["Latitude"], 3), round(pr["Longitude"], 3))
                if count >= 15:
                    break
        except asyncio.TimeoutError:
            print(f"quiet for {seconds}s")
    print("total:", count)

asyncio.run(stream_ais("1d1d1084705fa76fe17be94f7ce466f1b7e35f4d", 120))


async def diag(api_key):
    async with websockets.connect(
        "wss://stream.aisstream.io/v0/stream",
        ping_interval=20, ping_timeout=20, max_size=None
    ) as ws:
        payload = {"APIKey": api_key, "BoundingBoxes": [[[-90, -180], [90, 180]]]}
        await ws.send(json.dumps(payload))
        print("sent:", json.dumps(payload)[:60])
        try:
            for _ in range(5):
                raw = await asyncio.wait_for(ws.recv(), timeout=30)
                print("RECV:", raw[:200])
        except asyncio.TimeoutError:
            print("no data in 30s")

asyncio.run(diag("1d1d1084705fa76fe17be94f7ce466f1b7e35f4d"))
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
