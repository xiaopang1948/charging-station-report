"""
四子王旗充电桩投资决策报告 — 4种视觉风格版
"""
import json
from collections import Counter

DATA_PATH = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/stations_data.json"
OUT_DIR = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/"
DESKTOP = "C:/Users/bl/Desktop/"

with open(DATA_PATH, encoding="utf-8") as f:
    stations = json.load(f)

brand_list = ['蒙电e充', '星星充电', '蒙来电', '蒙马(高速)', '咔咔电姆', '驴充充', '云快充', '其他']
for s in stations:
    s['bi'] = brand_list.index(s['brand']) if s['brand'] in brand_list else 7

# === 统计数据 ===
town = [s for s in stations if s['distance'] <= 5]
brand_count = Counter(s['brand'] for s in stations)
r500 = sum(1 for s in stations if s['distance'] <= 0.5)
r1k = sum(1 for s in stations if s['distance'] <= 1)
r3k = sum(1 for s in stations if s['distance'] <= 3)
r5k = sum(1 for s in stations if s['distance'] <= 5)
ratings = [float(s['rating']) for s in stations if s['rating'] and s['rating'] not in ('[]', '0.0')]
avg_rating = round(sum(ratings)/len(ratings), 1) if ratings else 0

def brand_data():
    b_labels = json.dumps([b for b, _ in brand_count.most_common()], ensure_ascii=False)
    b_values = json.dumps([c for _, c in brand_count.most_common()])
    b_colors = json.dumps(['#4361ee','#e76f51','#2a9d8f','#8d99ae','#f72585','#e9c46a','#264653','#7209b7'])
    return b_labels, b_values, b_colors

def hist_data():
    bins = [0,0.5,1,2,3,5,10,20,50,200]
    labels = json.dumps(['<0.5km','0.5-1','1-2','2-3','3-5','5-10','10-20','20-50','>50km'], ensure_ascii=False)
    values = json.dumps([sum(1 for s in stations if bins[i]<=s['distance']<bins[i+1]) for i in range(len(bins)-1)])
    return labels, values

def cum_data():
    sd = sorted([s['distance'] for s in stations])
    return json.dumps(sd), json.dumps(list(range(1, len(sd)+1)))

def rating_data():
    rb = [0,1,2,3,4,5]
    labels = json.dumps(['0-1','1-2','2-3','3-4','4-5'], ensure_ascii=False)
    vals = json.dumps([sum(1 for r in ratings if rb[i]<=r<rb[i+1]) for i in range(len(rb)-1)])
    return labels, vals, len(ratings)

def avg_dist_data():
    ad = {}
    for s in stations:
        ad.setdefault(s['brand'], []).append(s['distance'])
    brands = json.dumps([b for b in brand_list if b in ad], ensure_ascii=False)
    vals = json.dumps([round(sum(ad[b])/len(ad[b]), 1) for b in brand_list if b in ad])
    return brands, vals

def nearest_rows():
    nearest = sorted(stations, key=lambda s: s['distance'])[:8]
    rows = ""
    for i, s in enumerate(nearest, 1):
        rd = s['rating'] if s['rating'] not in ('[]', '0.0') else '-'
        rows += f"<tr><td>{i}</td><td>{s['name'][:40]}</td><td>{s['distance']}km</td><td>{rd}</td></tr>"
    return rows

def all_rows():
    rows = ""
    for i, s in enumerate(sorted(stations, key=lambda x: x['distance']), 1):
        addr = (s.get('address') or '')[:35]
        rd = s['rating'] if s['rating'] not in ('[]', '0.0', '') else '-'
        tel = (s.get('tel') or '') or '-'
        rows += f"<tr><td>{i}</td><td>{s['brand']}</td><td>{s['name'][:45]}</td><td>{addr}</td><td>{s['distance']}km</td><td>{rd}</td><td>{tel}</td></tr>"
    return rows

def brand_table():
    rows = ""
    for b, c in brand_count.most_common():
        dists = [s['distance'] for s in stations if s['brand'] == b]
        avg_d = round(sum(dists)/len(dists), 1) if dists else 0
        rows += f"<tr><td>{b}</td><td>{c}</td><td>{round(c/len(stations)*100)}%</td><td>{avg_d}km</td></tr>"
    return rows

