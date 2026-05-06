"""Update index.html with new coords, distances, labels."""
import json, re

path = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/"

# Read stations data
with open(path + "stations_data.json", encoding="utf-8") as f:
    stations = json.load(f)

# Generate JS stations array
items = []
for s in stations:
    rating = s.get("rating", "-")
    if rating == "[]" or rating == "":
        rating = "-"
    items.append(json.dumps({
        "name": s["name"],
        "address": s["address"],
        "lng": s["lng"],
        "lat": s["lat"],
        "brand": s["brand"],
        "distance": s["distance"],
        "rating": rating
    }, ensure_ascii=False))
new_js_array = "var stations = [" + ",".join(items) + "];"

# Read index.html
with open(path + "index.html", encoding="utf-8") as f:
    html = f.read()

# 1. Replace the stations array (track bracket depth to handle nested [] in data)
marker = "var stations = ["
start = html.find(marker)
if start == -1:
    print("ERROR: Could not find stations array")
    exit(1)
start += len(marker)
depth = 1
i = start
in_str = False
while depth > 0 and i < len(html):
    ch = html[i]
    if ch == '"' and (i == 0 or html[i-1] != '\\'):
        in_str = not in_str
    if not in_str:
        if ch == '[': depth += 1
        elif ch == ']': depth -= 1
    i += 1
html = html[:start-len(marker)] + new_js_array + html[i:]

# 2. Replace old coords in map section
html = html.replace("[41.512269,111.694882]", "[41.51879906,111.69113591]")

# 3. Replace 脑木更路7号 label
html = html.replace("脑木更路7号（商铺）", "高油房路（充电桩规划位）")
html = html.replace("商铺位置：脑木更路7号", "商铺位置：高油房路（充电桩规划位）")
html = html.replace("脑木更路7号", "高油房路（充电桩规划位）")
html = html.replace("脑木更路北 1.8km", "高油房路北 1.8km")
html = html.replace("脑木更路东北 1.6km", "高油房路东北 1.6km")
html = html.replace("脑木更路北 2.1km", "高油房路北 2.1km")

# Write back
with open(path + "index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("index.html updated successfully")

# Verify distances updated
with open(path + "index.html", encoding="utf-8") as f:
    html = f.read()

# Find the nearest station distance for verification
m = re.search(r'"distance":\s*([\d.]+)', html)
if m:
    print(f"First station distance in HTML: {m.group(1)}km")
