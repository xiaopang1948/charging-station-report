"""
四子王旗充电站POI数据分析 + 地图可视化
"""
import csv
import json
import math
from collections import Counter, defaultdict

DATA_PATH = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/四子王旗充电站POI数据_20260505.csv"
OUT_DIR = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/"

# 高油房路南侧商铺（估算坐标）
SHOP_LON, SHOP_LAT = 111.69113591, 41.51879906

# ========== 1. 读数据 + 去重 ==========
rows = []
with open(DATA_PATH, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r["经度"] and r["纬度"]:
            r["经度_f"] = float(r["经度"])
            r["纬度_f"] = float(r["纬度"])
            rows.append(r)

def haversine(lon1, lat1, lon2, lat2):
    """计算两点间直线距离(km)"""
    R = 6371
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# 去重（按名称去重，保留第一个）
seen_names = set()
stations = []
for r in rows:
    name = r["名称"].strip()
    if name not in seen_names:
        seen_names.add(name)
        r["距离商铺_km"] = round(haversine(SHOP_LON, SHOP_LAT, r["经度_f"], r["纬度_f"]), 2)
        stations.append(r)

# ========== 2. 品牌分类 ==========
def classify_brand(name):
    name = name.replace(" ", "")
    if "蒙电e充" in name or "供电分公司" in name or "四子王供电" in name:
        return "蒙电e充"
    elif "星星充电" in name:
        return "星星充电"
    elif "蒙来电" in name:
        return "蒙来电"
    elif "蒙马" in name:
        return "蒙马(高速)"
    elif "咔咔电姆" in name:
        return "咔咔电姆"
    elif "驴充充" in name:
        return "驴充充"
    elif "云快充" in name:
        return "云快充"
    else:
        return "其他"

for s in stations:
    s["品牌"] = classify_brand(s["名称"])

# ========== 3. 分析统计 ==========
brand_count = Counter(s["品牌"] for s in stations)
print("=== 品牌分布 ===")
for b, c in brand_count.most_common():
    print(f"  {b}: {c}")

# 按距离排序
stations_sorted = sorted(stations, key=lambda s: s["距离商铺_km"])

print("\n=== 距离商铺最近的10个站 ===")
for s in stations_sorted[:10]:
    print(f"  {s['名称'][:30]:<30} {s['距离商铺_km']:>6.2f}km  [{s['品牌']}]")

# 乌兰花镇内（5km范围）
town_stations = [s for s in stations if s["距离商铺_km"] <= 5]
print(f"\n=== 乌兰花镇内(5km)站点: {len(town_stations)}个 ===")

# 周边竞争分析
print(f"\n=== 高油房路周边竞争分析 ===")
for radius, label in [(0.5, "500m"), (1, "1km"), (2, "3km"), (5, "5km")]:
    count = sum(1 for s in stations if s["距离商铺_km"] <= radius)
    print(f"  {label}范围内: {count}个充电站")

# 有电话的站点
with_phone = [s for s in stations if s.get("电话")]
print(f"\n=== 有联系电话的站点: {len(with_phone)}个 ===")
# 有评分的站点
with_rating = [s for s in stations if s.get("评分") and s["评分"] != "[]"]
print(f"有评分的站点: {len(with_rating)}个")
if with_rating:
    ratings = [float(s["评分"]) for s in with_rating]
    print(f"评分范围: {min(ratings):.1f} ~ {max(ratings):.1f}, 平均: {sum(ratings)/len(ratings):.1f}")

# ========== 4. 输出JSON供地图使用 ==========
stations_json = []
for s in stations:
    stations_json.append({
        "name": s["名称"],
        "address": s["地址"],
        "lng": s["经度_f"],
        "lat": s["纬度_f"],
        "brand": s["品牌"],
        "distance": s["距离商铺_km"],
        "tel": s.get("电话", ""),
        "rating": s.get("评分", ""),
        "photos": s.get("照片", "")[:100] if s.get("照片") else "",
    })

with open(OUT_DIR + "stations_data.json", "w", encoding="utf-8") as f:
    json.dump(stations_json, f, ensure_ascii=False, indent=2)
print(f"\n✅ 分析数据已保存: stations_data.json")

# ========== 5. 输出分析报告文本 ==========
report = f"""
# 四子王旗充电站POI数据分析报告

> 生成时间: 2026-05-05
> 数据来源: 高德地图Web服务API
> 商铺位置: 高油房路南侧（估算坐标: {SHOP_LON}, {SHOP_LAT}）

## 一、基础统计

| 指标 | 数值 |
|------|:----:|
| POI总记录数（含重复） | {len(rows)} |
| 去重后站点数 | {len(stations)} |
| 乌兰花镇内(5km)站点 | {len(town_stations)} |
| 有联系电话的站点 | {len(with_phone)} |
| 有评分的站点 | {len(with_rating)} |

## 二、品牌分布

| 品牌 | 数量 | 占比 |
|-----|:---:|:----:|
"""
for b, c in brand_count.most_common():
    pct = c / len(stations) * 100
    report += f"| {b} | {c} | {pct:.0f}% |\n"

report += f"""
## 三、高油房路周边竞争分析

| 半径 | 充电站数量 |
|:----:|:---------:|
| 500m | {sum(1 for s in stations if s['距离商铺_km'] <= 0.5)} |
| 1km | {sum(1 for s in stations if s['距离商铺_km'] <= 1)} |
| 3km | {sum(1 for s in stations if s['距离商铺_km'] <= 3)} |
| 5km | {sum(1 for s in stations if s['距离商铺_km'] <= 5)} |

## 四、距商铺最近的充电站

| 排名 | 站名 | 距离 | 品牌 |
|:---:|------|:----:|:----:|
"""
for i, s in enumerate(stations_sorted[:10], 1):
    report += f"| {i} | {s['名称'][:40]} | {s['距离商铺_km']:.2f}km | {s['品牌']} |\n"

with open(OUT_DIR + "数据分析报告.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"✅ 分析报告已保存: 数据分析报告.md")