# ========== 所有页面共用的脚本 ==========
CHARTS_JS = """<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script>
var stations = __DATA__;
var colorMap = {'蒙电e充':'#4361ee','星星充电':'#f72585','蒙来电':'#7209b7','蒙马(高速)':'#e76f51','咔咔电姆':'#2a9d8f','驴充充':'#e9c46a','云快充':'#264653','其他':'#8d99ae'};

var map = L.map('map').setView([41.53,111.70],13);
L.tileLayer('https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',{attribution:'高德地图',maxZoom:18}).addTo(map);
L.marker([41.5270,111.7030],{icon:L.divIcon({html:'<div class="shop-marker">S</div>',className:'',iconSize:[32,32],iconAnchor:[16,16]})}).addTo(map).bindTooltip('<b>高油房路南侧（商铺）</b>');
[{r:500,c:COLOR_500},{r:1000,c:COLOR_1K},{r:3000,c:COLOR_3K}].forEach(function(d){L.circle([41.5270,111.7030],{radius:d.r,color:d.c,fill:false,weight:1.5,dashArray:'5,8',opacity:0.5}).addTo(map)});
stations.forEach(function(s){var c=colorMap[s.brand]||'#8d99ae',sz=s.distance<1?26:s.distance<3?22:18;L.marker([s.lat,s.lng],{icon:L.divIcon({html:'<div style="background:'+c+';width:'+sz+'px;height:'+sz+'px;border-radius:50%;border:2px solid #'+R+';text-align:center;line-height:'+sz+'px;font-size:'+(sz*0.45)+'px">+</div>',className:'',iconSize:[sz,sz],iconAnchor:[sz/2,sz/2]})}).addTo(map)});

new Chart(document.getElementById('cb'),{type:'doughnut',data:{labels:BL,datasets:[{data:BV,backgroundColor:BC,borderWidth:0}]},options:{responsive:true,plugins:{legend:{position:'right',labels:{fontSize:12}},title:{display:true,text:'品牌分布',font:{size:14}}}}});
new Chart(document.getElementById('cd'),{type:'bar',data:{labels:HL,datasets:[{label:'站点数',data:HV,backgroundColor:['#e94560','#f4a261','#2a9d8f','#2a9d8f','#264653','#8d99ae','#8d99ae','#8d99ae','#8d99ae'],borderRadius:4}]},options:{responsive:true,plugins:{title:{display:true,text:'距商铺距离分布',font:{size:14}}},scales:{y:{beginAtZero:true,ticks:{stepSize:1}}}}});
new Chart(document.getElementById('cc'),{type:'line',data:{labels:CX,datasets:[{label:'累计站点数',data:CY,borderColor:'#4361ee',backgroundColor:'rgba(67,97,238,0.1)',fill:true,tension:0.3,pointRadius:2}]},options:{responsive:true,plugins:{title:{display:true,text:'累计站点数 vs 距离',font:{size:14}}},scales:{x:{title:{display:true,text:'距离(km)'}},y:{beginAtZero:true,title:{display:true,text:'站点数'}}}}});
var rates = RA;
new Chart(document.getElementById('cr'),{type:'bar',data:{labels:RL,datasets:[{label:'站点数',data:RV,backgroundColor:['#e94560','#f4a261','#2a9d8f','#4361ee','#7209b7'],borderRadius:4}]},options:{responsive:true,plugins:{title:{display:true,text:'评分分布 (n='+RN+', 平均'+AG+')',font:{size:14}}},scales:{y:{beginAtZero:true,ticks:{stepSize:1}}}}});
new Chart(document.getElementById('cbd'),{type:'bar',data:{labels:AB,datasets:[{label:'平均距离(km)',data:AV,backgroundColor:['#4361ee','#f72585','#7209b7','#e76f51','#2a9d8f','#e9c46a','#264653','#8d99ae'],borderRadius:4}]},options:{responsive:true,indexAxis:'y',plugins:{title:{display:true,text:'各品牌距商铺平均距离',font:{size:14}}},scales:{x:{beginAtZero:true,title:{display:true,text:'km'}}}}});
function ft(q){document.querySelectorAll('.sr').forEach(function(r){r.style.display=r.getAttribute('data-s').indexOf(q)>=0?'':'none'})}
</script>"""

