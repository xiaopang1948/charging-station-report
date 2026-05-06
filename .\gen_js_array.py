import json

path = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/"
with open(path + "stations_data.json", encoding="utf-8") as f:
    stations = json.load(f)

# Generate JS array
items = []
for s in stations:
    items.append(json.dumps({
        "name": s["name"],
        "address": s["address"],
        "lng": s["lng"],
        "lat": s["lat"],
        "brand": s["brand"],
        "distance": s["distance"],
        "rating": s.get("rating", "-")
    }, ensure_ascii=False))

js = "var stations = [" + ",".join(items) + "];"
print(js)
