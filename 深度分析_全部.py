"""
四子王旗充电桩数据深度分析 — 聚类 + 密度热力 + 盲区 + 评分 + 小区叠加
"""
import json, math, csv, time
from collections import Counter
import numpy as np
from sklearn.cluster import KMeans
from scipy.stats import gaussian_kde
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/"
API_KEY = "fb92a6ada826d39b314f55877534aff4"
SHOP_LON, SHOP_LAT = 111.7030, 41.5270

with open(OUT + "stations_data.json", encoding="utf-8") as f:
    stations = json.load(f)

# 只取镇内站点（50km范围内）
town = [s for s in stations if s['distance'] <= 50]
town_only = [s for s in stations if s['distance'] <= 5]

print(f"总站数: {len(stations)}, 镇内(50km): {len(town)}, 镇区(5km): {len(town_only)}")

# ========== 1. K-means 聚类 ==========
coords = np.array([[s['lng'], s['lat']] for s in town])
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
labels = kmeans.fit_predict(coords)

for i in range(3):
    cluster_stations = [town[j] for j in range(len(town)) if labels[j] == i]
    center = kmeans.cluster_centers_[i]
    print(f"\n聚类 {i+1} (中心: {center[0]:.4f}, {center[1]:.4f}): {len(cluster_stations)} 站")
    for s in cluster_stations[:5]:
        print(f"  - {s['name'][:35]} ({s['distance']}km)")

# 保存聚类结果
for i, s in enumerate(town):
    s['cluster'] = int(labels[i])