BL, BV, BC = brand_data()
HL, HV = hist_data()
CX, CY = cum_data()
RL, RV, RN = rating_data()
AB, AV = avg_dist_data()
NR = nearest_rows()
AR = all_rows()
BT = brand_table()
DI = json.dumps(stations, ensure_ascii=False)
RJ = json.dumps(ratings)

# ========== 4种风格模板 ==========

STYLES = {
    "极简商务风（Stripe风格）": {
        "filename": "充电桩报告_极简商务.html",
        "COLOR_500": "'#e53e3e'", "COLOR_1K": "'#dd6b20'", "COLOR_3K": "'#38a169'", "R": "fff",
        "CSS": """
body{margin:0;background:#f7f8fa;color:#1a202c;font-family:-apple-system,'Inter','Microsoft YaHei',sans-serif}
.hd{background:#fff;border-bottom:1px solid #e2e8f0;padding:48px 64px 32px;max-width:1280px;margin:0 auto}
.hd h1{font-size:24px;font-weight:600;color:#1a202c;margin:0 0 4px}
.hd .sub{font-size:14px;color:#718096}
.hd .st{display:inline-block;background:#ebf4ff;color:#3182ce;padding:2px 12px;border-radius:4px;font-size:13px;font-weight:500;margin-top:8px}
.kp{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;background:#e2e8f0;max-width:1280px;margin:0 auto;border-bottom:1px solid #e2e8f0}
.kp .c{background:#fff;padding:24px 16px;text-align:center}
.kp .n{font-size:32px;font-weight:700;color:#2d3748}
.kp .l{font-size:12px;color:#a0aec0;margin-top:4px;text-transform:uppercase;letter-spacing:0.5px}
.kp .h{color:#e53e3e}
.ct{max-width:1280px;margin:0 auto;padding:32px 64px}
.sc{background:#fff;border-radius:8px;margin-bottom:24px;padding:32px;box-shadow:0 1px 3px rgba(0,0,0,0.04);border:1px solid #e2e8f0}
.sc h2{font-size:18px;font-weight:600;color:#2d3748;margin:0 0 20px;padding-bottom:12px;border-bottom:1px solid #f0f0f0}
#map{height:420px;border-radius:8px}
.cg{display:grid;grid-template-columns:1fr 1fr;gap:32px}
.fd{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.fc{padding:20px;border-radius:8px;border:1px solid #e2e8f0}
.fc.g{background:#f0fff4;border-color:#c6f6d5}.fc.r{background:#fff5f5;border-color:#fed7d7}
.fc.b{background:#ebf8ff;border-color:#bee3f8}.fc.a{background:#fffaf0;border-color:#feebc8}
.fc h3{font-size:15px;margin:0 0 6px;font-weight:600}.fc p{font-size:13px;color:#4a5568;line-height:1.6;margin:0}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 12px;font-weight:600;color:#718096;border-bottom:2px solid #e2e8f0;font-size:11px;text-transform:uppercase;letter-spacing:0.5px}
td{padding:8px 12px;border-bottom:1px solid #f7f8fa;color:#4a5568}
tr:hover td{background:#f7f8fa}
.sb{width:100%;padding:10px 14px;border:1px solid #e2e8f0;border-radius:6px;font-size:14px;margin-bottom:16px;background:#f7f8fa;border:none}
.sb:focus{outline:none;background:#fff;box-shadow:0 0 0 2px #3182ce}
.steps{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.st{background:#f7f8fa;border-radius:6px;padding:16px;display:flex;gap:12px;align-items:flex-start}
.st .sn{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:12px;flex-shrink:0}
.st.p .sn{background:#e2e8f0;color:#718096}.st.d .sn{background:#48bb78;color:#fff}
.st .tx h4{font-size:13px;margin:0 0 2px;font-weight:600}.st .tx p{font-size:12px;color:#718096;margin:0}
.df{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;font-size:13px}
.df .dc{padding:20px;border-radius:8px}
.ft{text-align:center;padding:24px;color:#a0aec0;font-size:12px}
@media(max-width:768px){.hd{padding:24px 16px}.kp{grid-template-columns:repeat(3,1fr)}.kp .n{font-size:24px}.ct{padding:16px 16px}.cg{grid-template-columns:1fr}.fd{grid-template-columns:1fr}.steps{grid-template-columns:1fr}.df{grid-template-columns:1fr}}
"""
    },
    "深色科技风（暗黑模式）": {
        "filename": "充电桩报告_深色科技.html",
        "COLOR_500": "'#ff6b6b'", "COLOR_1K": "'#ffa94d'", "COLOR_3K": "'#69db7c'", "R": "1a1b2e",
        "CSS": """
body{margin:0;background:#0f0f1a;color:#e0e0e0;font-family:-apple-system,'SF Pro Text','Microsoft YaHei',sans-serif}
.hd{background:linear-gradient(135deg,#0a0a1a 0%,#1a1b3e 50%,#0a0a2a 100%);padding:48px 64px 32px;border-bottom:1px solid rgba(99,102,241,0.2)}
.hd h1{font-size:24px;font-weight:700;margin:0 0 4px;background:linear-gradient(90deg,#818cf8,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hd .sub{font-size:14px;color:#64748b}
.hd .st{display:inline-block;background:rgba(99,102,241,0.15);color:#818cf8;padding:2px 12px;border-radius:4px;font-size:12px;border:1px solid rgba(99,102,241,0.3);margin-top:8px}
.kp{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;background:rgba(99,102,241,0.1);max-width:1400px;margin:0 auto}
.kp .c{background:#15162c;padding:24px 16px;text-align:center}
.kp .n{font-size:32px;font-weight:700;color:#e2e8f0}
.kp .l{font-size:11px;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:1px}
.kp .h{color:#ff6b6b}
.ct{max-width:1400px;margin:0 auto;padding:32px 64px}
.sc{background:#15162c;border-radius:12px;margin-bottom:24px;padding:32px;border:1px solid rgba(99,102,241,0.15);box-shadow:0 4px 24px rgba(0,0,0,0.3)}
.sc h2{font-size:16px;font-weight:600;color:#c7d2fe;margin:0 0 20px;padding-bottom:12px;border-bottom:1px solid rgba(99,102,241,0.1)}
#map{height:420px;border-radius:8px;filter:brightness(0.85)}
.shop-marker{background:#ff6b6b;width:32px;height:32px;border-radius:50%;border:3px solid rgba(255,255,255,0.3);box-shadow:0 0 20px rgba(255,107,107,0.5);text-align:center;line-height:32px;font-size:16px;color:#fff!important}
.cg{display:grid;grid-template-columns:1fr 1fr;gap:32px}
.fd{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.fc{padding:20px;border-radius:8px;border:1px solid rgba(99,102,241,0.15)}
.fc.g{background:rgba(16,185,129,0.1);border-color:rgba(16,185,129,0.2)}.fc.r{background:rgba(239,68,68,0.1);border-color:rgba(239,68,68,0.2)}
.fc.b{background:rgba(99,102,241,0.1);border-color:rgba(99,102,241,0.2)}.fc.a{background:rgba(245,158,11,0.1);border-color:rgba(245,158,11,0.2)}
.fc h3{font-size:14px;margin:0 0 6px;font-weight:600;color:#e2e8f0}.fc p{font-size:13px;color:#94a3b8;line-height:1.6;margin:0}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 12px;font-weight:600;color:#64748b;border-bottom:2px solid rgba(99,102,241,0.15);font-size:11px;text-transform:uppercase;letter-spacing:0.5px}
td{padding:8px 12px;border-bottom:1px solid rgba(99,102,241,0.08);color:#94a3b8}
tr:hover td{background:rgba(99,102,241,0.05)}
.sb{width:100%;padding:10px 14px;border:1px solid rgba(99,102,241,0.2);border-radius:6px;font-size:14px;margin-bottom:16px;background:#1a1b3e;color:#e2e8f0}
.sb:focus{outline:none;box-shadow:0 0 0 2px #818cf8}
.steps{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.st{background:rgba(99,102,241,0.05);border-radius:6px;padding:16px;display:flex;gap:12px;align-items:flex-start;border:1px solid rgba(99,102,241,0.08)}
.st .sn{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:12px;flex-shrink:0}
.st.p .sn{background:rgba(99,102,241,0.15);color:#818cf8}.st.d .sn{background:#10b981;color:#fff}
.st .tx h4{font-size:13px;margin:0 0 2px;font-weight:600;color:#e2e8f0}.st .tx p{font-size:12px;color:#64748b;margin:0}
.df{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;font-size:13px}
.df .dc{padding:20px;border-radius:8px}
.ft{text-align:center;padding:24px;color:#475569;font-size:12px}
@media(max-width:768px){.hd{padding:24px 16px}.kp{grid-template-columns:repeat(3,1fr)}.kp .n{font-size:24px}.ct{padding:16px}.cg{grid-template-columns:1fr}.fd{grid-template-columns:1fr}.steps{grid-template-columns:1fr}.df{grid-template-columns:1fr}}
"""
    },
    "数据新闻风（Bloomberg风格）": {
        "filename": "充电桩报告_数据新闻.html",
        "COLOR_500": "'#e3120b'", "COLOR_1K": "'#ff7f00'", "COLOR_3K": "'#00873e'", "R": "fff",
        "CSS": """
body{margin:0;background:#fff;color:#111;font-family:Georgia,'Times New Roman','Microsoft YaHei',serif}
.hd{background:#111;color:#fff;padding:64px 64px 48px}
.hd h1{font-size:36px;font-weight:700;margin:0 0 8px;line-height:1.2;max-width:800px}
.hd .sub{font-size:14px;color:#999;border-top:1px solid #333;padding-top:12px;margin-top:8px}
.hd .st{display:inline-block;background:#e3120b;padding:2px 10px;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-top:12px;font-family:sans-serif}
.kp{display:grid;grid-template-columns:repeat(6,1fr);gap:0;max-width:1200px;margin:0 auto;border-bottom:3px solid #111}
.kp .c{padding:28px 16px;text-align:center;border-right:1px solid #eee}
.kp .c:last-child{border-right:none}
.kp .n{font-size:36px;font-weight:700;font-family:sans-serif;letter-spacing:-1px}
.kp .l{font-size:10px;color:#666;margin-top:4px;text-transform:uppercase;letter-spacing:1px;font-family:sans-serif}
.kp .h{color:#e3120b}
.ct{max-width:1200px;margin:0 auto;padding:40px 64px}
.sc{margin-bottom:40px;border-bottom:1px solid #eee;padding-bottom:32px}
.sc:last-child{border-bottom:none}
.sc h2{font-size:22px;font-weight:700;margin:0 0 20px;font-family:sans-serif;color:#111}
.sc h2::before{content:'';display:inline-block;width:4px;height:20px;background:#e3120b;margin-right:12px;vertical-align:middle}
#map{height:440px;border-radius:0;border:1px solid #ddd}
.shop-marker{background:#e3120b;width:32px;height:32px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.3);text-align:center;line-height:32px;font-size:16px;color:#fff!important}
.cg{display:grid;grid-template-columns:1fr 1fr;gap:40px}
.fd{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.fc{padding:20px;font-family:sans-serif}
.fc.g{border-left:4px solid #00873e;background:#f9fdf9}.fc.r{border-left:4px solid #e3120b;background:#fdf5f5}
.fc.b{border-left:4px solid #0058a3;background:#f5f8fd}.fc.a{border-left:4px solid #ff7f00;background:#fdf9f5}
.fc h3{font-size:15px;margin:0 0 6px;font-weight:700}.fc p{font-size:14px;color:#444;line-height:1.7;margin:0}
table{width:100%;border-collapse:collapse;font-size:13px;font-family:sans-serif}
th{text-align:left;padding:10px 12px;font-weight:700;color:#111;border-bottom:2px solid #111;font-size:10px;text-transform:uppercase;letter-spacing:1px}
td{padding:8px 12px;border-bottom:1px solid #eee;color:#444}
tr:hover td{background:#f5f5f5}
.sb{width:100%;padding:12px 16px;border:1px solid #ddd;border-radius:0;font-size:14px;font-family:sans-serif;margin-bottom:16px}
.sb:focus{outline:none;border-color:#111}
.steps{display:grid;grid-template-columns:1fr 1fr;gap:12px;font-family:sans-serif}
.st{background:#f9f9f9;padding:16px;display:flex;gap:12px;align-items:flex-start}
.st .sn{width:26px;height:26px;border-radius:0;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;flex-shrink:0;font-family:sans-serif}
.st.p .sn{background:#ddd;color:#666}.st.d .sn{background:#00873e;color:#fff}
.st .tx h4{font-size:13px;margin:0 0 2px;font-weight:700}.st .tx p{font-size:12px;color:#666;margin:0}
.df{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;font-size:13px;font-family:sans-serif}
.df .dc{padding:20px}
.ft{text-align:center;padding:32px;color:#999;font-size:12px;font-family:sans-serif;border-top:3px solid #111;max-width:1200px;margin:0 auto}
@media(max-width:768px){.hd{padding:32px 16px}.hd h1{font-size:28px}.kp{grid-template-columns:repeat(3,1fr)}.kp .n{font-size:28px}.ct{padding:24px 16px}.cg{grid-template-columns:1fr}.fd{grid-template-columns:1fr}.steps{grid-template-columns:1fr}.df{grid-template-columns:1fr}}
"""
    },
    "中文政务风（清新版）": {
        "filename": "充电桩报告_中文政务.html",
        "COLOR_500": "'#c0392b'", "COLOR_1K": "'#d68910'", "COLOR_3K": "'#27ae60'", "R": "fff",
        "CSS": """
body{margin:0;background:#f0f2f5;color:#2c3e50;font-family:'Microsoft YaHei','PingFang SC','Helvetica Neue',sans-serif}
.hd{background:linear-gradient(180deg,#1a3a5c 0%,#2c5f8a 100%);padding:40px 48px 28px}
.hd h1{font-size:26px;font-weight:700;margin:0 0 4px;color:#fff;letter-spacing:2px}
.hd .sub{font-size:14px;color:#a8c8e8}
.hd .st{display:inline-block;background:rgba(255,255,255,0.15);color:#fff;padding:2px 16px;border-radius:20px;font-size:12px;margin-top:8px}
.kp{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;padding:24px 48px;background:#fff}
.kp .c{text-align:center;background:#f8fafc;border-radius:12px;padding:20px 12px}
.kp .n{font-size:30px;font-weight:700;color:#1a3a5c}
.kp .l{font-size:13px;color:#7f8c8d;margin-top:4px}
.kp .h{color:#c0392b}
.ct{max-width:1200px;margin:0 auto;padding:24px 48px}
.sc{background:#fff;border-radius:16px;margin-bottom:24px;padding:28px 32px;box-shadow:0 2px 12px rgba(0,0,0,0.06)}
.sc h2{font-size:18px;font-weight:700;color:#1a3a5c;margin:0 0 16px;padding-left:14px;border-left:4px solid #2c5f8a}
#map{height:420px;border-radius:12px}
.shop-marker{background:#c0392b;width:32px;height:32px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.3);text-align:center;line-height:32px;font-size:16px;color:#fff!important}
.cg{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.fd{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.fc{padding:20px;border-radius:12px;border:1px solid #e8ecf0}
.fc.g{background:#eafaf1;border-color:#a3d9b1}.fc.r{background:#fdedec;border-color:#f5b7b1}
.fc.b{background:#ebf5fb;border-color:#a9cce3}.fc.a{background:#fef9e7;border-color:#f9e79f}
.fc h3{font-size:15px;margin:0 0 6px;font-weight:700}.fc p{font-size:14px;color:#555;line-height:1.7;margin:0}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 12px;font-weight:700;color:#2c3e50;border-bottom:2px solid #d5dbdb;font-size:13px}
td{padding:8px 12px;border-bottom:1px solid #eaeded;color:#555}
tr:hover td{background:#f8f9fa}
.sb{width:100%;padding:10px 16px;border:1px solid #d5dbdb;border-radius:8px;font-size:14px;margin-bottom:16px}
.sb:focus{outline:none;border-color:#2c5f8a;box-shadow:0 0 0 3px rgba(44,95,138,0.1)}
.steps{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.st{background:#f8fafc;border-radius:10px;padding:16px;display:flex;gap:12px;align-items:flex-start}
.st .sn{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0}
.st.p .sn{background:#bdc3c7;color:#fff}.st.d .sn{background:#27ae60;color:#fff}
.st .tx h4{font-size:14px;margin:0 0 2px;font-weight:600;color:#2c3e50}.st .tx p{font-size:13px;color:#7f8c8d;margin:0}
.df{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;font-size:14px}
.df .dc{padding:20px;border-radius:12px}
.ft{text-align:center;padding:24px;color:#95a5a6;font-size:13px;border-top:1px solid #eaeded;max-width:1200px;margin:0 auto}
@media(max-width:768px){.hd{padding:24px 16px}.kp{padding:16px;grid-template-columns:repeat(3,1fr)}.kp .n{font-size:24px}.ct{padding:16px}.cg{grid-template-columns:1fr}.fd{grid-template-columns:1fr}.steps{grid-template-columns:1fr}.df{grid-template-columns:1fr}}
"""
    }
}

