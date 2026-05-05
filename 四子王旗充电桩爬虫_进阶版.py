"""
四子王旗充电桩数据爬虫 — 进阶版
=================================
功能：
  1. 高德地图API → 充电站POI + 详情
  2. 百度地图API → 充电站POI（需要百度地图开发者Key）
  3. 蒙电e充小程序模拟 → 站点列表（需抓包获取接口）
  4. 生成数据分析报告

使用方法：
  1. 申请 Key：
     - 高德：https://lbs.amap.com/ → 控制台 → 应用管理 → 创建新应用 → 添加Key（Web服务）
     - 百度：https://lbsyun.baidu.com/ → 控制台 → 应用管理 → 创建应用（服务端）
  2. 填写下方的 API_KEY 和 BAIDU_API_KEY
  3. 运行：python 四子王旗充电桩爬虫_进阶版.py
"""

import requests
import json
import time
import csv
import hashlib
from datetime import datetime
from urllib.parse import quote

# ========== 配置 ==========
GAODE_API_KEY = "你的高德地图API Key"  # ← 替换！
BAIDU_API_KEY = "你的百度地图API Key"   # ← 如需百度地图就替换！
CITY = "四子王旗"


def gaode_search(keyword, city=CITY, page=1):
    """高德地图POI搜索"""
    url = "https://restapi.amap.com/v3/place/text"
    params = {
        "key": GAODE_API_KEY,
        "keywords": keyword,
        "city": city,
        "offset": 20,
        "page": page,
        "extensions": "all",
    }
    resp = requests.get(url, params=params, timeout=10)
    return resp.json()


def gaode_search_around(lon, lat, keyword, radius=5000):
    """高德周边搜索"""
    url = "https://restapi.amap.com/v3/place/around"
    params = {
        "key": GAODE_API_KEY,
        "location": f"{lon},{lat}",
        "keywords": keyword,
        "radius": radius,
        "offset": 20,
        "extensions": "all",
    }
    resp = requests.get(url, params=params, timeout=10)
    return resp.json()


def gaode_detail(poi_id):
    """高德地图POI详情（含评论、照片等）"""
    url = "https://restapi.amap.com/v3/place/detail"
    params = {
        "key": GAODE_API_KEY,
        "id": poi_id,
    }
    resp = requests.get(url, params=params, timeout=10)
    return resp.json()


def baidu_search(query, region=CITY):
    """百度地图POI搜索"""
    url = "https://api.map.baidu.com/place/v2/search"
    params = {
        "ak": BAIDU_API_KEY,
        "q": query,
        "region": region,
        "output": "json",
        "page_size": 20,
        "scope": 2,  # 返回详细信息
    }
    resp = requests.get(url, params=params, timeout=10)
    return resp.json()


def baidu_search_around(lat, lon, query, radius=5000):
    """百度周边搜索"""
    url = "https://api.map.baidu.com/place/v2/search"
    params = {
        "ak": BAIDU_API_KEY,
        "q": query,
        "location": f"{lat},{lon}",
        "radius": radius,
        "output": "json",
        "page_size": 20,
        "scope": 2,
    }
    resp = requests.get(url, params=params, timeout=10)
    return resp.json()


