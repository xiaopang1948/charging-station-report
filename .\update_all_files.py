"""批量更新所有文件中的旧坐标为新的充电桩位置坐标"""
import os

path = "D:/bl/.claude/projects/C--Users-bl/memory/charging_station_project/"

NEW_COORDS_LON = "111.69113591"
NEW_COORDS_LAT = "41.51879906"
NEW_LABEL = "高油房路（充电桩规划位）"

# Files that use the old 111.7030, 41.5270 format (Python generators + old HTML reports)
files_to_update_old_coords = [
    "充电桩报告_中文政务.html",
    "充电桩报告_数据新闻.html",
    "充电桩报告_极简商务.html",
    "充电桩报告_深色科技.html",
    "charging_map.html",
]

# Files to update labels from 高油房路南侧 to new label
files_to_update_label = [
    "充电桩报告_中文政务.html",
    "充电桩报告_数据新闻.html",
    "充电桩报告_极简商务.html",
    "充电桩报告_深色科技.html",
]

for fname in files_to_update_old_coords:
    fpath = os.path.join(path, fname)
    if not os.path.exists(fpath):
        print(f"SKIP (not found): {fname}")
        continue
    with open(fpath, encoding="utf-8") as f:
        content = f.read()

    changed = False
    # Replace [41.5270,111.7030] pattern
    if "41.5270" in content or "111.7030" in content:
        content = content.replace("41.5270", NEW_COORDS_LAT)
        content = content.replace("111.7030", NEW_COORDS_LON)
        changed = True

    for fname2 in files_to_update_label:
        if fname2 == fname:
            content = content.replace("高油房路南侧（商铺）", NEW_LABEL)
            content = content.replace("高油房路南侧", "高油房路")
            changed = True

    if changed:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"UPDATED: {fname}")
    else:
        print(f"NO CHANGE: {fname}")

print("\nDone!")