for style_name, style in STYLES.items():
    css = style["CSS"].replace("COLOR_500", style["COLOR_500"]).replace("COLOR_1K", style["COLOR_1K"]).replace("COLOR_3K", style["COLOR_3K"])
    r_val = style["R"]

    chart_js = CHARTS_JS.replace("COLOR_500", style["COLOR_500"]).replace("COLOR_1K", style["COLOR_1K"]).replace("COLOR_3K", style["COLOR_3K"]).replace("'#"+r_val, "'#fff")
    chart_js = chart_js.replace("__DATA__", DI)
    chart_js = chart_js.replace("BL", BL).replace("BV", BV).replace("BC", BC)
    chart_js = chart_js.replace("HL", HL).replace("HV", HV)
    chart_js = chart_js.replace("CX", CX).replace("CY", CY)
    chart_js = chart_js.replace("RA", RJ).replace("RL", RL).replace("RV", RV).replace("RN", str(RN)).replace("AG", str(avg_rating))
    chart_js = chart_js.replace("AB", AB).replace("AV", AV)

    lk = "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.css"
    lj = "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.js"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>四子王旗充电桩投资决策报告 — {style_name}</title>
<link rel="stylesheet" href="{lk}">
<script src="{lj}"></script>
<style>{css}
.leaflet-popup-content-wrapper{{border-radius:8px!important}}
.leaflet-popup-content{{margin:10px 14px!important;font-size:13px!important}}
</style>
</head>
<body>
<div class="hd">
  <h1>四子王旗充电桩投资决策报告</h1>
  <div class="sub">商铺：乌兰花镇·高油房路南侧 &nbsp;|&nbsp; 调研：2026年5月 &nbsp;|&nbsp; 风格：{style_name}</div>
  <div class="st">数据收集阶段 · 尚未决策</div>
