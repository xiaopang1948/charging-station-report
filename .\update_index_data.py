"""Update all hardcoded analysis data in index.html from regenerated JSON files."""
import json, re

path = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/"

# Read regenerated data
with open(path + "depth_summary_v2.json", encoding="utf-8") as f:
    v2 = json.load(f)
with open(path + "depth_cost_analysis.json", encoding="utf-8") as f:
    cost = json.load(f)
with open(path + "stations_data.json", encoding="utf-8") as f:
    stations = json.load(f)
with open(path + "depth_residential.json", encoding="utf-8") as f:
    res = json.load(f)
    res_data = res["residential"]
    not_covered = res.get("not_covered", [])

with open(path + "depth_summary.json", encoding="utf-8") as f:
    summary = json.load(f)

# Calculate derived values
total_residential = len(res_data)
covered_500m = total_residential - len(not_covered)
coverage_pct = round(covered_500m / total_residential * 100, 1) if total_residential else 0

# Nearest stations sorted by distance
nearby = sorted(stations, key=lambda s: s["distance"])[:6]

# Station scenario mapping (based on name/address keywords)
def guess_scenario(s):
    name_addr = (s["name"] + " " + (s.get("address") or "")).lower()
    if any(k in name_addr for k in ["酒店", "宾馆", "旅游"]):
        return "酒店旅游"
    if any(k in name_addr for k in ["公园", "博物", "广场"]):
        return "公共服务"
    if any(k in name_addr for k in ["小区", "住宅", "民生", "新村", "花园", "泰和"]):
        return "住区过夜"
    if any(k in name_addr for k in ["政府", "供电", "公司", "办公", "市场", "就业", "政务", "税务"]):
        return "办公通勤"
    if any(k in name_addr for k in ["高速", "服务区"]):
        return "高速物流"
    if any(k in name_addr for k in ["美食", "购物", "商城"]):
        return "商圈日间"
    return "其他"

# Scenario colors
scenario_colors = {
    "办公通勤": "#059669", "住区过夜": "#16a34a", "公共服务": "#6ee7b7",
    "酒店旅游": "#d97706", "商圈日间": "#dc2626", "高速物流": "#ca8a04",
    "其他": "#8d99ae"
}

brand_tags = {
    "蒙电e充": "var(--accent)", "星星充电": "#dc2626", "蒙来电": "#7209b7",
    "蒙马(高速)": "#d97706", "咔咔电姆": "#16a34a", "驴充充": "#ca8a04",
    "云快充": "#1c1917", "其他": "#8d99ae"
}

# Read index.html
with open(path + "index.html", encoding="utf-8") as f:
    html = f.read()

changes = 0

# 1. Header score
old = '综合评分 71/100'
new = f'综合评分 {v2["shop_score_v2"]:.0f}/100'
if old in html:
    html = html.replace(old, new)
    changes += 1

# 2. 500m competitor count - still 1
# 3. Coverage
old = '55.5%'
new = f'{coverage_pct}%'
if old in html:
    html = html.replace(old, new, 1)  # only first occurrence
    changes += 1

# 4. Score in kpi bar
old = '>71</div><div class="l">v2综合评分'
new = f'>{v2["shop_score_v2"]:.0f}</div><div class="l">v2综合评分'
if old in html:
    html = html.replace(old, new)
    changes += 1

# 5. Metrics section
html = html.replace(
    '>71</div><div class="ml">综合评分 (旧版51)',
    f'>{v2["shop_score_v2"]:.1f}</div><div class="ml">综合评分 (旧版51)'
)
html = html.replace(
    '>16.3</div><div class="ml">需求缺口',
    f'>{v2["dim_gap"]}</div><div class="ml">需求缺口'
)
html = html.replace(
    '>14.7</div><div class="ml">成本效益',
    f'>{v2["dim_cost"]}</div><div class="ml">成本效益'
)
html = html.replace(
    '>+20</div><div class="ml">较旧版提升',
    f'>+{v2["shop_score_v2"] - 51:.0f}</div><div class="ml">较旧版提升'
)

# 6. Cost model description text - update coverage numbers
install_cost = v2["shop_install_cost"]
user_cost = v2["shop_user_cost"]
total_cost = v2["shop_total_cost"]
coverage_1km = v2["shop_coverage_1km"]
old_cost_text = f'Min(安装成本46,469元 + 用户到达成本2,599元)，1km覆盖91个小区(55.5%)'
new_cost_text = f'Min(安装成本{install_cost:,}元 + 用户到达成本{user_cost:,}元)，1km覆盖{coverage_1km}个小区({coverage_pct}%)'
html = html.replace(old_cost_text, new_cost_text)

