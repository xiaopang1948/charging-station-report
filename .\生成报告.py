"""
四子王旗充电桩投资决策仪表盘 — 综合报告生成器
参考：Atlas EV Hub, Liberty Plugins, EVmatch 设计风格
改用 .replace() 避免 f-string 大括号冲突
"""
import json
from collections import Counter

DATA_PATH = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/stations_data.json"
OUT_PATH = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/index.html"
DESKTOP_PATH = "C:/Users/bl/Desktop/充电桩投资决策报告.html"

with open(DATA_PATH, encoding="utf-8") as f:
    stations = json.load(f)

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
r5k = sum(1 for s in stations if s['distance'] <= 5)
ratings = [float(s['rating']) for s in stations if s['rating'] and s['rating'] not in ('[]', '0.0')]
avg_rating = round(sum(ratings)/len(ratings), 1) if ratings else 0

# 品牌分布
brand_labels = json.dumps([b for b, _ in brand_count.most_common()], ensure_ascii=False)
brand_values = json.dumps([c for _, c in brand_count.most_common()])

# 距离分布
bins = [0,0.5,1,2,3,5,10,20,50,200]
hist_labels = json.dumps(['<0.5km','0.5-1','1-2','2-3','3-5','5-10','10-20','20-50','>50km'], ensure_ascii=False)
hist_values = json.dumps([sum(1 for s in stations if bins[i]<=s['distance']<bins[i+1]) for i in range(len(bins)-1)])

# 累计
sorted_dists = sorted([s['distance'] for s in stations])
cum_x = json.dumps(sorted_dists)
cum_y = json.dumps(list(range(1, len(sorted_dists)+1)))

# 评分分布
rating_bins = [0,1,2,3,4,5]
rating_labels = json.dumps(['0-1','1-2','2-3','3-4','4-5'], ensure_ascii=False)
rating_vals = json.dumps([sum(1 for r in ratings if rating_bins[i]<=r<rating_bins[i+1]) for i in range(len(rating_bins)-1)])
rating_count = len(ratings)

# 最近站点
nearest = sorted(stations, key=lambda s: s['distance'])[:10]

# 品牌平均距离
brand_avg_data = {}
for s in stations:
    brand_avg_data.setdefault(s['brand'], []).append(s['distance'])
avg_brands = json.dumps([b for b in brand_list if b in brand_avg_data], ensure_ascii=False)
avg_values = json.dumps([round(sum(brand_avg_data[b])/len(brand_avg_data[b]), 1) for b in brand_list if b in brand_avg_data])

# 竞争表
brand_table_rows = ""
for b, c in brand_count.most_common():
    dists = [s['distance'] for s in stations if s['brand'] == b]
    avg_d = round(sum(dists)/len(dists), 1) if dists else 0
    pct = round(c/len(stations)*100)
    bi = brand_list.index(b) if b in brand_list else 7
    brand_table_rows += f"<tr><td><span class=\"tag\" style=\"background:{brand_colors[bi]}\">{b}</span></td><td>{c}</td><td>{pct}%</td><td>{avg_d}km</td></tr>\n"

# 最近站点表
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
ratings_json = json.dumps(ratings)

TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>四子王旗充电桩投资决策报告</title>
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
.sb{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.st{background:#f8f9fa;border-radius:8px;padding:14px;display:flex;align-items:flex-start;gap:12px}
.st .sn{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0}
.st.p .sn{background:#dee2e6;color:#666}
.st.d .sn{background:#2a9d8f;color:#fff}
.st .tx h4{font-size:13px;margin-bottom:2px}
.st .tx p{font-size:12px;color:#888}
.sb{width:100%;padding:10px 14px;border:1px solid #dee2e6;border-radius:8px;font-size:14px;margin-bottom:12px}
.ft{text-align:center;padding:24px;color:#8899b4;font-size:12px;border-top:1px solid #e8ecf0}
.df{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;font-size:13px}
.df .dc{padding:16px;border-radius:8px}
@media(max-width:768px){.ct{padding:16px}.hd{padding:24px 16px}.kp{padding:16px;grid-template-columns:repeat(3,1fr)}.cg{grid-template-columns:1fr}.fd{grid-template-columns:1fr}.sb{grid-template-columns:1fr}.df{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="hd">
  <h1>四子王旗充电桩投资决策报告</h1>
  <div class="sub">商铺位置：乌兰花镇·高油房路南侧 &nbsp;|&nbsp; 调研周期：2026年5月 &nbsp;|&nbsp; 状态：数据收集中</div>
  <div class="st">&#9889; 数据收集阶段 · 尚未决策</div>
</div>
<div class="kp">
  <div class="c"><div class="n">__TOTAL__</div><div class="l">充电站总数</div></div>
  <div class="c"><div class="n">__TOWN__</div><div class="l">镇区内(5km)</div></div>
  <div class="c"><div class="n h">__500M__</div><div class="l">500m内竞争</div></div>
  <div class="c"><div class="n">__1KM__</div><div class="l">1km内</div></div>
  <div class="c"><div class="n">__BRANDS__</div><div class="l">品牌数量</div></div>
  <div class="c"><div class="n">__AVG_RATING__</div><div class="l">平均评分(满分5)</div></div>
</div>
<div class="ct">
<div class="sc">
  <h2>&#128205; 充电站分布地图</h2>
  <div id="map"></div>
</div>
<div class="sc">
  <h2>&#128200; 数据分析图表</h2>
  <div class="cg">
    <div><canvas id="cbrand"></canvas></div>
    <div><canvas id="cdist"></canvas></div>
    <div><canvas id="ccum"></canvas></div>
    <div><canvas id="crating"></canvas></div>
  </div>
</div>
<div class="sc">
  <h2>&#128269; 核心发现</h2>
  <div class="fd">
    <div class="fc g"><h3>&#9989; 位置空白优势</h3><p>高油房路南侧500米内仅1个充电站（蒙来电/维也纳酒店），1km内5个。镇中心站点密集，你商铺所在区域有空白。</p></div>
    <div class="fc b"><h3>&#128202; 蒙电e充垄断市场</h3><p>全镇17个站（占53%）为蒙电e充运营，定价极低（0.65元/度）。与其价格战不可行，优势在于位置便利性。</p></div>
    <div class="fc a"><h3>&#9888;&#65039; 利用率可能偏低</h3><p>基于乌兰察布2024数据推算：日均单枪约4.8度，2025年翻倍后预估10~20度/天。月收入约240~480元/枪。</p></div>
    <div class="fc r"><h3>&#10060; 关键数据仍缺失</h3><p>四子王旗电车保有量（车管所）、商铺供电容量（供电公司）、补贴资格（发改委）尚未确认。这些是决策核心依据。</p></div>
  </div>
</div>
<div class="sc">
  <h2>&#127978; 竞争格局</h2>
  <div class="cg">
    <div><canvas id="cbranddist"></canvas></div>
    <div style="padding:8px">
      <table>
        <tr><th>品牌</th><th>数量</th><th>占比</th><th>平均距离</th></tr>
        __BRAND_TABLE__
      </table>
    </div>
  </div>
</div>
<div class="sc">
  <h2>&#128203; 距商铺最近的充电站</h2>
  <div class="tw">
    <table><tr><th>#</th><th>品牌</th><th>站名</th><th>距离</th><th>评分</th></tr>__NEAREST__</table>
  </div>
</div>
<div class="sc">
  <h2>&#128196; 全部站点清单</h2>
  <input class="sb" type="text" id="ss" placeholder="搜索站点名称、品牌、地址..." oninput="ft(this.value)">
  <div class="tw">
    <table id="st"><tr><th>#</th><th>品牌</th><th>名称</th><th>地址</th><th>距商铺</th><th>评分</th><th>电话</th></tr>__ALL_ROWS__</table>
  </div>
</div>
<div class="sc">
  <h2>&#127919; 下一步行动</h2>
  <div class="steps">
    <div class="st d"><div class="sn">1</div><div class="tx"><h4>市场调研完成</h4><p>32个充电站POI数据，覆盖8个品牌，完成竞品分布分析</p></div></div>
    <div class="st d"><div class="sn">2</div><div class="tx"><h4>蒙电e充平台调研</h4><p>覆盖范围、定价策略、运营数据、设备供应商</p></div></div>
    <div class="st d"><div class="sn">3</div><div class="tx"><h4>品牌可靠性验证</h4><p>许继电气质量可靠（投诉极少），科大智能/驴充充不推荐</p></div></div>
    <div class="st d"><div class="sn">4</div><div class="tx"><h4>补贴政策调研</h4><p>400元/KW建设补贴（60kW可申请24,000元），但存在功率门槛风险</p></div></div>
    <div class="st p"><div class="sn">5</div><div class="tx"><h4 style="color:#e94560">打电话：车管所</h4><p>确认四子王旗电车保有量，这是决策最关键的数据</p></div></div>
    <div class="st p"><div class="sn">6</div><div class="tx"><h4 style="color:#e94560">打电话：供电公司</h4><p>确认商铺供电容量、是否需要变压器增容、峰谷电价</p></div></div>
    <div class="st p"><div class="sn">7</div><div class="tx"><h4>打电话：发改委/工信局</h4><p>确认备案流程和补贴申请资格</p></div></div>
    <div class="st p"><div class="sn">8</div><div class="tx"><h4>实地考察</h4><p>去文化路、和平路等站点看使用率，跟车主聊天验证需求</p></div></div>
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
<div class="ft">四子王旗充电桩投资调研报告 &middot; 2026年5月 &middot; 数据来源：高德地图API / 内蒙古电力集团 / 社交媒体验证</div>

<script>
var colorMap = {'蒙电e充':'#4361ee','星星充电':'#f72585','蒙来电':'#7209b7','蒙马(高速)':'#e76f51','咔咔电姆':'#2a9d8f','驴充充':'#e9c46a','云快充':'#264653','其他':'#8d99ae'};
var stations = __DATA__;
var map = L.map('map').setView([41.53,111.70],13);
L.tileLayer('https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',{attribution:'&copy; 高德地图',maxZoom:18}).addTo(map);
L.marker([41.5270,111.7030],{icon:L.divIcon({html:'<div style="background:#e94560;width:30px;height:30px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.3);text-align:center;line-height:30px;font-size:16px;color:#fff">S</div>',className:'',iconSize:[30,30],iconAnchor:[15,15]})}).addTo(map).bindTooltip('<b>高油房路南侧（商铺）</b>');
[{r:500,c:'#e94560'},{r:1000,c:'#f4a261'},{r:3000,c:'#2a9d8f'}].forEach(function(d){L.circle([41.5270,111.7030],{radius:d.r,color:d.c,fill:false,weight:1.5,dashArray:'5,8',opacity:0.5}).addTo(map)});
stations.forEach(function(s){var c=colorMap[s.brand]||'#8d99ae',sz=s.distance<1?26:s.distance<3?22:18;L.marker([s.lat,s.lng],{icon:L.divIcon({html:'<div style="background:'+c+';width:'+sz+'px;height:'+sz+'px;border-radius:50%;border:2px solid #fff;text-align:center;line-height:'+sz+'px;font-size:'+(sz*0.45)+'px;color:#fff">+</div>',className:'',iconSize:[sz,sz],iconAnchor:[sz/2,sz/2]})}).addTo(map).bindTooltip('<b>'+s.name+'</b><br><span style="color:'+c+'">'+s.brand+'</span> | '+s.distance.toFixed(2)+'km')});

new Chart(document.getElementById('cbrand'),{type:'doughnut',data:{labels:__BRAND_LABELS__,datasets:[{data:__BRAND_VALUES__,backgroundColor:__BRAND_COLORS__,borderWidth:0}]},options:{responsive:true,plugins:{legend:{position:'right',labels:{fontSize:12}},title:{display:true,text:'品牌分布',font:{size:14}}}}});

new Chart(document.getElementById('cdist'),{type:'bar',data:{labels:__HIST_LABELS__,datasets:[{label:'站点数',data:__HIST_VALUES__,backgroundColor:['#e94560','#f4a261','#2a9d8f','#2a9d8f','#264653','#8d99ae','#8d99ae','#8d99ae','#8d99ae'],borderRadius:4}]},options:{responsive:true,plugins:{title:{display:true,text:'距商铺距离分布',font:{size:14}}},scales:{y:{beginAtZero:true,ticks:{stepSize:1}}}}});

new Chart(document.getElementById('ccum'),{type:'line',data:{labels:__CUM_X__,datasets:[{label:'累计站点数',data:__CUM_Y__,borderColor:'#4361ee',backgroundColor:'rgba(67,97,238,0.1)',fill:true,tension:0.3,pointRadius:2}]},options:{responsive:true,plugins:{title:{display:true,text:'累计站点数 vs 距离',font:{size:14}}},scales:{x:{title:{display:true,text:'距离(km)'}},y:{beginAtZero:true,title:{display:true,text:'站点数'}}}}});

var ratings = __RATINGS__;
new Chart(document.getElementById('crating'),{type:'bar',data:{labels:__RATING_LABELS__,datasets:[{label:'站点数',data:__RATING_VALS__,backgroundColor:['#e94560','#f4a261','#2a9d8f','#4361ee','#7209b7'],borderRadius:4}]},options:{responsive:true,plugins:{title:{display:true,text:'评分分布 (n=__RATING_COUNT__, 平均__AVG_RATING__)',font:{size:14}}},scales:{y:{beginAtZero:true,ticks:{stepSize:1}}}}});

new Chart(document.getElementById('cbranddist'),{type:'bar',data:{labels:__AVG_BRANDS__,datasets:[{label:'平均距离(km)',data:__AVG_VALUES__,backgroundColor:['#4361ee','#f72585','#7209b7','#e76f51','#2a9d8f','#e9c46a','#264653','#8d99ae'],borderRadius:4}]},options:{responsive:true,indexAxis:'y',plugins:{title:{display:true,text:'各品牌距商铺平均距离',font:{size:14}}},scales:{x:{beginAtZero:true,title:{display:true,text:'km'}}}}});

function ft(q){document.querySelectorAll('.sr').forEach(function(r){r.style.display=r.getAttribute('data-search').indexOf(q)>=0?'':'none'})}
</script>
</body>
</html>"""

# 替换占位符
html = TPL
html = html.replace('__DATA__', data_json)
html = html.replace('__TOTAL__', str(len(stations)))
html = html.replace('__TOWN__', str(len(town)))
html = html.replace('__500M__', str(r500))
html = html.replace('__1KM__', str(r1k))
html = html.replace('__BRANDS__', str(len(brand_count)))
html = html.replace('__AVG_RATING__', str(avg_rating))
html = html.replace('__BRAND_LABELS__', brand_labels)
html = html.replace('__BRAND_VALUES__', brand_values)
html = html.replace('__BRAND_COLORS__', json.dumps(brand_colors))
html = html.replace('__HIST_LABELS__', hist_labels)
html = html.replace('__HIST_VALUES__', hist_values)
html = html.replace('__CUM_X__', cum_x)
html = html.replace('__CUM_Y__', cum_y)
html = html.replace('__RATINGS__', ratings_json)
html = html.replace('__RATING_LABELS__', rating_labels)
html = html.replace('__RATING_VALS__', rating_vals)
html = html.replace('__RATING_COUNT__', str(rating_count))
html = html.replace('__AVG_BRANDS__', avg_brands)
html = html.replace('__AVG_VALUES__', avg_values)
html = html.replace('__BRAND_TABLE__', brand_table_rows)
html = html.replace('__NEAREST__', nearest_rows)
html = html.replace('__ALL_ROWS__', all_rows)

for path in [OUT_PATH, DESKTOP_PATH]:
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

# 验证
verify = []
for kw in ['__DATA__', '__TOTAL__', '__BRAND_LABELS__']:
    if kw in html:
        verify.append(f"❌ {kw} 未替换")
if not any('__' in k for k in ['__DATA__', '__TOTAL__']):
    print("✅ 所有占位符已替换")
else:
    print('\n'.join(verify))

print(f"报告已生成! ({len(html)} 字符)")
print(f"项目目录: {OUT_PATH}")
print(f"桌面: {DESKTOP_PATH}")
print(f"站点数: {len(stations)}")