</div>
<div class="kp">
  <div class="c"><div class="n">{len(stations)}</div><div class="l">充电站总数</div></div>
  <div class="c"><div class="n">{len(town)}</div><div class="l">镇区内(5km)</div></div>
  <div class="c"><div class="n h">{r500}</div><div class="l">500m内竞争</div></div>
  <div class="c"><div class="n">{r1k}</div><div class="l">1km内</div></div>
  <div class="c"><div class="n">{len(brand_count)}</div><div class="l">品牌数量</div></div>
  <div class="c"><div class="n">{avg_rating}</div><div class="l">平均评分</div></div>
</div>
<div class="ct">
<div class="sc">
  <h2>充电站分布地图</h2>
  <div id="map"></div>
</div>
<div class="sc">
  <h2>数据分析</h2>
  <div class="cg">
    <div><canvas id="cb"></canvas></div>
    <div><canvas id="cd"></canvas></div>
    <div><canvas id="cc"></canvas></div>
    <div><canvas id="cr"></canvas></div>
  </div>
</div>
<div class="sc">
  <h2>核心发现</h2>
  <div class="fd">
    <div class="fc g"><h3>位置空白优势</h3><p>高油房路南侧500米内仅1个充电站，1km内5个。镇中心站点密集，你商铺所在区域有空白。</p></div>
    <div class="fc b"><h3>蒙电e充垄断市场</h3><p>全镇17个站（占53%）为蒙电e充运营，定价极低。优势在于位置便利性而非价格竞争。</p></div>
    <div class="fc a"><h3>利用率可能偏低</h3><p>乌兰察布2024年日均单枪约4.8度，翻倍后预估10~20度/天。月收入约240~480元/枪。</p></div>
    <div class="fc r"><h3>关键数据仍缺失</h3><p>电车保有量（车管所）、供电容量（供电公司）、补贴资格（发改委）尚未确认。</p></div>
  </div>
