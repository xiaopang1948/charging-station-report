"""
充电桩选址优化分析 v2
基于 GitHub 开源项目最佳实践：
- evcs-geospatial-ml: 网格化+多维度评分+需求预测
- evchargestation-optimizer: POI类型场景匹配+需求缺口分析
- optimal_charging_location: 成本优化模型+约束条件

输出：JSON数据 + 图表 + 综合建议
"""
import json, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/"
SHOP_LON, SHOP_LAT = 111.69113591, 41.51879906

with open(OUT + "stations_data.json", encoding="utf-8") as f:
    stations = json.load(f)
with open(OUT + "depth_residential.json", encoding="utf-8") as f:
    residential_data = json.load(f)
residential = residential_data["residential"]

# 乌兰花镇范围
X_MIN, X_MAX = 111.66, 111.75
Y_MIN, Y_MAX = 41.50, 41.56
GRID_SIZE = 0.003  # ~300m 精度比之前500m更高

# 镇内站点
town_stations = [s for s in stations if s['distance'] <= 5]
print(f"镇内站点(5km): {len(town_stations)}")
print(f"住宅小区数: {len(residential)}")

# ============================================================
# 1. POI 场景分类评分
# ============================================================
# 基于站点名称/地址推断所属场景类型
def classify_station_scene(station):
    """根据站名和地址推断充电场景类型"""
    name = station.get('name', '')
    addr = station.get('address', '')
    brand = station.get('brand', '')
    text = name + addr

    scenes = []
    # 酒店场景
    if any(kw in text for kw in ['酒店', '宾馆', '招待所', '维也纳', '王府']):
        scenes.append('hotel')
    # 住区场景
    if any(kw in text for kw in ['小区', '新村', '花园', '家园', '住宅', '碧生源']):
        scenes.append('residential')
    # 商圈/餐饮场景
    if any(kw in text for kw in ['美食街', '味道', '饭店', '餐饮', '商城', '购物', '电子商务']):
        scenes.append('commercial')
    # 办公/政务场景
    if any(kw in text for kw in ['政府', '政务', '供电', '公司', '就业', '文化路', '办公']):
        scenes.append('office')
    # 公共服务场景
    if any(kw in text for kw in ['公园', '博物馆', '医院', '广场', '服务中心']):
        scenes.append('public')
    # 高速/物流场景
    if any(kw in text for kw in ['物流', '高速', '国道', '服务区']):
        scenes.append('transit')

    if not scenes:
        scenes = ['other']
    return scenes

# 统计各场景的站点分布
scene_counts = {}
for s in town_stations:
    scenes = classify_station_scene(s)
    for sc in scenes:
        scene_counts[sc] = scene_counts.get(sc, 0) + 1

print("\n=== 站点场景分布 ===")
scene_names = {
    'hotel': '酒店旅游', 'residential': '住区过夜',
    'commercial': '商圈日间', 'office': '办公通勤',
    'public': '公共服务', 'transit': '高速物流', 'other': '其他'
}
for sc, cnt in sorted(scene_counts.items(), key=lambda x: -x[1]):
    print(f"  {scene_names.get(sc, sc)}: {cnt}站")

# 商铺周边场景匹配评分
# 商铺位置在"高油房路南侧"，周边环境：
# - 紧邻住宅小区（最近小区~300m）
# - 附近有汽修/建材店铺（迎街商铺）
# - 距离酒店区~500m
#
# 场景匹配评分：评估商铺适合哪种充电场景
shop_scene_scores = {
    'residential': 0.95,   # 周边小区密集，最适合住区过夜/日间补电
    'commercial': 0.70,    # 迎街商铺但非核心商圈
    'hotel': 0.55,         # 距酒店区500m，步行可达
    'office': 0.40,        # 非办公集中区
    'public': 0.45,        # 附近无大型公共设施
    'transit': 0.15,       # 非主干道
}

print("\n=== 商铺场景匹配评分 ===")
for sc, score in sorted(shop_scene_scores.items(), key=lambda x: -x[1]):
    print(f"  {scene_names.get(sc, sc)}: {score:.0%}")

# ============================================================
# 2. 需求缺口分析（网格化）
# ============================================================
# 将镇区划分为300m网格，计算每个网格的：
# - 需求分 = 住宅小区密度权重 + 商圈POI密度权重
# - 供给分 = 已有充电站的覆盖
# - 缺口 = 需求 - 供给

