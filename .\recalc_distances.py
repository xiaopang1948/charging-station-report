import json, math

SHOP_LON, SHOP_LAT = 111.69113591, 41.51879906

def haversine(lon1, lat1, lon2, lat2):
    R = 6371
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

path = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/"
with open(path + "stations_data.json", encoding="utf-8") as f:
    stations = json.load(f)

updated = 0
for s in stations:
    d = haversine(SHOP_LON, SHOP_LAT, s["lng"], s["lat"])
    if abs(d - s["distance"]) > 0.001:
        updated += 1
    s["distance"] = round(d, 2)

print(f"Updated {updated} stations")

with open(path + "stations_data.json", "w", encoding="utf-8") as f:
    json.dump(stations, f, ensure_ascii=False, indent=2)

# Print nearest stations
nearby = sorted(stations, key=lambda s: s["distance"])[:10]
print("\nNearest stations:")
for s in nearby:
    print(f'  {s["name"]} - {s["distance"]}km')