</div>
<div class="sc">
  <h2>竞争格局</h2>
  <div class="cg">
    <div><canvas id="cbd"></canvas></div>
    <div style="padding:8px">
      <table><tr><th>品牌</th><th>数量</th><th>占比</th><th>平均距离</th></tr>{BT}</table>
    </div>
  </div>
</div>
<div class="sc">
  <h2>距商铺最近的充电站</h2>
  <div class="tw"><table><tr><th>#</th><th>站名</th><th>距离</th><th>评分</th></tr>{NR}</table></div>
</div>
<div class="sc">
  <h2>全部站点清单</h2>
  <input class="sb" type="text" placeholder="搜索站点名称、品牌、地址..." oninput="ft(this.value)">
  <div class="tw"><table><tr><th>#</th><th>品牌</th><th>名称</th><th>地址</th><th>距商铺</th><th>评分</th><th>电话</th></tr>{AR}</table></div>
</div>
<div class="sc">
  <h2>下一步行动</h2>
  <div class="steps">
    <div class="st d"><div class="sn">1</div><div class="tx"><h4>市场调研完成</h4><p>32站POI数据，8个品牌，竞品分布分析完成</p></div></div>
    <div class="st d"><div class="sn">2</div><div class="tx"><h4>蒙电e充调研</h4><p>覆盖范围、定价策略、运营数据、设备供应商</p></div></div>
    <div class="st d"><div class="sn">3</div><div class="tx"><h4>品牌可靠性验证</h4><p>许继电气质量可靠，科大智能/驴充充不推荐</p></div></div>
    <div class="st d"><div class="sn">4</div><div class="tx"><h4>补贴政策调研</h4><p>400元/KW建设补贴，存在2500KW门槛风险</p></div></div>
    <div class="st p"><div class="sn">5</div><div class="tx"><h4 style="color:var(--accent,#e53e3e)">打电话：车管所</h4><p>确认四子王旗电车保有量——最关键数据</p></div></div>
    <div class="st p"><div class="sn">6</div><div class="tx"><h4 style="color:var(--accent,#e53e3e)">打电话：供电公司</h4><p>商铺供电容量、是否需增容、峰谷电价</p></div></div>
    <div class="st p"><div class="sn">7</div><div class="tx"><h4>打电话：发改委</h4><p>备案流程和补贴申请资格</p></div></div>
    <div class="st p"><div class="sn">8</div><div class="tx"><h4>实地考察</h4><p>看现有站点使用率，跟车主聊需求</p></div></div>
  </div>