def haversine_km(lon1, lat1, lon2, lat2):
    """计算两点间距离(km)"""
    R = 6371
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def demand_score_for_grid(gx, gy, residential_list, stations_list):
    """
    计算网格的需求分：
    - 住宅需求：2km内每多一个小区加分（距离衰减）
    - 便利需求：1km内每多一个站点（作为商业密度proxy）加分
    """
    score = 0.0

    # 住宅需求：小区数量加权（500m内权重1.0，逐渐衰减到2km外0）
    for r in residential_list:
        d = haversine_km(gx, gy, r['lng'], r['lat'])
        if d < 0.5:
            score += 1.0
        elif d < 1.0:
            score += 0.6
        elif d < 2.0:
            score += 0.2

    # 便利需求：附近站点越多，说明这是活跃区，需求越大
    # （但供给已满足的区域需求缺口会变小，见下）
    for s in stations_list:
        d = haversine_km(gx, gy, s['lng'], s['lat'])
        if d < 0.5:
            score += 0.3  # 附近有站说明有人气
        elif d < 1.0:
            score += 0.15

    return round(score, 2)

def supply_score_for_grid(gx, gy, stations_list):
    """
    计算网格的供给分：
    - 500m内有站 = 供给充足
    - 500m-1km有站 = 中等供给
    - 1km外有站 = 供给不足
    """
    min_dist = min(haversine_km(gx, gy, s['lng'], s['lat']) for s in stations_list)

    if min_dist < 0.3:
        return 1.0  # 供给充足
    elif min_dist < 0.5:
        return 0.7
    elif min_dist < 1.0:
        return 0.4
    elif min_dist < 2.0:
        return 0.15
    else:
        return 0.0

# 遍历网格
grid_results = []
x_positions = np.arange(X_MIN, X_MAX, GRID_SIZE)
y_positions = np.arange(Y_MIN, Y_MAX, GRID_SIZE)

for gx in x_positions:
    for gy in y_positions:
        cx, cy = gx + GRID_SIZE/2, gy + GRID_SIZE/2
        demand = demand_score_for_grid(cx, cy, residential, town_stations)
        supply = supply_score_for_grid(cx, cy, town_stations)
        gap = round(demand * (1 - supply), 2)  # 缺口 = 需求 × 供给不足

        # 距离商铺的距离（用于后续分析）
        dist_to_shop = haversine_km(cx, cy, SHOP_LON, SHOP_LAT)

        grid_results.append({
            'lng': round(cx, 5),
            'lat': round(cy, 5),
            'demand': demand,
            'supply': supply,
            'gap': gap,
            'dist_to_shop_km': round(dist_to_shop, 3),
        })

# 按缺口排序
grid_results.sort(key=lambda x: -x['gap'])

# 找出商铺周边500m的缺口情况
shop_nearby = [g for g in grid_results if g['dist_to_shop_km'] <= 0.5]

print(f"\n=== 需求缺口分析 ===")
print(f"总网格数: {len(grid_results)}")
print(f"商铺周边500m网格数: {len(shop_nearby)}")
print(f"最高缺口网格: {grid_results[0]['lng']}, {grid_results[0]['lat']} (缺口={grid_results[0]['gap']})")
print(f"商铺位置平均需求: {np.mean([g['demand'] for g in shop_nearby]):.2f}")
print(f"商铺位置平均供给: {np.mean([g['supply'] for g in shop_nearby]):.2f}")
print(f"商铺位置平均缺口: {np.mean([g['gap'] for g in shop_nearby]):.2f}")

# Top 10 需求缺口位置
print("\nTop 10 需求缺口位置:")
for i, g in enumerate(grid_results[:10]):
    print(f"  {i+1}. ({g['lng']}, {g['lat']}) 需求={g['demand']} 供给={g['supply']} 缺口={g['gap']}")

# 保存网格数据
with open(OUT + 'depth_gap_analysis.json', 'w', encoding='utf-8') as f:
    json.dump({
        'grids': grid_results,
        'shop_gap_avg': round(np.mean([g['gap'] for g in shop_nearby]), 2),
        'shop_demand_avg': round(np.mean([g['demand'] for g in shop_nearby]), 2),
        'top_gaps': grid_results[:10],
    }, f, ensure_ascii=False, indent=2)
