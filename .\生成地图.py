"""
生成四子王旗充电站地图HTML（非f-string方式，避免大括号冲突）
"""
import json

DATA_PATH = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/stations_data.json"
OUT_PATH = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/charging_map.html"
DESKTOP_PATH = "C:/Users/bl/Desktop/charging_map.html"

with open(DATA_PATH, encoding="utf-8") as f:
    stations = json.load(f)

brand_list = ['蒙电e充', '星星充电', '蒙来电', '蒙马(高速)', '咔咔电姆', '驴充充', '云快充', '其他']
for s in stations:
    s['bi'] = brand_list.index(s['brand']) if s['brand'] in brand_list else 7

data_json = json.dumps(stations, ensure_ascii=False)

# 读取模板
template = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>四子王旗充电站分布地图</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.css" />
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; font-family:'Microsoft YaHei',sans-serif; }
body { display:flex; height:100vh; }
#map { flex:1; height:100vh; }
#sidebar { width:400px; padding:16px; overflow-y:auto; background:#f8f9fa; border-left:1px solid #dee2e6; }
h2 { font-size:16px; margin-bottom:12px; color:#333; }
.stat-box { background:#fff; border-radius:8px; padding:12px; margin-bottom:12px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }
.stat-row { display:flex; justify-content:space-between; margin-bottom:6px; font-size:13px; }
.stat-row .label { color:#666; }
.stat-row .value { font-weight:bold; color:#333; }
.brand-tag { display:inline-block; padding:2px 8px; border-radius:10px; font-size:11px; color:#fff; margin:1px; }
.b0 { background:#4361ee; } .b1 { background:#f72585; } .b2 { background:#7209b7; }
.b3 { background:#e76f51; } .b4 { background:#2a9d8f; } .b5 { background:#e9c46a; color:#333; }
.b6 { background:#264653; } .b7 { background:#8d99ae; }
.station-list { list-style:none; }
.station-item { background:#fff; border-radius:6px; padding:10px 12px; margin-bottom:6px; box-shadow:0 1px 2px rgba(0,0,0,0.06); cursor:pointer; font-size:13px; }
.station-item:hover { box-shadow:0 2px 8px rgba(0,0,0,0.15); }
.station-item .sname { font-weight:bold; font-size:13px; }
.station-item .sinfo { color:#888; font-size:11px; margin-top:3px; }
.distance-bar { display:inline-block; height:6px; border-radius:3px; background:#e9ecef; margin-right:6px; vertical-align:middle; }
.active { background:#e3f2fd !important; }
#search-box { width:100%; padding:8px 12px; border:1px solid #ddd; border-radius:6px; font-size:13px; margin-bottom:10px; }
.warning { background:#fff3cd; border:1px solid #ffc107; border-radius:6px; padding:10px; margin-bottom:12px; font-size:13px; }
</style>
</head>
<body>
<div id="map"></div>
<div id="sidebar">
  <h2>数据概览</h2>
  <div class="stat-box" id="stats">加载中...</div>
  <div class="warning">红点=商铺 | 虚线圈=500m/1km/3km</div>
  <h2>附近站点（由近到远）</h2>
  <input id="search-box" type="text" placeholder="搜索站点..." oninput="filterStations(this.value)">
  <ul class="station-list" id="stationList">加载中...</ul>
</div>
<script>
var colorMap = {
  '蒙电e充':'#4361ee','星星充电':'#f72585','蒙来电':'#7209b7',
  '蒙马(高速)':'#e76f51','咔咔电姆':'#2a9d8f','驴充充':'#e9c46a',
  '云快充':'#264653','其他':'#8d99ae'
};
var brands = ['蒙电e充','星星充电','蒙来电','蒙马(高速)','咔咔电姆','驴充充','云快充','其他'];
var shop = [41.51879906, 111.69113591];

var map = L.map('map').setView([41.53, 111.70], 13);
L.tileLayer('https://webrd01.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
  attribution: '&copy; 高德地图', maxZoom: 18
}).addTo(map);

L.marker(shop, {
  icon: L.divIcon({
    html: '<div style="background:#e63946;width:30px;height:30px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.3);text-align:center;line-height:30px;font-size:16px">S</div>',
    className: '', iconSize: [30,30], iconAnchor: [15,15]
  })
}).addTo(map).bindTooltip('<b>高油房路南侧（商铺）</b>');

[{r:500,c:'#e63946'},{r:1000,c:'#f4a261'},{r:3000,c:'#2a9d8f'}].forEach(function(d) {
  L.circle(shop, {radius:d.r, color:d.c, fill:false, weight:1.5, dashArray:'5,8', opacity:0.5}).addTo(map);
});

var stations = __DATA__;

stations.forEach(function(s) {
  var color = colorMap[s.brand] || '#8d99ae';
  var sz = s.distance < 1 ? 26 : s.distance < 3 ? 22 : 18;
  var m = L.marker([s.lat, s.lng], {
    icon: L.divIcon({
      html: '<div style="background:'+color+';width:'+sz+'px;height:'+sz+'px;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.2);text-align:center;line-height:'+sz+'px;font-size:'+(sz*0.45)+'px">+</div>',
      className: '', iconSize: [sz,sz], iconAnchor: [sz/2, sz/2]
    })
  }).addTo(map);
  m.bindTooltip('<b>'+s.name+'</b><br><span style="color:'+color+'">'+s.brand+'</span> | '+s.distance.toFixed(2)+'km');
});

function renderStats() {
  var n = stations.length;
  var r500 = stations.filter(function(s){return s.distance<=0.5}).length;
  var r1k = stations.filter(function(s){return s.distance<=1}).length;
  var r3k = stations.filter(function(s){return s.distance<=3}).length;
  var r5k = stations.filter(function(s){return s.distance<=5}).length;
  var bc = {};
  stations.forEach(function(s){bc[s.brand]=(bc[s.brand]||0)+1;});
  var bhtml = '';
  var bi = 0;
  for (var b in bc) {
    bhtml += '<span class="brand-tag b'+(bi%8)+'">'+b+' '+bc[b]+'</span> ';
    bi++;
  }
  document.getElementById('stats').innerHTML =
    '<div class="stat-row"><span class="label">站点总数</span><span class="value">'+n+'</span></div>' +
    '<div class="stat-row"><span class="label" style="color:#e63946">500m内</span><span class="value">'+r500+'</span></div>' +
    '<div class="stat-row"><span class="label" style="color:#f4a261">1km内</span><span class="value">'+r1k+'</span></div>' +
    '<div class="stat-row"><span class="label" style="color:#2a9d8f">3km内</span><span class="value">'+r3k+'</span></div>' +
    '<div class="stat-row"><span class="label">镇区(5km)</span><span class="value">'+r5k+'</span></div>' +
    '<div style="margin-top:8px;padding-top:8px;border-top:1px solid #eee">'+bhtml+'</div>';
}

function renderList(arr) {
  var sorted = arr.slice().sort(function(a,b){return a.distance-b.distance;});
  var html = '';
  sorted.forEach(function(s) {
    var w = Math.max(8, 180 - s.distance * 12);
    html += '<li class="station-item" onclick="map.setView(['+s.lat+','+s.lng+'],15)">' +
      '<div class="sname"><span class="brand-tag b'+s.bi+'">'+s.brand+'</span> '+s.name+'</div>' +
      '<div class="sinfo">' +
      '<span class="distance-bar" style="width:'+w+'px;opacity:0.4"></span> ' +
      s.distance.toFixed(2)+'km' +
      (s.rating && s.rating!=='[]' && s.rating!=='0.0' ? ' | 评分 '+s.rating : '') +
      '</div></li>';
  });
  document.getElementById('stationList').innerHTML = html;
}

function filterStations(q) {
  if (!q) { renderList(stations); return; }
  renderList(stations.filter(function(s){return s.name.indexOf(q)>=0||s.brand.indexOf(q)>=0;}));
}

renderStats();
renderList(stations);
</script>
</body>
</html>"""

html = template.replace('__DATA__', data_json)

for path in [OUT_PATH, DESKTOP_PATH]:
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

print("地图已生成!")
print("项目目录:", OUT_PATH)
print("桌面:", DESKTOP_PATH)
print("站点数:", len(stations))

# 验证生成的HTML是否有效
with open(OUT_PATH, encoding="utf-8") as f:
    content = f.read()
if '__DATA__' not in content and 'stations_data.json' not in content:
    print("验证: 数据已嵌入HTML ✅")
else:
    print("验证: 数据未正确嵌入 ❌")