</div>
<div class="sc">
  <h2>决策框架</h2>
  <div class="df">
    <div class="dc" style="background:#eafaf1;border:1px solid #a3d9b1"><h3 style="font-size:14px;color:#27ae60">做（Go）</h3><p style="color:#555;margin-top:6px;line-height:1.6">电车保有量&gt;500辆<br>供电够（不需大额增容）<br>使用率高</p></div>
    <div class="dc" style="background:#fef9e7;border:1px solid #f9e79f"><h3 style="font-size:14px;color:#d68910">谨慎</h3><p style="color:#555;margin-top:6px;line-height:1.6">保有量200~500辆<br>需一定增容费<br>回收周期3~5年可接受</p></div>
    <div class="dc" style="background:#fdedec;border:1px solid #f5b7b1"><h3 style="font-size:14px;color:#c0392b">不做（No-Go）</h3><p style="color:#555;margin-top:6px;line-height:1.6">保有量&lt;200辆<br>需新增变压器<br>补贴申请不到</p></div>
  </div>
</div>
</div>
<div class="ft">四子王旗充电桩投资调研报告 &middot; 2026年5月 &middot; 数据和图表基于高德地图API / 内蒙古电力集团 / 社交媒体验证</div>
{chart_js}
</body>
</html>"""

    out_path = OUT_DIR + style["filename"]
    desk_path = DESKTOP + style["filename"]
    for p in [out_path, desk_path]:
        with open(p, "w", encoding="utf-8") as f:
            f.write(html)
    print(f"✅ {style_name} → {style['filename']}")

print(f"\n全部4版已生成，共{len(stations)}站")