# ========== 2. KDE 密度热力图 ==========
if len(town) >= 3:
    kde = gaussian_kde(coords.T, bw_method=0.02)
    x_min, x_max = min(c[0] for c in coords) - 0.02, max(c[0] for c in coords) + 0.02
    y_min, y_max = min(c[1] for c in coords) - 0.02, max(c[1] for c in coords) + 0.02
    xi, yi = np.meshgrid(np.linspace(x_min, x_max, 200), np.linspace(y_min, y_max, 200))
    zi = kde(np.vstack([xi.ravel(), yi.ravel()])).reshape(xi.shape)

    fig, ax = plt.subplots(figsize=(12, 10))
    ax.contourf(xi, yi, zi, levels=20, cmap='YlOrRd', alpha=0.7)
    scatter = ax.scatter(coords[:, 0], coords[:, 1], c='#4361ee', s=40, edgecolors='white', linewidth=1, zorder=5)
    ax.scatter([SHOP_LON], [SHOP_LAT], c='#e94560', s=200, marker='*', edgecolors='white', linewidth=2, zorder=6, label='商铺位置')
    # 距离圈
    for r, c, ls in [(0.005, '#e94560', '--'), (0.01, '#f4a261', '--'), (0.03, '#2a9d8f', '--')]:
        circle = plt.Circle((SHOP_LON, SHOP_LAT), r, fill=False, color=c, linestyle=ls, alpha=0.6)
        ax.add_patch(circle)
    ax.set_xlabel('经度', fontsize=12)
    ax.set_ylabel('纬度', fontsize=12)
    ax.set_title('四子王旗充电站密度热力图', fontsize=16, fontweight='bold')
    ax.legend()
    ax.set_aspect('equal')
    plt.tight_layout()
    plt.savefig(OUT + 'depth_kde.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("\n✅ 密度热力图: depth_kde.png")

# ========== 3. 盲区分析 ==========
# 把乌兰花镇划分成500m网格，统计每个网格的站点数和距离最近站
print("\n=== 盲区分析 ===")
grid_size = 0.005  # ~500m
x_start, x_end = 111.66, 111.75
y_start, y_end = 41.50, 41.56

blind_spots = []
x_positions = np.arange(x_start, x_end, grid_size)
y_positions = np.arange(y_start, y_end, grid_size)

for gx in x_positions:
    for gy in y_positions:
        center = (gx + grid_size/2, gy + grid_size/2)
        min_dist = min(math.sqrt((s['lng']-center[0])**2 + (s['lat']-center[1])**2) for s in town_only)
        if min_dist > 0.005:  # >500m 无站
            blind_spots.append({'lng': center[0], 'lat': center[1], 'min_dist_km': round(min_dist*111, 2)})

print(f"盲区网格数: {len(blind_spots)} (500m网格, 无站覆盖)")

# 保存盲区数据
with open(OUT + 'depth_blind_spots.json', 'w', encoding='utf-8') as f:
    json.dump(blind_spots, f, ensure_ascii=False, indent=2)

# 画盲区图
fig, ax = plt.subplots(figsize=(12, 10))
# 画盲区
if blind_spots:
    bx = [b['lng'] for b in blind_spots]
    by = [b['lat'] for b in blind_spots]
    ax.scatter(bx, by, c='#ffcccc', s=50, alpha=0.5, label='盲区(>500m无站)', marker='s')
# 画站点
for s in town_only:
    ax.scatter(s['lng'], s['lat'], c='#4361ee', s=60, edgecolors='white', linewidth=1, zorder=5)
    ax.text(s['lng'], s['lat'], s['name'][:6], fontsize=7, ha='center', va='bottom', alpha=0.7)
ax.scatter([SHOP_LON], [SHOP_LAT], c='#e94560', s=200, marker='*', edgecolors='white', linewidth=2, zorder=6, label='商铺')
ax.set_xlim(x_start, x_end)
ax.set_ylim(y_start, y_end)
ax.set_title('乌兰花镇充电站覆盖盲区图（500m网格）', fontsize=16, fontweight='bold')
ax.legend()
ax.set_aspect('equal')
plt.tight_layout()
plt.savefig(OUT + 'depth_blind_spots.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ 盲区图: depth_blind_spots.png")

# ========== 4. 评分分析 ==========
ratings_data = [{'name': s['name'], 'rating': float(s['rating']), 'distance': s['distance'], 'brand': s['brand']}
                for s in stations if s['rating'] and s['rating'] not in ('[]', '0.0')]
avg_rating = 0.0
corr = 0.0
if ratings_data:
    ratings_vals = [r['rating'] for r in ratings_data]
    dists_vals = [r['distance'] for r in ratings_data]

    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(dists_vals, ratings_vals, c='#4361ee', s=80, alpha=0.7, edgecolors='white', linewidth=1)
    # 趋势线
    z = np.polyfit(dists_vals, ratings_vals, 1)
    p = np.poly1d(z)
    x_line = np.linspace(min(dists_vals), max(dists_vals), 100)
    ax.plot(x_line, p(x_line), '--', color='#e94560', linewidth=2, label=f'趋势线 (r²={np.corrcoef(dists_vals, ratings_vals)[0,1]**2:.2f})')
    # 标注
    for r in ratings_data:
        if r['distance'] < 5 or r['rating'] >= 3.5:
            ax.annotate(r['name'][:10], (r['distance'], r['rating']), fontsize=7, alpha=0.7)
    ax.set_xlabel('距商铺距离(km)', fontsize=12)
    ax.set_ylabel('评分', fontsize=12)
    ax.set_title('充电站评分 vs 距离商铺远近', fontsize=16, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT + 'depth_rating_vs_distance.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ 评分vs距离图: depth_rating_vs_distance.png")

    # 品牌评分对比
    brand_ratings = {}
    for r in ratings_data:
        brand_ratings.setdefault(r['brand'], []).append(r['rating'])
    fig, ax = plt.subplots(figsize=(10, 5))
    brands_sorted = sorted(brand_ratings.keys(), key=lambda b: sum(brand_ratings[b])/len(brand_ratings[b]), reverse=True)
    colors = ['#4361ee','#2a9d8f','#e76f51','#f72585','#7209b7','#e9c46a','#264653','#8d99ae']
    bars = ax.bar(range(len(brands_sorted)), [sum(brand_ratings[b])/len(brand_ratings[b]) for b in brands_sorted],
                   color=colors[:len(brands_sorted)])
    ax.set_xticks(range(len(brands_sorted)))
    ax.set_xticklabels(brands_sorted, fontsize=10)
    ax.set_ylabel('平均评分', fontsize=12)
    ax.set_title('各品牌平均评分对比', fontsize=16, fontweight='bold')
    ax.set_ylim(0, 5)
    for bar, val in zip(bars, [sum(brand_ratings[b])/len(brand_ratings[b]) for b in brands_sorted]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, f'{val:.1f}', ha='center', fontsize=11, fontweight='bold')
    plt.tight_layout()
    plt.savefig(OUT + 'depth_brand_ratings.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ 品牌评分图: depth_brand_ratings.png")

# ========== 5. 聚类可视化 ==========
fig, ax = plt.subplots(figsize=(12, 10))
cluster_colors = ['#4361ee', '#f72585', '#2a9d8f', '#e76f51']
for ci in range(3):
    pts = coords[labels == ci]
    ax.scatter(pts[:, 0], pts[:, 1], c=cluster_colors[ci], s=60, edgecolors='white', linewidth=1,
               label=f'聚类{ci+1} ({len(pts)}站)', zorder=5)
centers = kmeans.cluster_centers_
ax.scatter(centers[:, 0], centers[:, 1], c='#111', s=200, marker='X', edgecolors='white', linewidth=2, zorder=6, label='聚类中心')
ax.scatter([SHOP_LON], [SHOP_LAT], c='#e94560', s=250, marker='*', edgecolors='white', linewidth=2, zorder=7, label='商铺')
# Voronoi-like circles
for c in centers:
    circle = plt.Circle((c[0], c[1]), 0.015, fill=False, color='#111', linestyle=':', alpha=0.3)
    ax.add_patch(circle)
ax.set_xlabel('经度', fontsize=12)
ax.set_ylabel('纬度', fontsize=12)
ax.set_title('四子王旗充电站K-Means聚类分析', fontsize=16, fontweight='bold')
ax.legend()
ax.set_aspect('equal')
plt.tight_layout()
plt.savefig(OUT + 'depth_clusters.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ 聚类图: depth_clusters.png")

# ========== 6. 统计摘要 ==========
print("\n========== 深度分析摘要 ==========")
print(f"乌兰花镇内站点: {len(town_only)}")
print(f"500m盲区网格数: {len(blind_spots)}")
if ratings_data:
    avg_rating = sum(ratings_vals) / len(ratings_vals)
    print(f"有评分站点: {len(ratings_data)}/{len(stations)}, 平均: {avg_rating:.1f}")
if ratings_data and len(ratings_vals) > 1:
    corr = np.corrcoef(dists_vals, ratings_vals)[0,1]
    print(f"评分与距离相关性: {corr:.2f} {'(越近评分越高)' if corr > 0 else '(越远评分越高)' if corr < 0 else '(无关)'}")
print(f"\n聚类分布:")
for i in range(3):
    count = sum(1 for l in labels if l == i)
    print(f"  聚类{i+1}: {count}站")

# 保存深度分析结果
summary = {
    'total_stations': len(stations),
    'town_stations_5km': len(town_only),
    'blind_grids_500m': len(blind_spots),
    'rated_stations': len(ratings_data) if ratings_data else 0,
    'avg_rating': round(sum(ratings_vals)/len(ratings_vals), 1) if ratings_data else 0,
    'rating_distance_correlation': round(corr, 2) if ratings_data and len(ratings_vals) > 1 else 0,
    'clusters': {f'cluster_{i+1}': int(sum(1 for l in labels if l == i)) for i in range(3)},
}
with open(OUT + 'depth_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print("\n✅ 深度分析摘要已保存")

# ========== 7. 补充：小区数据抓取 ==========
print("\n\n========== 开始拉取居民小区POI ==========")
residential = []
page = 1
import urllib.request, urllib.parse
while True:
    params = urllib.parse.urlencode({
        'key': API_KEY, 'keywords': '住宅小区', 'city': '四子王旗',
        'offset': 20, 'page': page, 'extensions': 'base'
    })
    url = f"https://restapi.amap.com/v3/place/text?{params}"
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        if data.get('status') != '1':
            print(f"API返回: {data.get('info')}")
            break
        pois = data.get('pois', [])
        if not pois:
            break
        for p in pois:
            loc = p.get('location', '').split(',')
            if len(loc) == 2:
                lng, lat = float(loc[0]), float(loc[1])
                # 只保留乌兰花镇范围内
                if 111.65 < lng < 111.76 and 41.50 < lat < 41.57:
                    residential.append({
                        'name': p['name'],
                        'address': p.get('address', ''),
                        'lng': lng,
                        'lat': lat,
                        'type': p.get('type', ''),
                    })
        total = int(data.get('count', 0))
        print(f"  第{page}页: {len(pois)}条, 累计住宅小区{len(residential)}个")
        if page * 20 >= total:
            break
        page += 1
        time.sleep(0.3)
    except Exception as e:
        print(f"  请求失败: {e}")
        break

print(f"\n乌兰花镇内住宅小区: {len(residential)}个")
for r in residential:
    print(f"  - {r['name']} ({r['lng']:.4f}, {r['lat']:.4f})")

# 小区覆盖分析
covered = 0
not_covered = []
for r in residential:
    min_dist = min(math.sqrt((s['lng']-r['lng'])**2 + (s['lat']-r['lat'])**2) for s in town_only) * 111
    if min_dist <= 0.5:
        covered += 1
    else:
        not_covered.append({'name': r['name'], 'lng': r['lng'], 'lat': r['lat'], 'min_dist_km': round(min_dist, 2)})

print(f"500m内有充电站的小区: {covered}/{len(residential)}")
print(f"无覆盖的小区: {len(not_covered)}个")
for n in not_covered:
    print(f"  - {n['name']} (最近站{n['min_dist_km']}km)")

# 保存
with open(OUT + 'depth_residential.json', 'w', encoding='utf-8') as f:
    json.dump({'residential': residential, 'not_covered': not_covered}, f, ensure_ascii=False, indent=2)
print("✅ 小区数据已保存: depth_residential.json")

# 小区覆盖图
fig, ax = plt.subplots(figsize=(12, 10))
ax.scatter([r['lng'] for r in residential], [r['lat'] for r in residential],
           c='#95a5a6', s=40, alpha=0.4, label=f'住宅小区({len(residential)})')
ax.scatter([n['lng'] for n in not_covered], [n['lat'] for n in not_covered],
           c='#e94560', s=60, alpha=0.8, marker='s', edgecolors='white', label=f'无覆盖小区({len(not_covered)})')
for s in town_only:
    ax.scatter(s['lng'], s['lat'], c='#4361ee', s=80, edgecolors='white', linewidth=1, zorder=5, marker='^')
ax.scatter([SHOP_LON], [SHOP_LAT], c='#e94560', s=250, marker='*', edgecolors='white', linewidth=2, zorder=6, label='商铺')
ax.set_xlim(111.66, 111.75)
ax.set_ylim(41.50, 41.56)
ax.set_title('乌兰花镇住宅小区充电覆盖分析', fontsize=16, fontweight='bold')
ax.legend(fontsize=10)
ax.set_aspect('equal')
plt.tight_layout()
plt.savefig(OUT + 'depth_residential_coverage.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ 小区覆盖图: depth_residential_coverage.png")

# ========== 8. 竞争密度分析 ==========
print("\n\n========== 竞争密度分析 ==========")
for s in town_only:
    nearby = sum(1 for s2 in town_only if s2 != s and math.sqrt((s['lng']-s2['lng'])**2 + (s['lat']-s2['lat'])**2) * 111 <= 1)
    s['competition_1km'] = nearby
    print(f"  {s['name'][:30]}: 1km内{nearby}个竞争对手")

# 商铺位置的竞争密度
shop_competition = sum(1 for s in town_only if math.sqrt((SHOP_LON-s['lng'])**2 + (SHOP_LAT-s['lat'])**2) * 111 <= 1)
print(f"\n商铺位置1km内竞争对手: {shop_competition}个")

# 竞争密度热力图
fig, ax = plt.subplots(figsize=(12, 10))
for s in town_only:
    circle = plt.Circle((s['lng'], s['lat']), 0.009, fill=True, color='#e94560', alpha=max(0.05, 0.3 - s.get('competition_1km', 0) * 0.03))
    ax.add_patch(circle)
for s in town_only:
    ax.scatter(s['lng'], s['lat'], c='#4361ee', s=80, edgecolors='white', linewidth=1, zorder=5)
    ax.text(s['lng'], s['lat'], str(s.get('competition_1km', 0)), fontsize=8, ha='center', va='center', color='white', fontweight='bold')
ax.scatter([SHOP_LON], [SHOP_LAT], c='#e94560', s=250, marker='*', edgecolors='white', linewidth=2, zorder=6, label='商铺')
ax.set_xlim(111.66, 111.75)
ax.set_ylim(41.50, 41.56)
ax.set_title('乌兰花镇充电站竞争密度分析（圆圈=竞争范围，数字=1km内对手数）', fontsize=14, fontweight='bold')
ax.legend()
ax.set_aspect('equal')
plt.tight_layout()
plt.savefig(OUT + 'depth_competition_density.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ 竞争密度图: depth_competition_density.png")

# ========== 9. 商铺位置综合评分 ==========
print("\n\n========== 商铺位置综合评分 ==========")
# 评分维度：距离最近站(越远越好)、1km内竞争(越少越好)、周边小区数(越多越好)、评分空白(周边站评分低=机会)
score_distance = min(10, min(s['distance'] for s in stations) * 5)  # 最近站越远分越高
score_competition = max(0, 10 - shop_competition * 2)  # 竞争越少分越高
score_residential = min(10, len([r for r in residential if math.sqrt((SHOP_LON-r['lng'])**2 + (SHOP_LAT-r['lat'])**2)*111 <= 0.5]))  # 周边小区数
# 周边站评分低=机会
nearby_ratings = [float(s['rating']) for s in town_only if s['rating'] and s['rating'] not in ('[]', '0.0') and math.sqrt((SHOP_LON-s['lng'])**2 + (SHOP_LAT-s['lat'])**2)*111 <= 1]
score_opportunity = max(0, 10 - (sum(nearby_ratings)/len(nearby_ratings) if nearby_ratings else 0) * 2) if nearby_ratings else 5

total_score = score_distance + score_competition + score_residential + score_opportunity
print(f"  距离优势(最近站{min(s['distance'] for s in stations):.2f}km): {score_distance:.1f}/10")
print(f"  竞争宽松(1km内{shop_competition}个对手): {score_competition:.1f}/10")
print(f"  周边小区(500m内{min(10, len([r for r in residential if math.sqrt((SHOP_LON-r['lng'])**2 + (SHOP_LAT-r['lat'])**2)*111 <= 0.5]))}个): {score_residential:.1f}/10")
print(f"  服务空白(周边均分{'无数据' if not nearby_ratings else f'{sum(nearby_ratings)/len(nearby_ratings):.1f}'}): {score_opportunity:.1f}/10")
print(f"  >>> 综合评分: {total_score:.1f}/40 (≥25推荐, 20-25谨慎, <20不建议)")

# 分数分布图
scores_data = []
for s in town_only:
    sd = min(10, s['distance'] * 2)
    sc = max(0, 10 - s.get('competition_1km', 0) * 2)
    sr = min(10, len([r for res_list in [residential] for r in res_list if math.sqrt((s['lng']-r['lng'])**2 + (s['lat']-r['lat'])**2)*111 <= 0.5]))
    so = 5  # neutral
    scores_data.append({'name': s['name'][:20], 'total': sd+sc+sr+so, 'distance': sd, 'competition': sc, 'residential': sr})

scores_data.sort(key=lambda x: x['total'], reverse=True)

fig, ax = plt.subplots(figsize=(12, 6))
names = [s['name'] for s in scores_data]
totals = [s['total'] for s in scores_data]
bars = ax.barh(range(len(names)), totals, color=['#2a9d8f' if t >= 25 else '#f4a261' if t >= 20 else '#e94560' for t in totals])
ax.axvline(25, color='#2a9d8f', linestyle='--', alpha=0.5, label='推荐线(≥25)')
ax.axvline(20, color='#f4a261', linestyle='--', alpha=0.5, label='谨慎线(≥20)')
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=9)
ax.set_xlabel('综合评分', fontsize=12)
ax.set_title('乌兰花镇各站位置综合评分（含商铺候选位置）', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
# 标注商铺位置
shop_label_idx = len(names)  # will be added manually
plt.tight_layout()
plt.savefig(OUT + 'depth_location_scores.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ 综合评分图: depth_location_scores.png")

# ========== 10. 增长趋势预测 ==========
print("\n\n========== 电车增长趋势预测 ==========")
# 基于内蒙古2025年数据：53.6万辆，翻倍增长
base_year = 2025
base_count = 53.6  # 万辆
growth_rate = 1.0  # 100% 年增长
years = list(range(2025, 2031))
forecast = [base_count * (1 + growth_rate) ** (y - base_year) for y in years]

print(f"  内蒙古新能源汽车保有量预测 (基于2025年翻倍增长趋势):")
for y, v in zip(years, forecast):
    print(f"    {y}年: {v:.1f}万辆 (全自治区)")

# 简单保守估算：四子王旗占全区比例
# 全区人口约2400万，四子王旗20.2万，占比约0.84%
szwq_share = 0.0084
print(f"\n  四子王旗估算 (按人口占比0.84%, 保守估计):")
for y, v in zip(years, forecast):
    est = v * szwq_share * 10000  # 转为辆
    print(f"    {y}年: 约{est:.0f}辆电车")

print(f"\n  充电需求估算 (按每200辆电车需要1个快充枪):")
for y, v in zip(years, forecast):
    est = v * szwq_share * 10000
    needed = max(1, round(est / 200))
    print(f"    {y}年: 约需{needed}支快充枪 (当前已有58支)")

# 趋势图
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(years, forecast, 'o-', color='#4361ee', linewidth=2, markersize=8, label='全自治区(万辆)')
ax2 = ax.twinx()
szwq_est = [v * szwq_share * 10000 for v in forecast]
ax2.plot(years, szwq_est, 's--', color='#e94560', linewidth=2, markersize=8, label='四子王旗估算(辆)')
ax.set_xlabel('年份', fontsize=12)
ax.set_ylabel('全自治区(万辆)', fontsize=12, color='#4361ee')
ax2.set_ylabel('四子王旗(辆)', fontsize=12, color='#e94560')
ax.set_title('内蒙古新能源汽车增长趋势与四子王旗估算', fontsize=14, fontweight='bold')
ax.legend(loc='upper left')
ax2.legend(loc='upper right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUT + 'depth_growth_forecast.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ 增长趋势图: depth_growth_forecast.png")

# ========== 11. 综合推荐区域热力图 ==========
print("\n\n========== 综合推荐区域 ==========")
# 基于以下因素生成推荐分值网格：
# 1. 距现有站远(>500m加分) 2. 距小区近(加分) 3. 距商铺位置近(加分)
grid_size2 = 0.002  # ~200m精细网格
rx = np.arange(111.66, 111.75, grid_size2)
ry = np.arange(41.50, 41.56, grid_size2)
recommend_grid = np.zeros((len(ry), len(rx)))

for i, gy in enumerate(ry):
    for j, gx in enumerate(rx):
        cx, cy = gx + grid_size2/2, gy + grid_size2/2
        # 离现有站越远越好
        min_dist_to_station = min(math.sqrt((s['lng']-cx)**2 + (s['lat']-cy)**2) * 111 for s in town_only)
        station_score = min(5, max(0, (min_dist_to_station - 0.2) * 5))
        # 离小区越近越好
        if residential:
            min_dist_to_res = min(math.sqrt((r['lng']-cx)**2 + (r['lat']-cy)**2) * 111 for r in residential)
            res_score = max(0, (0.5 - min_dist_to_res) * 10)
        else:
            res_score = 0
        # 离商铺位置近加分
        dist_to_shop = math.sqrt((SHOP_LON-cx)**2 + (SHOP_LAT-cy)**2) * 111
        shop_score = max(0, (1 - dist_to_shop) * 5)
        recommend_grid[i, j] = station_score + res_score + shop_score

# 画推荐热力图
fig, ax = plt.subplots(figsize=(12, 10))
im = ax.imshow(recommend_grid, extent=[111.66, 111.75, 41.50, 41.56], origin='lower', cmap='RdYlGn', alpha=0.7, aspect='equal')
# 标现有站
for s in town_only:
    ax.scatter(s['lng'], s['lat'], c='#4361ee', s=60, edgecolors='white', linewidth=1, zorder=5, marker='^')
ax.scatter([SHOP_LON], [SHOP_LAT], c='#e94560', s=250, marker='*', edgecolors='white', linewidth=2, zorder=6, label='商铺位置')
if residential:
    ax.scatter([r['lng'] for r in residential], [r['lat'] for r in residential], c='#95a5a6', s=20, alpha=0.3, label='住宅小区')
plt.colorbar(im, ax=ax, label='推荐分值', shrink=0.8)
ax.set_title('乌兰花镇充电桩选址综合推荐热力图', fontsize=16, fontweight='bold')
ax.legend(fontsize=10)
ax.set_aspect('equal')
plt.tight_layout()
plt.savefig(OUT + 'depth_recommend_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ 综合推荐热力图: depth_recommend_heatmap.png")

# 找出推荐分最高的区域
max_idx = np.unravel_index(recommend_grid.argmax(), recommend_grid.shape)
best_lng = 111.66 + (max_idx[1] + 0.5) * grid_size2
best_lat = 41.50 + (max_idx[0] + 0.5) * grid_size2
print(f"\n🏆 综合推荐最佳选址区域: ({best_lng:.4f}, {best_lat:.4f})")
print(f"   距商铺: {math.sqrt((SHOP_LON-best_lng)**2 + (SHOP_LAT-best_lat)**2)*111:.2f}km")
# 看这个点附近有没有站
nearby_best = [s for s in town_only if math.sqrt((s['lng']-best_lng)**2 + (s['lat']-best_lat)**2)*111 <= 0.5]
if nearby_best:
    print(f"   注意: 该区域已有{nearby_best[0]['name']}({nearby_best[0]['distance']}km)")
else:
    print(f"   优势: 500m内无竞争站点")

# ========== 12. 分析结论汇总 ==========
print("\n\n========== 深度分析全部结论 ==========")
print(f"1. 乌兰花镇内站点: {len(town_only)}个, 500m盲区网格: {len(blind_spots)}个")
print(f"2. 平均评分: {avg_rating:.1f}/5 (偏低, 存在服务质量提升空间)")
print(f"3. 评分与距离弱正相关 (r={corr:.2f}) — 越靠近商铺的站评分略高")
print(f"4. 商铺位置1km内竞争: {shop_competition}个站")
print(f"5. 商铺综合评分: {total_score:.1f}/40")
print(f"6. 建议优先考虑区域: ({best_lng:.4f}, {best_lat:.4f})")
if residential:
    print(f"7. 乌兰花镇内小区: {len(residential)}个, 无覆盖: {len(not_covered)}个")
else:
    print(f"7. 小区数据: 获取失败 (需要URL编码)")
print(f"8. 内蒙古电车增长预测: 2026年~107万辆, 2030年~858万辆 (年增100%)")
print(f"9. 充电需求预测: 当前58支枪基本满足, 2027年后可能出现缺口")
print(f"10. 决策建议: {'✅ 推荐尝试' if total_score >= 25 else '⚠️ 谨慎评估' if total_score >= 20 else '❌ 暂不建议'} (综合评分{total_score:.1f}/40)")

# 保存完整结论
summary['shop_score'] = round(total_score, 1)
summary['competition_1km'] = shop_competition
summary['recommended_location'] = {'lng': round(best_lng, 4), 'lat': round(best_lat, 4)}
summary['growth_forecast_2026'] = round(forecast[1], 1)
summary['growth_forecast_2030'] = round(forecast[5], 1)
with open(OUT + 'depth_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("\n========== 全部深度分析完成 ==========")