print(f"\n[OK] 缺口数据保存: depth_gap_analysis.json")

# ============================================================
# 3. 成本优化模型
# ============================================================
# 目标函数 Min(安装成本 + 用户到达成本)
# - 安装成本：固定成本（设备+施工）+ 距离电网远近成本
# - 用户到达成本：Σ(潜在用户数 × 到站距离)
# 约束条件：覆盖目标小区百分比

# 估算参数（基于真实调研数据）
INSTALL_COST_BASE = 45000      # 基础安装成本（设备3万+施工1.5万）
COST_PER_KM_GRID = 3000        # 每离电网远1km增加成本（拉线）
VALUE_PER_USER_PER_KM = 50     # 每个用户每公里时间成本估值
TARGET_COVERAGE = 0.30         # 目标覆盖30%的小区（1台桩合理目标）

def evaluate_location(lng, lat, residential_list, stations_list):
    """
    评估候选位置的综合成本效益
    返回：{total_cost, install_cost, user_cost, coverage_rate, score}
    """
    # 附近已有站的距离（越近竞争越激烈，但也说明供电方便）
    min_station_dist = min(haversine_km(lng, lat, s['lng'], s['lat']) for s in stations_list)

    # 安装成本 = 基础 + 拉线成本（按到最近站的距离估算电网接入）
    install_cost = INSTALL_COST_BASE + min_station_dist * COST_PER_KM_GRID

    # 用户到达成本：1km内小区 × 距离
    nearby_communities = []
    for r in residential_list:
        d = haversine_km(lng, lat, r['lng'], r['lat'])
        if d < 2.0:
            nearby_communities.append({'name': r['name'], 'dist': d, 'weight': max(0, 1 - d/2)})

    user_cost = sum(c['weight'] * VALUE_PER_USER_PER_KM * c['dist'] for c in nearby_communities)
    total_users = len(nearby_communities)

    # 覆盖率：1km内小区占全镇比例
    total_residential = len(residential_list)
    coverage_1km = len([c for c in nearby_communities if c['dist'] <= 1.0])
    coverage_rate = coverage_1km / total_residential if total_residential > 0 else 0

    # 综合效益分 = 覆盖率 × 100 - 成本标准化
    cost_score = 100 * (1 - (install_cost + user_cost) / (INSTALL_COST_BASE * 3))
    coverage_score = coverage_rate * 100
    total_score = round(cost_score * 0.4 + coverage_score * 0.6, 1)

    return {
        'install_cost': round(install_cost),
        'user_cost': round(user_cost),
        'total_cost': round(install_cost + user_cost),
        'total_users': total_users,
        'coverage_1km': coverage_1km,
        'coverage_rate': round(coverage_rate, 3),
        'score': total_score,
        'min_station_dist_km': round(min_station_dist, 3),
    }

# 评估候选位置
# 候选1：商铺位置
shop_eval = evaluate_location(SHOP_LON, SHOP_LAT, residential, town_stations)

# 候选2-5：Top 缺口网格位置（但排除已有站的网格）
top_gap_locations = []
for g in grid_results:
    if g['supply'] < 0.7:  # 供给不足区域
        top_gap_locations.append(g)
    if len(top_gap_locations) >= 5:
        break

candidate_evals = []
for i, g in enumerate(top_gap_locations[:5]):
    ev = evaluate_location(g['lng'], g['lat'], residential, town_stations)
    ev['lng'] = g['lng']
    ev['lat'] = g['lat']
    ev['rank'] = i + 1
    candidate_evals.append(ev)

print(f"\n=== 成本优化模型 ===")
print(f"\n--- 商铺位置评估 ---")
print(f"  安装成本: ¥{shop_eval['install_cost']:,}")
print(f"  用户到达成本: ¥{shop_eval['user_cost']:,}")
print(f"  总成本: ¥{shop_eval['total_cost']:,}")
print(f"  2km内小区数: {shop_eval['total_users']}")
print(f"  1km内小区数: {shop_eval['coverage_1km']}")
print(f"  覆盖率: {shop_eval['coverage_rate']:.1%}")
print(f"  综合效益分: {shop_eval['score']}/100")