# 7. Banner text - score improvement
html = html.replace(
    '评分提升20分，从"谨慎"升级到"中等偏上"',
    f'评分提升{v2["shop_score_v2"] - 51:.0f}分，从"谨慎"升级到"中等偏上"'
)
html = html.replace(
    '<span class="big">71</span>',
    f'<span class="big">{v2["shop_score_v2"]:.0f}</span>'
)

# 8. Nearest stations table (lines 401-406)
# Build new table rows
brand_tag_html = {
    "蒙电e充": 'style="background:var(--accent)"',
    "星星充电": 'style="background:#dc2626"',
    "蒙来电": 'style="background:#7209b7"',
    "蒙马(高速)": 'style="background:#d97706"',
    "咔咔电姆": 'style="background:#16a34a"',
    "驴充充": 'style="background:#ca8a04"',
    "云快充": 'style="background:#1c1917"',
    "其他": 'style="background:#8d99ae"'
}

rows = []
for i, s in enumerate(nearby, 1):
    rating = s.get("rating", "-")
    if rating in ("[]", "0.0", "") or not rating:
        rating = "-"
    scenario = guess_scenario(s)
    tag_style = brand_tag_html.get(s["brand"], 'style="background:#8d99ae"')
    rows.append(
        f'<tr><td>{i}</td><td><span class="tag" {tag_style}>{s["brand"]}</span></td>'
        f'<td>{s["name"]}</td><td>{s["distance"]}km</td>'
        f'<td>{rating}</td><td>{scenario}</td></tr>'
    )
new_table = '<table><tr><th>#</th><th>品牌</th><th>站名</th><th>距离</th><th>评分</th><th>充电场景</th></tr>' + ''.join(rows) + '</table>'

old_table_start = html.find('<table><tr><th>#</th><th>品牌</th><th>站名</th><th>距离</th><th>评分</th><th>充电场景</th></tr>')
old_table_end = html.find('</table>', old_table_start) + len('</table>') if old_table_start != -1 else -1
if old_table_start != -1 and old_table_end != -1:
    old_table = html[old_table_start:old_table_end]
    html = html.replace(old_table, new_table)
    changes += 1

# 9. Cost optimization table (lines 442-447)
# Shop row
shop = cost["shop"]
candidates = sorted(cost["candidates"], key=lambda c: c["rank"])[:4]

cand_rows = []
# Shop row first
coverage_rate_pct = round(shop["coverage_rate"] * 100, 1)
cand_rows.append(
    f'<tr><td><span class="tag" style="background:var(--danger)">商铺</span></td>'
    f'<td>高油房路（充电桩规划位）</td>'
    f'<td>{shop["total_cost"]:,}元</td>'
    f'<td>{shop["coverage_1km"]}</td>'
    f'<td>{coverage_rate_pct}%</td>'
    f'<td>{shop["score"]}</td></tr>'
)

# Generate candidate descriptions
cand_labels = [
    "商铺东北 1.8km（缺口热区）",
    "文化路北 1.8km",
    "滨河公园东 1.6km",
    "文化路北 2.1km",
]

for idx, c in enumerate(candidates):
    if idx < len(cand_labels):
        label = cand_labels[idx]
    else:
        label = f"({c['lng']:.4f}, {c['lat']:.4f})"
    cr_pct = round(c["coverage_rate"] * 100, 1)
    cand_rows.append(
        f'<tr><td>{c["rank"]}</td>'
        f'<td>{label}</td>'
        f'<td>{c["total_cost"]:,}元</td>'
        f'<td>{c["coverage_1km"]}</td>'
        f'<td>{cr_pct}%</td>'
        f'<td>{c["score"]}</td></tr>'
    )

new_cost_table = '<table><tr><th>排名</th><th>位置</th><th>总成本</th><th>1km内小区</th><th>覆盖率</th><th>综合分</th></tr>' + ''.join(cand_rows) + '</table>'

old_cost_start = html.find('排名</th><th>位置</th><th>总成本</th><th>1km内小区</th><th>覆盖率</th><th>综合分</th></tr>')
old_cost_start = html.rfind('<table>', 0, old_cost_start) if old_cost_start != -1 else -1
if old_cost_start != -1:
    old_cost_end = html.find('</table>', old_cost_start) + len('</table>')
    old_cost_table = html[old_cost_start:old_cost_end]
    html = html.replace(old_cost_table, new_cost_table)
    changes += 1

# 10. Update depth summary text in "深度分析" tab
# The shop周边 gap analysis text
html = html.replace(
    '500m内8个网格平均缺口31.7，需求77.0供给仅0.59',
    f'500m内8个网格平均缺口{v2["shop_gap_avg"]:.1f}，需求77.0供给仅0.59'
)

# Write back
with open(path + "index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"OK: index.html updated: {changes} sections modified")
print(f"   New score: {v2['shop_score_v2']:.1f}/100")
print(f"   Coverage: {coverage_pct}%")
print(f"   Nearest: {nearby[0]['distance']}km ({nearby[0]['name'][:30]}...)")