def main():
    print("=" * 60)
    print("四子王旗充电桩数据采集 — 进阶版")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # 检查配置
    if GAODE_API_KEY == "你的高德地图API Key":
        print("⚠️  高德API Key 未设置！")
        print("   请到 https://lbs.amap.com/ 注册并申请 Web服务 Key\n")
        want_gaode = False
    else:
        want_gaode = True

    if BAIDU_API_KEY == "你的百度地图API Key":
        print("⚠️  百度API Key 未设置（可选，不影响高德搜索）")
        want_baidu = False
    else:
        want_baidu = True

    all_stations = []

    # ========== 高德地图搜索 ==========
    if want_gaode:
        print("\n" + "=" * 60)
        print("📡 高德地图 API 搜索")
        print("=" * 60)

        keywords = ["充电站", "充电桩", "蒙电e充"]
        for kw in keywords:
            print(f"\n  搜索：'{kw}'")
            for page in [1, 2]:
                try:
                    data = gaode_search(kw, page=page)
                    if data.get("status") != "1":
                        print(f"    API返回: {data.get('info')}")
                        break
                    pois = data.get("pois", [])
                    if not pois:
                        print(f"    无更多结果")
                        break
                    for poi in pois:
                        biz_ext = poi.get("biz_ext", {})
                        rating = biz_ext.get("rating", "无")
                        cost = biz_ext.get("cost", "无")
                        photos = poi.get("photos", [])
                        photo_urls = [p.get("url", "") for p in photos[:3]]

                        station = {
                            "来源": "高德地图",
                            "名称": poi.get("name", ""),
                            "地址": poi.get("address", ""),
                            "经度": poi.get("location", "").split(",")[0] if poi.get("location") else "",
                            "纬度": poi.get("location", "").split(",")[1] if poi.get("location") else "",
                            "类型": poi.get("type", ""),
                            "电话": poi.get("tel", ""),
                            "评分": rating,
                            "消费": cost,
                            "照片": "; ".join(photo_urls),
                            "POI_ID": poi.get("id", ""),
                        }

                        # 去重
                        if station not in all_stations:
                            all_stations.append(station)
                            print(f"    ✓ {station['名称']}")
                            if rating != "无":
                                print(f"      评分: {rating} | 消费: {cost}")
                    if int(data.get("count", 0)) <= page * 20:
                        break
                    time.sleep(0.3)
                except Exception as e:
                    print(f"    错误: {e}")
                    break

        # 周边搜索（扩大覆盖面）
        print("\n  周边搜索：乌兰花镇中心方圆10km")
        centers = [
            (111.7000, 41.5333, "乌兰花镇中心"),
        ]
        for lon, lat, label in centers:
            try:
                data = gaode_search_around(lon, lat, "充电站", 10000)
                if data.get("status") == "1":
                    pois = data.get("pois", [])
                    for poi in pois:
                        station = {
                            "来源": "高德周边",
                            "名称": poi.get("name", ""),
                            "地址": poi.get("address", ""),
                            "经度": poi.get("location", "").split(",")[0] if poi.get("location") else "",
                            "纬度": poi.get("location", "").split(",")[1] if poi.get("location") else "",
                            "类型": poi.get("type", ""),
                            "电话": poi.get("tel", ""),
                            "评分": poi.get("biz_ext", {}).get("rating", ""),
                            "消费": poi.get("biz_ext", {}).get("cost", ""),
                            "照片": "",
                            "POI_ID": poi.get("id", ""),
                        }
                        if station not in all_stations:
                            all_stations.append(station)
                            print(f"    ✓ {station['名称']} | {station.get('地址', '')}")
                time.sleep(0.3)
            except Exception as e:
                print(f"    错误: {e}")

    # ========== 百度地图搜索 ==========
    if want_baidu:
        print("\n" + "=" * 60)
        print("📡 百度地图 API 搜索")
        print("=" * 60)

        for kw in ["充电站", "充电桩", "蒙电e充"]:
            print(f"\n  搜索：'{kw}'")
            try:
                data = baidu_search(kw)
                if data.get("status") != 0:
                    print(f"    API返回: {data.get('message')}")
                    continue
                results = data.get("results", [])
                for r in results:
                    loc = r.get("location", {})
                    station = {
                        "来源": "百度地图",
                        "名称": r.get("name", ""),
                        "地址": r.get("address", ""),
                        "经度": loc.get("lng", ""),
                        "纬度": loc.get("lat", ""),
                        "类型": r.get("type", ""),
                        "电话": r.get("telephone", ""),
                        "评分": "",
                        "消费": "",
                        "照片": "",
                        "POI_ID": r.get("uid", ""),
                    }
                    if station not in all_stations:
                        all_stations.append(station)
                        print(f"    ✓ {station['名称']}")
                time.sleep(0.3)
            except Exception as e:
                print(f"    错误: {e}")

    # ========== 输出报告 ==========
    print("\n" + "=" * 60)
    print("📊 数据汇总报告")
    print("=" * 60)

    source_count = {}
    for s in all_stations:
        src = s["来源"]
        source_count[src] = source_count.get(src, 0) + 1

    print(f"\n  总记录数: {len(all_stations)}")
    print(f"  数据来源分布:")
    for src, cnt in source_count.items():
        print(f"    - {src}: {cnt} 条")

    if all_stations:
        print(f"\n  {'序号':<4} {'来源':<8} {'名称':<28} {'地址':<30}")
        print("  " + "-" * 75)
        for i, s in enumerate(all_stations, 1):
            name = s['名称'][:26]
            addr = s['地址'][:28]
            src = s['来源'][:6]
            print(f"  {i:<4} {src:<8} {name:<28} {addr:<30}")

        # 保存CSV
        filename = f"四子王旗充电站数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=all_stations[0].keys())
            writer.writeheader()
            writer.writerows(all_stations)
        print(f"\n  ✅ CSV已保存: {filename}")

        # 保存JSON（含完整原始数据）
        json_file = filename.replace(".csv", ".json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(all_stations, f, ensure_ascii=False, indent=2)
        print(f"  ✅ JSON已保存: {json_file}")
    else:
        print("\n  ❌ 未获取到任何数据")
        print("  请检查：")
        print("    1. API Key是否正确（高德Web服务Key，不是Android/iOS Key）")
        print("    2. 网络连接是否正常")
        print("    3. 四子王旗地区在高德地图中是否有充电站标注")

    print("\n" + "=" * 60)
    print("💡 补充建议")
    print("=" * 60)
    print("""
  1. 蒙电e充APP抓包（进阶）：
     - 手机开启代理（如 Charles），安装SSL证书
     - 打开蒙电e充小程序，浏览充电站列表
     - 在抓包工具中查找类似 /station/list 的接口
     - 从中可以获取真实站点的经纬度、忙闲状态、电价等

  2. 手动验证（推荐）：
     打开高德地图APP → 搜索"四子王旗充电站"
     可以直接看到每个站点的：位置、距离、有多少空闲桩
     比API返回的信息更实时
""")


if __name__ == "__main__":
    main()