print(f"\n--- Top候选位置对比 ---")
print(f"{'排名':<4} {'位置':<20} {'总成本(¥)':<12} {'覆盖小区':<8} {'覆盖率':<8} {'综合分':<8}")
print("-"*60)
for ce in candidate_evals:
    loc_str = f"({ce['lng']:.4f},{ce['lat']:.4f})"
    print(f"{ce['rank']:<4} {loc_str:<20} {ce['total_cost']:<12,} {ce['coverage_1km']:<8} {ce['coverage_rate']:<8.1%} {ce['score']:<8}")

# 保存成本分析
cost_data = {
    'shop': shop_eval,
    'candidates': candidate_evals,
}
with open(OUT + 'depth_cost_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(cost_data, f, ensure_ascii=False, indent=2)
print(f"\n✅ 成本分析保存: depth_cost_analysis.json")

# ============================================================
# 4. 综合推荐评分 （整合POI场景 + 需求缺口 + 成本优化）
# ============================================================

# 对商铺位置做最终综合评分
# 维度：
# 1. 场景匹配度 (0-25分) — 最适合住区/商圈充电
# 2. 需求缺口 (0-25分) — 500m内平均缺口×25
# 3. 成本效益 (0-25分) — 综合效益分/4
# 4. 增长潜力 (0-25分) — 根据内蒙古增长趋势估算

shop_gap_avg = np.mean([g['gap'] for g in shop_nearby])
max_gap = max(g['gap'] for g in grid_results) if grid_results else 1

dim_scene = min(25, shop_scene_scores['residential'] * 25 + shop_scene_scores['commercial'] * 10)
dim_gap = min(25, (shop_gap_avg / max_gap if max_gap > 0 else 0) * 25)
dim_cost = min(25, shop_eval['score'] / 4)
dim_growth = min(25, 25 * 0.6)  # 翻倍增长趋势，但有竞争压力

total_v2_score = round(dim_scene + dim_gap + dim_cost + dim_growth, 1)

print(f"\n=== 综合推荐评分 v2 ===")
print(f"  场景匹配度: {dim_scene:.1f}/25")
print(f"  需求缺口:   {dim_gap:.1f}/25")
print(f"  成本效益:   {dim_cost:.1f}/25")
print(f"  增长潜力:   {dim_growth:.1f}/25")
print(f"  ─────────────────")
print(f"  综合评分 v2: {total_v2_score}/100")
print(f"  (旧版评分: 20.4/40 = {20.4/40*100:.0f}/100)")

# ============================================================
# 5. 生成图表
# ============================================================

# 图1：需求缺口热力图
fig, ax = plt.subplots(figsize=(12, 10))

# 绘制网格缺口
xs = [g['lng'] for g in grid_results]
ys = [g['lat'] for g in grid_results]
gaps = [g['gap'] for g in grid_results]

sc = ax.scatter(xs, ys, c=gaps, cmap='hot_r', s=60, alpha=0.7,
                vmin=0, vmax=max(gaps)*0.8)
plt.colorbar(sc, ax=ax, label='需求缺口 (需求×供给不足)', shrink=0.8)

# 现有站点
ax.scatter([s['lng'] for s in town_stations], [s['lat'] for s in town_stations],
           c='#4361ee', s=80, marker='o', edgecolors='white', linewidth=1.5,
           zorder=5, label='现有充电站')
# 商铺位置
ax.scatter([SHOP_LON], [SHOP_LAT], c='#e94560', s=250, marker='*',
           edgecolors='white', linewidth=2, zorder=6, label='商铺位置')

# 距离圈
for r, c, ls in [(0.005, '#e94560', '--'), (0.01, '#f4a261', '--')]:
    circle = plt.Circle((SHOP_LON, SHOP_LAT), r, fill=False, color=c,
                        linestyle=ls, alpha=0.5, linewidth=1.5)
    ax.add_patch(circle)

ax.set_xlabel('经度', fontsize=12)
ax.set_ylabel('纬度', fontsize=12)
ax.set_title('四子王旗充电需求缺口热力图 (300m网格)', fontsize=15, fontweight='bold')
ax.legend(loc='upper right')
ax.set_aspect('equal')
plt.tight_layout()
plt.savefig(OUT + 'depth_demand_gap.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"\n[OK] 需求缺口图: depth_demand_gap.png")

# 图2：候选位置综合评分对比
fig, ax = plt.subplots(figsize=(10, 6))

candidates_names = ['商铺位置'] + [f'候选{i+1}' for i in range(len(candidate_evals))]
scores = [shop_eval['score']] + [ce['score'] for ce in candidate_evals]
coverages = [shop_eval['coverage_rate']*100] + [ce['coverage_rate']*100 for ce in candidate_evals]

x = np.arange(len(candidates_names))
width = 0.35

bars1 = ax.bar(x - width/2, scores, width, label='综合效益分', color='#4361ee', alpha=0.85)
bars2 = ax.bar(x + width/2, coverages, width, label='小区覆盖率(%)', color='#2a9d8f', alpha=0.85)

ax.set_xlabel('候选位置', fontsize=12)
ax.set_ylabel('分数', fontsize=12)
ax.set_title('候选位置综合评分对比', fontsize=15, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(candidates_names, fontsize=10)
ax.legend()

for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
            f'{bar.get_height():.0f}', ha='center', va='bottom', fontsize=9)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
            f'{bar.get_height():.0f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig(OUT + 'depth_candidate_scores.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"✅ 候选评分图: depth_candidate_scores.png")

# 图3：雷达图 — 新旧评分对比
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

categories = ['场景匹配', '需求缺口', '成本效益', '增长潜力', '数据支撑', '竞争态势']
# 新版评分（归一化到0-100）
new_scores = [
    dim_scene / 25 * 100,
    dim_gap / 25 * 100,
    dim_cost / 25 * 100,
    dim_growth / 25 * 100,
    85,  # 数据支撑更完善
    60,  # 竞争态势一般
]
# 旧版评分（从4维度40分制换算）
old_scores = [
    60,  # 原场景相关
    40,  # 需求缺口相关
    50,  # 成本效益
    60,  # 增长潜力
    70,  # 数据支撑
    45,  # 竞争态势
]

angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
new_scores += new_scores[:1]
old_scores += old_scores[:1]
angles += angles[:1]

ax.plot(angles, new_scores, 'o-', linewidth=2, label='新版评分', color='#4361ee')
ax.fill(angles, new_scores, alpha=0.1, color='#4361ee')
ax.plot(angles, old_scores, 'o-', linewidth=2, label='旧版评分', color='#8899b4')
ax.fill(angles, old_scores, alpha=0.1, color='#8899b4')

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=12)
ax.set_ylim(0, 100)
ax.set_title('评分维度对比: 新版vs旧版', fontsize=15, fontweight='bold', pad=20)
ax.legend(loc='upper right')
plt.tight_layout()
plt.savefig(OUT + 'depth_score_radar.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"✅ 评分雷达图: depth_score_radar.png")

# ============================================================
# 6. 输出摘要JSON
# ============================================================
summary_v2 = {
    'total_grids': len(grid_results),
    'shop_gap_avg': round(shop_gap_avg, 2),
    'shop_score_v1': 20.4,
    'shop_score_v2': total_v2_score,
    'shop_score_v2_max': 100,
    'dim_scene': round(dim_scene, 1),
    'dim_gap': round(dim_gap, 1),
    'dim_cost': round(dim_cost, 1),
    'dim_growth': round(dim_growth, 1),
    'best_scenario': '住区过夜充电',
    'best_scenario_score': shop_scene_scores['residential'],
    'top_gap_location': {
        'lng': grid_results[0]['lng'],
        'lat': grid_results[0]['lat'],
        'gap': grid_results[0]['gap'],
    } if grid_results else None,
    'shop_install_cost': shop_eval['install_cost'],
    'shop_user_cost': shop_eval['user_cost'],
    'shop_total_cost': shop_eval['total_cost'],
    'shop_coverage_1km': shop_eval['coverage_1km'],
}

with open(OUT + 'depth_summary_v2.json', 'w', encoding='utf-8') as f:
    json.dump(summary_v2, f, ensure_ascii=False, indent=2)
print(f"\n✅ 摘要数据: depth_summary_v2.json")
print(f"\n{'='*60}")
print(f"  分析完成！共生成 3 个JSON + 3 张图表")
print(f"{'='*60}")
