"""
生成数据分析图表
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import json
import numpy as np
from collections import Counter

# 用中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUT_DIR = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/"

with open(OUT_DIR + "stations_data.json", encoding="utf-8") as f:
    stations = json.load(f)

# ===== 1. 品牌分布饼图 =====
brand_count = Counter(s['brand'] for s in stations)
labels = [f"{b}\n({c}个)" for b, c in brand_count.most_common()]
sizes = [c for _, c in brand_count.most_common()]
colors_pie = ['#4361ee', '#e76f51', '#2a9d8f', '#8d99ae', '#f72585', '#7209b7', '#e9c46a', '#264653']

fig, ax = plt.subplots(figsize=(8, 6))
wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors_pie[:len(sizes)],
                                   autopct='%1.0f%%', startangle=90, textprops={'fontsize': 11})
ax.set_title('四子王旗充电站品牌分布', fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(OUT_DIR + 'chart_brand_pie.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ chart_brand_pie.png")

# ===== 2. 距离分布柱状图 =====
dists = [s['distance'] for s in stations]
bins = [0, 0.5, 1, 2, 3, 5, 10, 20, 50, 100]
labels_hist = ['<0.5km', '0.5-1', '1-2', '2-3', '3-5', '5-10', '10-20', '20-50', '>50km']
counts = [sum(1 for d in dists if bins[i] <= d < bins[i+1]) for i in range(len(bins)-1)]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(range(len(counts)), counts, color=['#e63946', '#f4a261', '#2a9d8f', '#2a9d8f', '#264653', '#8d99ae', '#8d99ae', '#8d99ae', '#8d99ae'])
ax.set_xticks(range(len(counts)))
ax.set_xticklabels(labels_hist, fontsize=10)
ax.set_ylabel('站点数量', fontsize=12)
ax.set_title('充电站距离商铺的距离分布', fontsize=14, fontweight='bold')
# 在柱子上标数字
for bar, count in zip(bars, counts):
    if count > 0:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, str(count),
                ha='center', fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig(OUT_DIR + 'chart_distance_hist.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ chart_distance_hist.png")

# ===== 3. 评分分布 =====
ratings = [float(s['rating']) for s in stations if s['rating'] and s['rating'] != '[]']
if ratings:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(ratings, bins=10, color='#4361ee', alpha=0.7, edgecolor='white')
    ax.axvline(sum(ratings)/len(ratings), color='#e63946', linestyle='--', linewidth=2, label=f'平均 {sum(ratings)/len(ratings):.1f}')
    ax.set_xlabel('评分', fontsize=12)
    ax.set_ylabel('站点数', fontsize=12)
    ax.set_title('充电站评分分布', fontsize=14, fontweight='bold')
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUT_DIR + 'chart_rating_hist.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ chart_rating_hist.png")

# ===== 4. 累计距离曲线 =====
dists_sorted = sorted(dists)
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(dists_sorted, range(1, len(dists_sorted)+1), 'o-', color='#4361ee', markersize=4, linewidth=2)
ax.axvline(0.5, color='#e63946', linestyle=':', alpha=0.7, label='500m')
ax.axvline(1, color='#f4a261', linestyle=':', alpha=0.7, label='1km')
ax.axvline(5, color='#2a9d8f', linestyle=':', alpha=0.7, label='5km(镇区)')
ax.set_xlabel('距离商铺(km)', fontsize=12)
ax.set_ylabel('累计站点数', fontsize=12)
ax.set_title('累计充电站数量 vs 距离', fontsize=14, fontweight='bold')
ax.legend()
ax.set_xlim(0, max(dists_sorted)+1)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUT_DIR + 'chart_cumulative.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ chart_cumulative.png")

# ===== 5. 品牌距离箱线图 =====
brands_data = {}
for s in stations:
    b = s['brand']
    if b not in brands_data:
        brands_data[b] = []
    brands_data[b].append(s['distance'])

fig, ax = plt.subplots(figsize=(10, 5))
brand_names = list(brands_data.keys())
brand_dists = [brands_data[b] for b in brand_names]
colors_box = ['#4361ee', '#f72585', '#7209b7', '#e76f51', '#2a9d8f', '#e9c46a', '#264653', '#8d99ae']
bp = ax.boxplot(brand_dists, labels=brand_names, patch_artist=True)
for patch, color in zip(bp['boxes'], colors_box[:len(brand_names)]):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)
ax.set_ylabel('距离商铺(km)', fontsize=12)
ax.set_title('各品牌站点距离分布', fontsize=14, fontweight='bold')
ax.tick_params(axis='x', rotation=30)
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(OUT_DIR + 'chart_brand_distance.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ chart_brand_distance.png")

print("\n所有图表已生成!")
