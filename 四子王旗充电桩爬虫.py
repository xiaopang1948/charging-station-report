"""
四子王旗充电桩数据爬虫
========================
使用方法：
1. 去 https://lbs.amap.com/ 注册高德地图开发者，免费申请 Web 服务 API Key
2. 将下方 API_KEY 替换为你申请的 Key
3. 运行：python 四子王旗充电桩爬虫.py
"""

import requests
import json
import time
import csv
from datetime import datetime

# ========== 配置 ==========
API_KEY = "fb92a6ada826d39b314f55877534aff4"
CITY = "四子王旗"
KEYWORDS = ["充电站", "充电桩", "电动汽车充电"]

# 四子王旗经纬度范围（乌兰花镇中心）
LAT_CENTER = 41.5333
LON_CENTER = 111.7000
RADIUS = 10000  # 10公里


def search_poi(keyword, page=1):
    """调用高德地图POI搜索API"""
    url = "https://restapi.amap.com/v3/place/text"
    params = {
        "key": API_KEY,
        "keywords": keyword,
        "city": CITY,
        "offset": 20,  # 每页20条
        "page": page,
        "extensions": "all",  # 返回详细信息
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("status") == "1":
            return data
        else:
            print(f"  API错误: {data.get('info')}")
            return None
    except Exception as e:
        print(f"  请求失败: {e}")
        return None


def search_around(lon, lat, keyword, radius=3000):
    """周边搜索——按经纬度范围搜索充电站"""
    url = "https://restapi.amap.com/v3/place/around"
    params = {
        "key": API_KEY,
        "location": f"{lon},{lat}",
        "keywords": keyword,
        "radius": radius,
        "offset": 20,
        "extensions": "all",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("status") == "1":
            return data
        return None
    except Exception as e:
        print(f"  周边搜索失败: {e}")
        return None


def parse_charger_info(poi):
    """解析单个充电站信息"""
    photos = poi.get("photos", [])
    photo_urls = [p.get("url", "") for p in photos] if photos else []

    tel = poi.get("tel", "")
    if isinstance(tel, list):
        tel = "; ".join(tel)

    return {
        "名称": poi.get("name", ""),
        "地址": poi.get("address", ""),
        "经度": poi.get("location", "").split(",")[0] if poi.get("location") else "",
        "纬度": poi.get("location", "").split(",")[1] if poi.get("location") else "",
        "距离(米)": poi.get("distance", ""),
        "类型": poi.get("type", ""),
        "营业时间": poi.get("business_area", ""),
        "电话": tel,
        "网站": poi.get("website", ""),
        "评分": poi.get("biz_ext", {}).get("rating", ""),
        "人均消费": poi.get("biz_ext", {}).get("cost", ""),
        "照片": "; ".join(photo_urls[:3]),  # 只取前3张
    }


def main():
    print("=" * 60)
    print("四子王旗充电桩数据采集")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if API_KEY == "你的高德地图API Key":
        print("\n⚠️  请先在高德地图开放平台 (https://lbs.amap.com/) 免费注册并申请 Key")
        print("   然后将脚本中的 API_KEY 替换为你自己的 Key\n")
        return

    all_pois = []

    # 方式1：关键词搜索
    print("\n▶ 方式1：关键词搜索")
    for kw in KEYWORDS:
        print(f"  搜索关键词：{kw}")
        page = 1
        while True:
            data = search_poi(kw, page=page)
            if not data:
                break
            pois = data.get("pois", [])
            if not pois:
                break
            for poi in pois:
                info = parse_charger_info(poi)
                if info not in all_pois:
                    all_pois.append(info)
                    print(f"    ✓ {info['名称']} | {info['地址']}")
            total = int(data.get("count", 0))
            if page * 20 >= total:
                break
            page += 1
            time.sleep(0.5)  # QPS控制

    # 方式2：周边搜索（以乌兰花镇中心为原点）
    print("\n▶ 方式2：周边搜索（乌兰花镇中心10公里范围）")
    data = search_around(LON_CENTER, LAT_CENTER, "充电站", RADIUS)
    if data:
        pois = data.get("pois", [])
        for poi in pois:
            info = parse_charger_info(poi)
            if info not in all_pois:
                all_pois.append(info)
                print(f"    ✓ {info['名称']} | {info['地址']}")

    # 输出结果
    print(f"\n{'=' * 60}")
    print(f"共找到 {len(all_pois)} 个充电站/充电桩相关POI")
    print('=' * 60)

    if all_pois:
        # 打印表格
        print(f"\n{'序号':<4} {'名称':<30} {'地址':<30} {'电话':<15}")
        print("-" * 80)
        for i, poi in enumerate(all_pois, 1):
            name = poi['名称'][:28]
            addr = poi['地址'][:28]
            tel = poi['电话'][:13]
            print(f"{i:<4} {name:<30} {addr:<30} {tel:<15}")

        # 保存到CSV文件
        filename = f"四子王旗充电站数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=all_pois[0].keys())
            writer.writeheader()
            writer.writerows(all_pois)
        print(f"\n✅ 数据已保存到：{filename}")
    else:
        print("\n❌ 未找到充电站数据，可能原因：")
        print("  1. API Key无效或未设置")
        print("  2. 四子王旗地区数据在高德地图中标注不全")
        print("  3. 搜不到可以试试搜索'蒙电e充'")


if __name__ == "__main__":
    main()
