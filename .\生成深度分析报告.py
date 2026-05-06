"""
四子王旗充电桩 — 深度分析综合报告
整合：聚类/KDE/盲区/评分/竞争密度/小区覆盖/增长预测/推荐选址
"""
import json, base64
from collections import Counter

DATA_PATH = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/stations_data.json"
OUT_PATH = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/index.html"
DESKTOP_PATH = "C:/Users/bl/Desktop/充电桩投资决策报告.html"

with open(DATA_PATH, encoding="utf-8") as f:
    stations = json.load(f)

# 加载深度分析结果
try:
    with open(DATA_PATH.replace("stations_data.json", "depth_summary.json"), encoding="utf-8") as f:
        depth = json.load(f)
except:
    depth = {}

try:
    with open(DATA_PATH.replace("stations_data.json", "depth_residential.json"), encoding="utf-8") as f:
        res_data = json.load(f)
        residential_list = res_data.get("residential", [])
        not_covered_list = res_data.get("not_covered", [])
except:
    residential_list = []
    not_covered_list = []

try:
    with open(DATA_PATH.replace("stations_data.json", "depth_blind_spots.json"), encoding="utf-8") as f:
        blind_spots = json.load(f)
except:
    blind_spots = []

# 品牌颜色
brand_list = ['蒙电e充', '星星充电', '蒙来电', '蒙马(高速)', '咔咔电姆', '驴充充', '云快充', '其他']
brand_colors = ['#4361ee','#f72585','#7209b7','#e76f51','#2a9d8f','#e9c46a','#264653','#8d99ae']
for s in stations:
    s['bi'] = brand_list.index(s['brand']) if s['brand'] in brand_list else 7

# 统计
town = [s for s in stations if s['distance'] <= 5]
brand_count = Counter(s['brand'] for s in stations)
r500 = sum(1 for s in stations if s['distance'] <= 0.5)
r1k = sum(1 for s in stations if s['distance'] <= 1)
r3k = sum(1 for s in stations if s['distance'] <= 3)
ratings = [float(s['rating']) for s in stations if s['rating'] and s['rating'] not in ('[]', '0.0')]
avg_rating = round(sum(ratings)/len(ratings), 1) if ratings else 0

# 品牌表
brand_table_rows = ""
for b, c in brand_count.most_common():
    dists = [s['distance'] for s in stations if s['brand'] == b]
    avg_d = round(sum(dists)/len(dists), 1) if dists else 0
    pct = round(c/len(stations)*100)
    bi = brand_list.index(b) if b in brand_list else 7
    brand_table_rows += f"<tr><td><span class=\"tag\" style=\"background:{brand_colors[bi]}\">{b}</span></td><td>{c}</td><td>{pct}%</td><td>{avg_d}km</td></tr>\n"

# 最近站点表
nearest = sorted(stations, key=lambda s: s['distance'])[:10]
nearest_rows = ""
for i, s in enumerate(nearest[:8], 1):
    bi = s['bi']
    rd = s['rating'] if s['rating'] not in ('[]', '0.0') else '-'
    nearest_rows += f"<tr><td>{i}</td><td><span class=\"tag\" style=\"background:{brand_colors[bi]}\">{s['brand']}</span></td><td>{s['name'][:40]}</td><td>{s['distance']}km</td><td>{rd}</td></tr>\n"

# 全部站点表
all_rows = ""
for i, s in enumerate(sorted(stations, key=lambda x: x['distance']), 1):
    bi = s['bi']
    addr = (s.get('address') or '')[:35]
    tel = (s.get('tel') or '') or '-'
    rd = s['rating'] if s['rating'] not in ('[]', '0.0', '') else '-'
    all_rows += f"<tr class=\"sr\" data-search=\"{s['name']} {s['brand']} {s.get('address','')}\">"
    all_rows += f"<td>{i}</td><td><span class=\"tag\" style=\"background:{brand_colors[bi]}\">{s['brand']}</span></td>"
    all_rows += f"<td>{s['name'][:45]}</td><td style=\"color:#888;font-size:12px\">{addr}</td>"
    all_rows += f"<td>{s['distance']}km</td><td>{rd}</td><td style=\"font-size:12px\">{tel}</td></tr>\n"

data_json = json.dumps(stations, ensure_ascii=False)

# 拼图
def img_tag(name, alt=""):
    return f'<img src="{name}" alt="{alt}" style="width:100%;border-radius:8px;cursor:pointer" onclick="window.open(\'{name}\')">'

TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>四子王旗充电桩投资决策报告 (深度分析版)</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.css">
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,'Microsoft YaHei',sans-serif}
body{background:#f0f2f5;color:#333}
.hd{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);color:#fff;padding:40px 48px 32px}
.hd h1{font-size:28px;font-weight:700;margin-bottom:6px;letter-spacing:1px}
.hd .sub{font-size:14px;color:#8899b4}
.hd .st{display:inline-block;background:#e94560;padding:3px 12px;border-radius:12px;font-size:12px;margin-top:8px}
.kp{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px;padding:24px 48px;background:#fff;border-bottom:1px solid #e8ecf0}
.kp .c{text-align:center}
.kp .n{font-size:28px;font-weight:700;color:#1a1a2e}
.kp .l{font-size:12px;color:#8899b4;margin-top:2px}
.kp .h{color:#e94560}
.ct{max-width:1400px;margin:0 auto;padding:24px 48px}
.sc{background:#fff;border-radius:12px;padding:24px;margin-bottom:24px;box-shadow:0 1px 4px rgba(0,0,0,0.06)}
.sc h2{font-size:18px;font-weight:600;margin-bottom:16px;color:#1a1a2e;display:flex;align-items:center;gap:8px}
#map{height:480px;border-radius:8px;z-index:1}
.cg{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.cg3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px}
.fd{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.fd .fc{padding:16px;border-radius:8px;border-left:4px solid}
.fc.g{border-color:#2a9d8f;background:#f0faf8}
.fc.r{border-color:#e94560;background:#fef0f2}
.fc.b{border-color:#4361ee;background:#f0f2ff}
.fc.a{border-color:#f4a261;background:#fef8f0}
.fc h3{font-size:14px;margin-bottom:4px}
.fc p{font-size:13px;color:#666;line-height:1.6}
.tw{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#f8f9fa;text-align:left;padding:10px 12px;font-weight:600;color:#555;border-bottom:2px solid #dee2e6;white-space:nowrap}
td{padding:8px 12px;border-bottom:1px solid #f0f0f0}
tr:hover td{background:#f8f9ff}
.tag{display:inline-block;padding:2px 8px;border-radius:8px;font-size:11px;color:#fff}
.sb{width:100%;padding:10px 14px;border:1px solid #dee2e6;border-radius:8px;font-size:14px;margin-bottom:12px}
.ft{text-align:center;padding:24px;color:#8899b4;font-size:12px;border-top:1px solid #e8ecf0}
.df{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;font-size:13px}
.df .dc{padding:16px;border-radius:8px}
.tabs{display:flex;gap:4px;margin-bottom:16px;flex-wrap:wrap}
.tab{padding:8px 20px;border-radius:20px;font-size:13px;cursor:pointer;border:1px solid #dee2e6;background:#fff;transition:all 0.2s}
.tab:hover{background:#f0f2ff;border-color:#4361ee}
.tab.act{background:#4361ee;color:#fff;border-color:#4361ee}
.tc{display:none}
.tc.act{display:block}
.met{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:16px}
.met .m{text-align:center;padding:16px;background:#f8f9fa;border-radius:12px}
.met .mv{font-size:24px;font-weight:700;color:#1a1a2e}
.met .ml{font-size:12px;color:#888;margin-top:4px}
.ins{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.ins .i{background:#f8f9fa;border-radius:8px;padding:14px;border-left:3px solid}
.ins .i h4{font-size:13px;margin-bottom:4px}
.ins .i p{font-size:12px;color:#666;line-height:1.5}
@media(max-width:768px){.ct{padding:16px}.hd{padding:24px 16px}.kp{padding:16px;grid-template-columns:repeat(3,1fr)}.cg{grid-template-columns:1fr}.cg3{grid-template-columns:1fr}.fd{grid-template-columns:1fr}.ins{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="hd">
  <h1>&#9889; 四子王旗充电桩投资决策报告</h1>
  <div class="sub">商铺位置：乌兰花镇·高油房路南侧 &nbsp;|&nbsp; 调研周期：2026年5月 &nbsp;|&nbsp; 深度分析版（含聚类/热力/盲区/小区/增长预测）</div>
  <div class="st">&#9889; 数据收集阶段 · 综合评分 """ + str(depth.get('shop_score', '待评估')) + """/40</div>
</div>
<div class="kp">
  <div class="c"><div class="n">""" + str(len(stations)) + """</div><div class="l">充电站总数</div></div>
  <div class="c"><div class="n">""" + str(len(town)) + """</div><div class="l">镇区内(5km)</div></div>
  <div class="c"><div class="n h">""" + str(r500) + """</div><div class="l">500m内竞争</div></div>
  <div class="c"><div class="n">""" + str(r1k) + """</div><div class="l">1km内</div></div>
  <div class="c"><div class="n">""" + str(len(brand_count)) + """</div><div class="l">品牌数量</div></div>
  <div class="c"><div class="n">""" + str(avg_rating) + """</div><div class="l">平均评分(满分5)</div></div>
</div>
<div class="ct">

<!-- Tabs -->
<div class="tabs" id="tabs">
  <div class="tab act" onclick="sw(this,'ov')">&#128202; 总览</div>
  <div class="tab" onclick="sw(this,'da')">&#128200; 深度分析</div>
  <div class="tab" onclick="sw(this,'map')">&#128205; 地图</div>
  <div class="tab" onclick="sw(this,'list')">&#128196; 站点清单</div>
</div>

<!-- 总览 -->
<div class="tc act" id="tc_ov">
<div class="sc">
  <h2>&#128202; 深度分析结论</h2>
  <div class="met">
    <div class="m"><div class="mv">""" + str(depth.get('shop_score', '?')) + """/40</div><div class="ml">商铺综合评分</div></div>
    <div class="m"><div class="mv">""" + str(depth.get('competition_1km', '?')) + """</div><div class="ml">1km内竞争对手</div></div>
    <div class="m"><div class="mv">""" + str(depth.get('blind_grids_500m', '?')) + """</div><div class="ml">500m盲区网格</div></div>
    <div class="m"><div class="mv">""" + str(len(residential_list)) + """</div><div class="ml">镇内小区总数</div></div>
    <div class="m"><div class="mv">""" + str(len(not_covered_list)) + """</div><div class="ml">无覆盖小区</div></div>
    <div class="m"><div class="mv">""" + str(depth.get('growth_forecast_2026', '?')) + """万</div><div class="ml">2026年内蒙古电车</div></div>
  </div>
  <div class="ins">
    <div class="i" style="border-color:#2a9d8f"><h4>&#9989; 位置空白优势</h4><p>高油房路南侧500米内仅1个充电站，1km内3个竞争。镇中心站点密集，商铺所在区域相对空白。</p></div>
    <div class="i" style="border-color:#4361ee"><h4>&#128202; 蒙电e充垄断市场</h4><p>全镇17个站（占53%）为蒙电e充运营。与其价格战不可行，优势在于位置便利性和服务质量。</p></div>
    <div class="i" style="border-color:#f4a261"><h4>&#128227; 小区覆盖缺口</h4><p>""" + str(len(residential_list)) + """个住宅小区中，""" + str(len(not_covered_list)) + """个（""" + str(round(len(not_covered_list)/max(len(residential_list),1)*100)) + """%）500m内无充电站。商圈周边覆盖不足=需求未被满足。</p></div>
    <div class="i" style="border-color:#e94560"><h4>&#128200; 增长趋势利好</h4><p>内蒙古电车保有量2025年53.6万辆（翻倍增长）。预测2026年~107万辆，2027年需约90支快充枪（当前仅58支），供求缺口将出现。</p></div>
    <div class="i" style="border-color:#7209b7"><h4>&#127919; 综合推荐</h4><p>商铺综合评分20.4/40，属"谨慎"区间。关键是车管所数据（真实电车保有量）+ 供电容量确认 + 补贴资格确认。</p></div>
    <div class="i" style="border-color:#e76f51"><h4>&#9888;&#65039; 评分偏低=机会</h4><p>现有站点平均评分仅2.8/5，说明用户体验普遍差。新站做好维护、支付便利性，可形成口碑优势。</p></div>
  </div>
</div>

<div class="sc">
  <h2>&#127978; 竞争格局</h2>
  <div class="cg">
    <div><canvas id="cbrand"></canvas></div>
    <div style="padding:8px">
      <table><tr><th>品牌</th><th>数量</th><th>占比</th><th>平均距离</th></tr>""" + brand_table_rows + """</table>
    </div>
  </div>
</div>

<div class="sc">
  <h2>&#128203; 距商铺最近的充电站</h2>
  <div class="tw">
    <table><tr><th>#</th><th>品牌</th><th>站名</th><th>距离</th><th>评分</th></tr>""" + nearest_rows + """</table>
  </div>
</div>

<div class="sc">
  <h2>&#9878;&#65039; 决策框架</h2>
  <div class="df">
    <div class="dc" style="background:#f0faf8;border:1px solid #b8e6d8"><h3 style="font-size:14px;color:#2a9d8f">&#9989; 做（Go）</h3><p style="color:#555;margin-top:6px;line-height:1.6">电车保有量 &gt; 500辆<br>供电容量够（不需大额增容）<br>周边站确实使用率高</p></div>
    <div class="dc" style="background:#fef8f0;border:1px solid #f7d9a3"><h3 style="font-size:14px;color:#f4a261">&#9888;&#65039; 谨慎</h3><p style="color:#555;margin-top:6px;line-height:1.6">电车保有量 200~500辆<br>需要一定增容费用<br>回收周期 3~5年可接受</p></div>
    <div class="dc" style="background:#fef0f2;border:1px solid #f5b7b7"><h3 style="font-size:14px;color:#e94560">&#10060; 不做（No-Go）</h3><p style="color:#555;margin-top:6px;line-height:1.6">电车保有量 &lt; 200辆<br>需要新增变压器（投入过大）<br>补贴确认申请不到</p></div>
  </div>
</div>
</div>

<!-- 深度分析 -->
<div class="tc" id="tc_da">
<div class="sc">
  <h2>&#128200; 深度分析仪表盘</h2>
  <div class="cg">
    <div><h3 style="font-size:14px;text-align:center;margin-bottom:8px;color:#4361ee">K-Means 聚类分析 (3簇)</h3>""" + img_tag("depth_clusters.png", "聚类分析") + """</div>
    <div><h3 style="font-size:14px;text-align:center;margin-bottom:8px;color:#4361ee">KDE 密度热力图</h3>""" + img_tag("depth_kde.png", "密度热力") + """</div>
  </div>
</div>

<div class="sc">
  <h2>&#127965; 盲区分析 &amp; 小区覆盖</h2>
  <div class="cg">
    <div><h3 style="font-size:14px;text-align:center;margin-bottom:8px;color:#e94560">乌兰花镇充电盲区 (500m网格)</h3>""" + img_tag("depth_blind_spots.png", "盲区图") + """</div>
    <div><h3 style="font-size:14px;text-align:center;margin-bottom:8px;color:#2a9d8f">住宅小区充电覆盖分析</h3>""" + img_tag("depth_residential_coverage.png", "小区覆盖") + """</div>
  </div>
</div>

<div class="sc">
  <h2>&#128202; 评分 &amp; 竞争分析</h2>
  <div class="cg">
    <div><h3 style="font-size:14px;text-align:center;margin-bottom:8px;color:#4361ee">评分 vs 距离商铺远近</h3>""" + img_tag("depth_rating_vs_distance.png", "评分距离") + """</div>
    <div><h3 style="font-size:14px;text-align:center;margin-bottom:8px;color:#f72585">各品牌平均评分对比</h3>""" + img_tag("depth_brand_ratings.png", "品牌评分") + """</div>
  </div>
  <div class="cg" style="margin-top:20px">
    <div><h3 style="font-size:14px;text-align:center;margin-bottom:8px;color:#e76f51">竞争密度分析</h3>""" + img_tag("depth_competition_density.png", "竞争密度") + """</div>
    <div><h3 style="font-size:14px;text-align:center;margin-bottom:8px;color:#7209b7">各站位置综合评分</h3>""" + img_tag("depth_location_scores.png", "位置评分") + """</div>
  </div>
</div>

<div class="sc">
  <h2>&#128200; 增长趋势 &amp; 推荐选址</h2>
  <div class="cg">
    <div><h3 style="font-size:14px;text-align:center;margin-bottom:8px;color:#2a9d8f">内蒙古电车增长趋势预测</h3>""" + img_tag("depth_growth_forecast.png", "增长预测") + """</div>
    <div><h3 style="font-size:14px;text-align:center;margin-bottom:8px;color:#2a9d8f">选址综合推荐热力图</h3>""" + img_tag("depth_recommend_heatmap.png", "推荐选址") + """</div>
  </div>
</div>
</div>

<!-- 地图 -->
<div class="tc" id="tc_map">
<div class="sc">
  <h2>&#128205; 充电站分布地图</h2>
  <div id="map"></div>
</div>
</div>

<!-- 站点清单 -->
<div class="tc" id="tc_list">
<div class="sc">
  <h2>&#128196; 全部站点清单</h2>
  <input class="sb" type="text" id="ss" placeholder="搜索站点名称、品牌、地址..." oninput="ft(this.value)">
  <div class="tw">
    <table id="st"><tr><th>#</th><th>品牌</th><th>名称</th><th>地址</th><th>距商铺</th><th>评分</th><th>电话</th></tr>""" + all_rows + """</table>
  </div>
</div>
</div>

</div>
<div class="ft">四子王旗充电桩投资调研报告 &middot; 深度分析版 &middot; 2026年5月 &middot; 数据来源：高德地图API / 内蒙古电力集团 / 社交媒体验证</div>

<script>
var colorMap = {'蒙电e充':'#4361ee','星星充电':'#f72585','蒙来电':'#7209b7','蒙马(高速)':'#e76f51','咔咔电姆':'#2a9d8f','驴充充':'#e9c46a','云快充':'#264653','其他':'#8d99ae'};
var stations = """ + data_json + """;

// Tab switching
function sw(el, id) {
  document.querySelectorAll('.tab').forEach(function(t){t.classList.remove('act')});
  document.querySelectorAll('.tc').forEach(function(t){t.classList.remove('act')});
  el.classList.add('act');
  document.getElementById('tc_'+id).classList.add('act');
  if(id==='map') setTimeout(function(){map.invalidateSize()},200);
}

// Map
var map = L.map('map').setView([41.53,111.70],13);
L.tileLayer('https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',{attribution:'&copy; 高德地图',maxZoom:18}).addTo(map);
L.marker([41.51879906,111.69113591],{icon:L.divIcon({html:'<div style="background:#e94560;width:30px;height:30px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.3);text-align:center;line-height:30px;font-size:16px;color:#fff">S</div>',className:'',iconSize:[30,30],iconAnchor:[15,15]})}).addTo(map).bindTooltip('<b>高油房路（充电桩规划位）</b>');
[{r:500,c:'#e94560'},{r:1000,c:'#f4a261'},{r:3000,c:'#2a9d8f'}].forEach(function(d){L.circle([41.51879906,111.69113591],{radius:d.r,color:d.c,fill:false,weight:1.5,dashArray:'5,8',opacity:0.5}).addTo(map)});
stations.forEach(function(s){var c=colorMap[s.brand]||'#8d99ae',sz=s.distance<1?26:s.distance<3?22:18;L.marker([s.lat,s.lng],{icon:L.divIcon({html:'<div style="background:'+c+';width:'+sz+'px;height:'+sz+'px;border-radius:50%;border:2px solid #fff;text-align:center;line-height:'+sz+'px;font-size:'+(sz*0.45)+'px;color:#fff">+</div>',className:'',iconSize:[sz,sz],iconAnchor:[sz/2,sz/2]})}).addTo(map).bindTooltip('<b>'+s.name+'</b><br><span style="color:'+c+'">'+s.brand+'</span> | '+s.distance.toFixed(2)+'km')});

// Chart: brand doughnut
var brands = {};
stations.forEach(function(s){brands[s.brand]=(brands[s.brand]||0)+1});
var bl=Object.keys(brands), bv=Object.values(brands), bc=bl.map(function(b){return colorMap[b]||'#8d99ae'});
new Chart(document.getElementById('cbrand'),{type:'doughnut',data:{labels:bl,datasets:[{data:bv,backgroundColor:bc,borderWidth:0}]},options:{responsive:true,plugins:{legend:{position:'right',labels:{fontSize:12}},title:{display:true,text:'品牌分布',font:{size:14}}}}});

// Search
function ft(q){document.querySelectorAll('.sr').forEach(function(r){r.style.display=r.getAttribute('data-search').indexOf(q)>=0?'':'none'})}
</script>
</body>
</html>"""

for path in [OUT_PATH, DESKTOP_PATH]:
    with open(path, "w", encoding="utf-8") as f:
        f.write(TPL)

# Verify
unreplaced = [kw for kw in ['__DATA__'] if kw in TPL]
if not unreplaced:
    print(f"✅ 深度分析综合报告已生成! ({len(TPL)} 字符)")
    print(f"   {OUT_PATH}")
    print(f"   {DESKTOP_PATH}")
else:
    print(f"❌ 有占位符未替换: {unreplaced}")
