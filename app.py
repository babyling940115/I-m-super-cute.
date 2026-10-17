import asyncio
import math
import random
from datetime import datetime
from typing import Dict, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# ================= 1. 臺灣海峽遠洋公海航道 =================

CORRIDOR_MAINLAND_COAST = [
    {"lat": 26.20, "lon": 120.50},
    {"lat": 25.50, "lon": 119.80},
    {"lat": 24.60, "lon": 118.90},
    {"lat": 23.80, "lon": 118.00},
    {"lat": 22.80, "lon": 116.80},
]

CORRIDOR_STRAIT_CENTER = [
    {"lat": 25.80, "lon": 121.20},
    {"lat": 25.00, "lon": 120.40},
    {"lat": 24.00, "lon": 119.60},
    {"lat": 23.00, "lon": 118.80},
    {"lat": 21.80, "lon": 118.20},
]

CORRIDOR_PENGHU_CHANNEL = [
    {"lat": 24.80, "lon": 120.55},
    {"lat": 24.20, "lon": 120.20},
    {"lat": 23.60, "lon": 119.85},
    {"lat": 22.90, "lon": 119.95},
    {"lat": 22.20, "lon": 120.00},
]

CORRIDOR_EAST_COAST = [
    {"lat": 25.40, "lon": 122.30},
    {"lat": 24.60, "lon": 122.00},
    {"lat": 23.80, "lon": 121.80},
    {"lat": 22.80, "lon": 121.50},
    {"lat": 21.80, "lon": 121.20},
]

CORRIDOR_BASHI_STRAIT = [
    {"lat": 21.60, "lon": 117.50},
    {"lat": 21.55, "lon": 119.20},
    {"lat": 21.60, "lon": 120.80},
    {"lat": 21.70, "lon": 122.50},
    {"lat": 21.80, "lon": 124.00},
]

OFFSHORE_ANCHOR_HOTSPOTS = [
    {
        "lat_min": 22.42,
        "lat_max": 22.55,
        "lon_min": 120.02,
        "lon_max": 120.14,
        "weight": 4,
    },
    {
        "lat_min": 24.25,
        "lat_max": 24.48,
        "lon_min": 118.20,
        "lon_max": 118.55,
        "weight": 4,
    },
    {
        "lat_min": 24.20,
        "lat_max": 24.38,
        "lon_min": 120.26,
        "lon_max": 120.38,
        "weight": 2,
    },
    {
        "lat_min": 23.45,
        "lat_max": 23.65,
        "lon_min": 119.35,
        "lon_max": 119.55,
        "weight": 2,
    },
    {
        "lat_min": 25.18,
        "lat_max": 25.30,
        "lon_min": 121.40,
        "lon_max": 121.75,
        "weight": 2,
    },
]

# ================= 2. 高雄港深水主航槽 =================


def generate_dense_spline(waypoints: list, num_sub: int = 15) -> list:
  dense_path = []
  for i in range(len(waypoints) - 1):
    p1 = waypoints[i]
    p2 = waypoints[i + 1]
    for step in range(num_sub):
      t = step / float(num_sub)
      lat = p1["lat"] + (p2["lat"] - p1["lat"]) * t
      lon = p1["lon"] + (p2["lon"] - p1["lon"]) * t
      dense_path.append({"lat": round(lat, 6), "lon": round(lon, 6)})
  dense_path.append(waypoints[-1])
  return dense_path


RAW_PORT_MAIN_KEYPOINTS = [
    {"lat": 22.6280, "lon": 120.2450},
    {"lat": 22.6200, "lon": 120.2540},
    {"lat": 22.6170, "lon": 120.2640},
    {"lat": 22.6148, "lon": 120.2710},
    {"lat": 22.6115, "lon": 120.2770},
    {"lat": 22.6050, "lon": 120.2840},
    {"lat": 22.5970, "lon": 120.2880},
    {"lat": 22.5890, "lon": 120.2930},
    {"lat": 22.5810, "lon": 120.2980},
    {"lat": 22.5750, "lon": 120.3030},
    {"lat": 22.5690, "lon": 120.3085},
    {"lat": 22.5630, "lon": 120.3135},
    {"lat": 22.5580, "lon": 120.3190},
    {"lat": 22.5560, "lon": 120.3230},
    {"lat": 22.5510, "lon": 120.3140},
    {"lat": 22.5450, "lon": 120.3030},
    {"lat": 22.5390, "lon": 120.2920},
    {"lat": 22.5280, "lon": 120.2800},
]

ROUTE_PORT_MAIN_DENSE = generate_dense_spline(
    RAW_PORT_MAIN_KEYPOINTS, num_sub=15
)

RAW_FERRY_GUSHAN = [
    {"lat": 22.6180, "lon": 120.2680},
    {"lat": 22.6160, "lon": 120.2710},
    {"lat": 22.6140, "lon": 120.2740},
]
ROUTE_FERRY_GUSHAN_DENSE = generate_dense_spline(RAW_FERRY_GUSHAN, num_sub=10)

RAW_PILOT_N = [
    {"lat": 22.6220, "lon": 120.2550},
    {"lat": 22.6170, "lon": 120.2640},
    {"lat": 22.6120, "lon": 120.2760},
    {"lat": 22.6050, "lon": 120.2840},
]
ROUTE_PILOT_N_DENSE = generate_dense_spline(RAW_PILOT_N, num_sub=10)

RAW_PILOT_S = [
    {"lat": 22.5390, "lon": 120.2920},
    {"lat": 22.5450, "lon": 120.3030},
    {"lat": 22.5510, "lon": 120.3140},
    {"lat": 22.5560, "lon": 120.3230},
]
ROUTE_PILOT_S_DENSE = generate_dense_spline(RAW_PILOT_S, num_sub=10)

# ================= 3. 高雄港純水體靜態繫泊點 =================

PORT_PURE_WATER_BERTHS = [
    {"lat": 22.6180, "lon": 120.2760, "type": "passenger"},
    {"lat": 22.6170, "lon": 120.2785, "type": "passenger"},
    {"lat": 22.6155, "lon": 120.2810, "type": "special"},
    {"lat": 22.6085, "lon": 120.2785, "type": "fishing"},
    {"lat": 22.6055, "lon": 120.2805, "type": "special"},
    {"lat": 22.6025, "lon": 120.2825, "type": "cargo"},
    {"lat": 22.5995, "lon": 120.2845, "type": "fishing"},
    {"lat": 22.5965, "lon": 120.2860, "type": "special"},
    {"lat": 22.6075, "lon": 120.2915, "type": "passenger"},
    {"lat": 22.6035, "lon": 120.2935, "type": "special"},
    {"lat": 22.5435, "lon": 120.3400, "type": "fishing"},
    {"lat": 22.5420, "lon": 120.3415, "type": "fishing"},
    {"lat": 22.5405, "lon": 120.3430, "type": "fishing"},
    {"lat": 22.5500, "lon": 120.1200, "type": "tanker"},
    {"lat": 22.5600, "lon": 120.1100, "type": "cargo"},
    {"lat": 22.5400, "lon": 120.1000, "type": "tanker"},
    {"lat": 22.5700, "lon": 120.1300, "type": "cargo"},
    {"lat": 22.5800, "lon": 120.1200, "type": "special"},
    {"lat": 22.5900, "lon": 120.1100, "type": "fishing"},
]

# ================= 4. 船種規範 =================

SHIP_TYPES_DICT = {
    "cargo": {"label": "貨船", "color": "#00b4d8"},
    "tanker": {"label": "油輪", "color": "#ff1493"},
    "fishing": {"label": "漁船", "color": "#0011ff"},
    "passenger": {"label": "客船", "color": "#ffaa00"},
    "special": {"label": "引水/拖駁", "color": "#e60000"},
    "other": {"label": "其他船舶", "color": "#94a3b8"},
}


class PathLockedVessel:

  def __init__(
      self,
      mmsi: int,
      name: str,
      callsign: str,
      imo: int,
      st_type: str,
      is_anchored: bool = False,
      route: list = None,
      exact_coord: dict = None,
      speed_knots: float = 10.0,
      is_port_vessel: bool = False,
  ):
    self.mmsi = mmsi
    self.name = name
    self.callsign = callsign
    self.imo = imo
    self.st_type = st_type
    self.type_name = SHIP_TYPES_DICT[st_type]["label"]
    self.color = SHIP_TYPES_DICT[st_type]["color"]
    self.is_anchored = is_anchored
    self.is_port_vessel = is_port_vessel
    self.sog = 0.0 if is_anchored else round(speed_knots, 1)

    if self.is_anchored:
      if exact_coord:
        self.lat = exact_coord["lat"]
        self.lon = exact_coord["lon"]
        self.cog = float(random.choice([45, 135, 225, 315]))
      else:
        zone = random.choice(OFFSHORE_ANCHOR_HOTSPOTS)
        self.lat = round(random.uniform(zone["lat_min"], zone["lat_max"]), 6)
        self.lon = round(random.uniform(zone["lon_min"], zone["lon_max"]), 6)
        self.cog = float(random.randint(0, 360))
      self.route = []
      self.progress = 0.0
      self.forward = True
    else:
      self.route = route
      self.progress = float(random.randint(0, len(route) - 2)) + random.uniform(
          0.1, 0.9
      )
      self.forward = random.choice([True, False])

      idx = int(self.progress)
      t = self.progress - idx
      p1 = self.route[idx]
      p2 = self.route[min(idx + 1, len(self.route) - 1)]
      self.lat = round(p1["lat"] + (p2["lat"] - p1["lat"]) * t, 6)
      self.lon = round(p1["lon"] + (p2["lon"] - p1["lon"]) * t, 6)

      if not is_port_vessel:
        self.lat += random.uniform(-0.015, 0.015)
        self.lon += random.uniform(-0.015, 0.015)
        if self.lon > 120.15 and 22.40 <= self.lat <= 22.70:
          self.lon = 120.10

      self.cog = float(self.calculate_tangent_bearing())

  def calculate_tangent_bearing(self) -> float:
    idx = int(self.progress)
    lookahead = 2 if self.forward else -2
    next_idx = max(0, min(len(self.route) - 1, idx + lookahead))

    target = self.route[next_idx]
    dlat = target["lat"] - self.lat
    dlon = target["lon"] - self.lon
    bearing = math.degrees(math.atan2(dlon, dlat))
    return (bearing + 360.0) % 360.0

  def move(self, base_step_sea: float, base_step_port: float):
    if self.is_anchored:
      self.sog = 0.0
      return

    step = (base_step_port if self.is_port_vessel else base_step_sea) * (
        self.sog / 10.0
    )
    progress_delta = step * 18.0

    if self.forward:
      self.progress += progress_delta
      if self.progress >= len(self.route) - 1.05:
        self.forward = False
        self.progress = len(self.route) - 1.05
    else:
      self.progress -= progress_delta
      if self.progress <= 0.05:
        self.forward = True
        self.progress = 0.05

    idx = int(self.progress)
    t = self.progress - idx
    p1 = self.route[idx]
    p2 = self.route[min(idx + 1, len(self.route) - 1)]

    self.lat = round(p1["lat"] + (p2["lat"] - p1["lat"]) * t, 6)
    self.lon = round(p1["lon"] + (p2["lon"] - p1["lon"]) * t, 6)

    target_bearing = self.calculate_tangent_bearing()
    diff = (target_bearing - self.cog + 180.0) % 360.0 - 180.0

    max_turn_rate = 6.0 if self.is_port_vessel else 4.5
    if abs(diff) <= max_turn_rate:
      self.cog = target_bearing
    else:
      turn = math.copysign(max_turn_rate, diff)
      self.cog = (self.cog + turn + 360.0) % 360.0


# ================= 5. 建立整合船隊 =================


def build_combined_fleet() -> List[PathLockedVessel]:
  fleet_list = []
  base_mmsi = 412330000
  letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
  idx = 0

  sea_types_ratio = (
      ["cargo"] * 35
      + ["tanker"] * 20
      + ["fishing"] * 22
      + ["passenger"] * 8
      + ["other"] * 8
      + ["special"] * 7
  )
  weighted_sea_routes = (
      [CORRIDOR_MAINLAND_COAST] * 4
      + [CORRIDOR_STRAIT_CENTER] * 3
      + [CORRIDOR_PENGHU_CHANNEL] * 2
      + [CORRIDOR_EAST_COAST] * 2
      + [CORRIDOR_BASHI_STRAIT] * 2
  )

  for _ in range(650):
    st = random.choice(sea_types_ratio)
    mmsi = base_mmsi + idx
    idx += 1
    is_anchored = random.random() < 0.22
    route = random.choice(weighted_sea_routes)
    callsign = "".join(random.choices(letters, k=4))
    imo = (
        0
        if st in ["fishing", "special", "other"]
        else random.randint(9100000, 9999999)
    )
    name = (
        f"CHANGFENG_{mmsi % 1000}"
        if st == "tanker"
        else (
            f"MIN_YU_{mmsi % 10000:04d}"
            if st == "fishing"
            else f"OCEAN_LINE_{mmsi % 1000}"
        )
    )

    fleet_list.append(
        PathLockedVessel(
            mmsi=mmsi,
            name=name,
            callsign=callsign,
            imo=imo,
            st_type=st,
            is_anchored=is_anchored,
            route=route,
            speed_knots=random.uniform(8.5, 16.5),
            is_port_vessel=False,
        )
    )

  for i in range(14):
    st = random.choice(["cargo", "tanker", "special", "cargo"])
    mmsi = base_mmsi + idx
    idx += 1
    name = (
        f"EVER_PORT_{i+1:02d}" if st == "cargo" else f"FORMOSA_OIL_{i+1:02d}"
    )
    fleet_list.append(
        PathLockedVessel(
            mmsi=mmsi,
            name=name,
            callsign=f"BK{random.randint(1000,9999)}",
            imo=random.randint(9100000, 9999999),
            st_type=st,
            is_anchored=False,
            route=ROUTE_PORT_MAIN_DENSE,
            speed_knots=random.uniform(6.5, 8.5),
            is_port_vessel=True,
        )
    )

  for i in range(4):
    mmsi = base_mmsi + idx
    idx += 1
    fleet_list.append(
        PathLockedVessel(
            mmsi=mmsi,
            name=f"旗鼓輪 {i+1} 號",
            callsign=f"FERRY{i+1}",
            imo=0,
            st_type="passenger",
            is_anchored=False,
            route=ROUTE_FERRY_GUSHAN_DENSE,
            speed_knots=5.5,
            is_port_vessel=True,
        )
    )

  for i in range(4):
    mmsi = base_mmsi + idx
    idx += 1
    fleet_list.append(
        PathLockedVessel(
            mmsi=mmsi,
            name=f"高雄引水艇 0{i+1}",
            callsign=f"PILOT{i+1}",
            imo=0,
            st_type="special",
            is_anchored=False,
            route=ROUTE_PILOT_N_DENSE,
            speed_knots=8.0,
            is_port_vessel=True,
        )
    )

  for i in range(3):
    mmsi = base_mmsi + idx
    idx += 1
    fleet_list.append(
        PathLockedVessel(
            mmsi=mmsi,
            name=f"高港引水 2{i+1}",
            callsign=f"PILOT2{i+1}",
            imo=0,
            st_type="special",
            is_anchored=False,
            route=ROUTE_PILOT_S_DENSE,
            speed_knots=7.5,
            is_port_vessel=True,
        )
    )

  for berth in PORT_PURE_WATER_BERTHS:
    mmsi = base_mmsi + idx
    idx += 1
    st = berth["type"]
    fleet_list.append(
        PathLockedVessel(
            mmsi=mmsi,
            name=f"BERTH_{mmsi % 1000:03d}",
            callsign=f"BM{random.randint(1000, 9999)}",
            imo=(
                random.randint(9200000, 9999999)
                if st in ["cargo", "tanker"]
                else 0
            ),
            st_type=st,
            is_anchored=True,
            exact_coord=berth,
            is_port_vessel=True,
        )
    )

  return fleet_list


fleet = build_combined_fleet()

# ================= 6. 前端視圖 =================

HTML_PAGE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="referrer" content="no-referrer">
    <title>高雄港船舶動態監控系統</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft JhengHei", "微軟正黑體", sans-serif; }
        #map { height: 100vh; width: 100vw; background: #c5e4f3; }

        /* 避開左上角原生縮放按鈕 (+-) */
        .system-topbar {
            position: absolute; 
            top: 15px; 
            left: 60px; 
            z-index: 1100;
            display: flex; 
            align-items: center; 
            gap: 8px;
        }

        .toolbox-icon {
            background: rgba(45, 55, 72, 0.90);
            border-radius: 8px;
            width: 42px; height: 42px;
            display: flex; align-items: center; justify-content: center;
            border: 1px solid rgba(255, 255, 255, 0.15);
            cursor: pointer;
            box-shadow: 0 4px 16px rgba(0,0,0,0.35);
        }
        .toolbox-icon svg { width: 22px; height: 22px; fill: #cbd5e1; }

        .system-btn-group {
            background: rgba(45, 55, 72, 0.90);
            backdrop-filter: blur(6px);
            border-radius: 8px;
            padding: 4px 10px;
            display: flex;
            align-items: center;
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 4px 16px rgba(0,0,0,0.35);
        }

        .nav-tool-btn {
            background: transparent;
            border: none;
            color: #ffffff;
            font-size: 13px;
            font-weight: 500;
            padding: 6px 12px;
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            border-right: 1px solid rgba(255, 255, 255, 0.15);
            transition: all 0.2s;
        }
        .nav-tool-btn:last-child { border-right: none; }
        .nav-tool-btn:hover { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }
        .nav-tool-btn svg { width: 16px; height: 16px; fill: #cbd5e1; }

        /* AIS 圖例面板：預設置於工具列下方 */
        .legend-panel {
            position: absolute; 
            top: 70px; 
            left: 60px; 
            z-index: 1000;
            background: rgba(15, 23, 42, 0.94); 
            color: #fff;
            padding: 12px 18px; 
            border-radius: 8px; 
            border: 1px solid rgba(56, 189, 248, 0.4);
            box-shadow: 0 4px 20px rgba(0,0,0,0.5); 
            font-size: 12px; 
            line-height: 1.6;
        }
        .legend-grid {
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 4px 12px; 
            margin-top: 6px; 
            font-size: 12px;
        }
        .legend-item { display: flex; align-items: center; gap: 6px; }
        .legend-dot { width: 10px; height: 10px; border-radius: 2px; }

        .leaflet-marker-icon { transition: none !important; cursor: pointer; }

        .ship-wrap {
            width: 100%; height: 100%;
            display: flex; align-items: center; justify-content: center;
        }
        .symbol-svg {
            width: 100%; height: 100%; overflow: visible;
        }

        .leaflet-popup-content-wrapper {
            padding: 0; background: #ffffff; border-radius: 0px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.45); border: 1px solid #475569; overflow: hidden;
        }
        .leaflet-popup-content { margin: 0; width: 320px !important; font-family: monospace; }
        .leaflet-popup-tip-container { display: none; }
        
        .vessel-dialog-header {
            background: #383838; color: #ffffff; font-size: 13px; font-weight: bold;
            padding: 6px 10px; display: flex; justify-content: space-between; align-items: center;
        }
        .vessel-dialog-header .close-btn { cursor: pointer; color: #ccc; font-size: 16px; }
        .vessel-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .vessel-table tr { border-bottom: 1px solid #cbd5e1; }
        .vessel-table tr:last-child { border-bottom: none; }
        .vessel-table td.label-cell {
            background: #000000; color: #ffffff; font-weight: bold;
            padding: 4px 8px; width: 105px; text-align: right; border-right: 1px solid #64748b;
        }
        .vessel-table td.value-cell { background: #ffffff; color: #000000; padding: 4px 8px; }
    </style>
</head>
<body>
    <div class="system-topbar">
        <div class="toolbox-icon" title="工具箱">
            <svg viewBox="0 0 24 24"><path d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z"/></svg>
        </div>
        <div class="system-btn-group">
            <button class="nav-tool-btn" onclick="toggleLegend()">
                <svg viewBox="0 0 24 24"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/></svg>
                圖例
            </button>
            <button class="nav-tool-btn" onclick="alert('目前使用：臺灣通用電子地圖(NLSC)')">
                <svg viewBox="0 0 24 24"><path d="M20.5 3l-.16.03L15 5.1 9 3 3.36 4.9c-.21.07-.36.25-.36.48V20.5c0 .28.22.5.5.5l.16-.03L9 18.9l6 2.1 5.64-1.9c.21-.07.36-.25.36-.48V3.5c0-.28-.22-.5-.5-.5zM15 19l-6-2.11V5l6 2.11V19z"/></svg>
                底圖
            </button>
            <button class="nav-tool-btn" onclick="searchVessel()">
                <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
                船舶查詢
            </button>
            <button class="nav-tool-btn" id="coords-btn">
                <svg viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
                座標查詢
            </button>
            <button class="nav-tool-btn" onclick="alert('點擊地圖兩點量測距離')">
                <svg viewBox="0 0 24 24"><path d="M21 6H3c-1.1 0-2 .9-2 2v8c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 10H3V8h2v4h2V8h2v4h2V8h2v4h2V8h3v8z"/></svg>
                距離
            </button>
            <button class="nav-tool-btn" onclick="alert('已清除所有航跡歷史')">
                <svg viewBox="0 0 24 24"><path d="M19.36 10.04l-4.7-4.7 1.4-1.4c.78-.78 2.05-.78 2.83 0l1.88 1.88c.78.78.78 2.05 0 2.83l-1.41 1.39zm-6.11-3.29l4.7 4.7-9.88 9.88H3.37v-4.7l9.88-9.88z"/></svg>
                清除軌跡
            </button>
        </div>
    </div>

    <!-- AIS 圖例面板 -->
    <div class="legend-panel" id="legend-panel">
        <b style="color: #38bdf8;">AIS 即時圖例</b> (在海總數: <b id="ship-count" style="color: #4ade80;">0</b> 艘)
        <div class="legend-grid">
            <div class="legend-item"><div class="legend-dot" style="background:#00b4d8;"></div>貨船 (淺藍)</div>
            <div class="legend-item"><div class="legend-dot" style="background:#ff1493;"></div>油輪 (粉紅)</div>
            <div class="legend-item"><div class="legend-dot" style="background:#0011ff;"></div>漁船 (深藍)</div>
            <div class="legend-item"><div class="legend-dot" style="background:#ffaa00;"></div>客船/渡輪 (黃色)</div>
            <div class="legend-item"><div class="legend-dot" style="background:#e60000;"></div>引水/拖駁 (紅色)</div>
            <div class="legend-item"><div class="legend-dot" style="background:#94a3b8;"></div>其他船舶 (灰色)</div>
        </div>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const map = L.map('map', { 
            attributionControl: false 
        }).setView([22.569, 120.308], 14);

        L.tileLayer('https://wmts.nlsc.gov.tw/wmts/EMAP/default/GoogleMapsCompatible/{z}/{y}/{x}', {
            maxZoom: 18,
            minZoom: 6
        }).addTo(map);

        map.on('mousemove', (e) => {
            document.getElementById('coords-btn').innerHTML = `
                <svg viewBox="0 0 24 24" style="width:16px;height:16px;fill:#38bdf8;"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
                ${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}
            `;
        });

        function toggleLegend() {
            const p = document.getElementById('legend-panel');
            p.style.display = (p.style.display === 'none') ? 'block' : 'none';
        }

        function searchVessel() {
            const kw = prompt("請輸入船名或 MMSI 進行定位查詢：");
            if (!kw) return;
            for (let id in markers) {
                const marker = markers[id];
                if (marker._vesselData && (marker._vesselData.name.includes(kw) || marker._vesselData.mmsi.toString().includes(kw))) {
                    map.setView(marker.getLatLng(), 15);
                    marker.openPopup();
                    return;
                }
            }
            alert("查無該船舶！");
        }

        const markers = {};
        let activeMMSI = null;

        function toDMS(degVal) {
            const absolute = Math.abs(degVal);
            const degrees = Math.floor(absolute);
            const minutesNotTruncated = (absolute - degrees) * 60;
            const minutes = Math.floor(minutesNotTruncated);
            const seconds = ((minutesNotTruncated - minutes) * 60).toFixed(2);
            return degrees + '°' + minutes + "'" + seconds + '″';
        }

        function buildPopupContent(v) {
            return `
                <div class="vessel-dialog-header">
                    <span>船舶資料</span>
                    <span class="close-btn" onclick="map.closePopup(); activeMMSI=null;">×</span>
                </div>
                <table class="vessel-table">
                    <tr><td class="label-cell">IMO_Number</td><td class="value-cell">${v.imo}</td></tr>
                    <tr><td class="label-cell">MMSI</td><td class="value-cell">${v.mmsi}</td></tr>
                    <tr><td class="label-cell">船名</td><td class="value-cell">${v.name}</td></tr>
                    <tr><td class="label-cell">呼號</td><td class="value-cell">${v.callsign}</td></tr>
                    <tr><td class="label-cell">船舶種類</td><td class="value-cell">${v.type_name}</td></tr>
                    <tr><td class="label-cell">經度</td><td class="value-cell">${v.lon.toFixed(6)}(${toDMS(v.lon)})</td></tr>
                    <tr><td class="label-cell">緯度</td><td class="value-cell">${v.lat.toFixed(6)}(${toDMS(v.lat)})</td></tr>
                    <tr><td class="label-cell">航向</td><td class="value-cell">${Math.round(v.cog)}°</td></tr>
                    <tr><td class="label-cell">航速</td><td class="value-cell">${v.sog} </td></tr>
                    <tr><td class="label-cell">紀錄時間</td><td class="value-cell">${v.record_time}</td></tr>
                </table>
            `;
        }

        function createMovingChevronSvg(color) {
            return `
            <svg class="symbol-svg" viewBox="0 0 100 160">
                <defs>
                    <clipPath id="hull-clip">
                        <polygon points="50,0 95,45 90,160 50,125 10,160 5,45" />
                    </clipPath>
                </defs>
                <polygon points="50,0 95,45 90,160 50,125 10,160 5,45" 
                         fill="${color}" stroke="#111827" stroke-width="8" stroke-linejoin="round"/>
                <g clip-path="url(#hull-clip)">
                    <polyline points="-10,55 50,10 110,55 110,80 50,35 -10,80" fill="#ffffff" />
                    <polyline points="-10,110 50,65 110,110 110,135 50,90 -10,135" fill="#ffffff" />
                </g>
            </svg>`;
        }

        function createStationaryDiamondSvg(color) {
            return `
            <svg class="symbol-svg" viewBox="0 0 100 100">
                <g transform="rotate(45 50 50)">
                    <rect x="18" y="18" width="64" height="64" rx="4"
                          fill="${color}" stroke="#111827" stroke-width="8" />
                    <circle cx="50" cy="50" r="12" fill="none" stroke="#ffffff" stroke-width="8" />
                </g>
            </svg>`;
        }

        function createAISIcon(v) {
            if (v.sog === 0) {
                const size = 15;
                return L.divIcon({
                    className: '',
                    html: `<div class="ship-wrap" style="transform: rotate(${v.cog}deg); width:${size}px; height:${size}px;">
                             ${createStationaryDiamondSvg(v.color)}
                           </div>`,
                    iconSize: [size, size],
                    iconAnchor: [size / 2, size / 2]
                });
            } else {
                const w = 15;
                const h = 23;
                return L.divIcon({
                    className: '',
                    html: `<div class="ship-wrap" style="transform: rotate(${v.cog}deg); width:${w}px; height:${h}px;">
                             ${createMovingChevronSvg(v.color)}
                           </div>`,
                    iconSize: [w, h],
                    iconAnchor: [w / 2, h / 2]
                });
            }
        }

        map.on('popupclose', () => { activeMMSI = null; });

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

        ws.onmessage = (event) => {
            const vessels = JSON.parse(event.data);
            document.getElementById('ship-count').innerText = vessels.length;

            vessels.forEach(v => {
                const latLng = [v.lat, v.lon];
                const icon = createAISIcon(v);
                const popupHtml = buildPopupContent(v);

                if (markers[v.mmsi]) {
                    markers[v.mmsi].setLatLng(latLng);
                    markers[v.mmsi].setIcon(icon);
                    markers[v.mmsi]._vesselData = v;
                    if (activeMMSI === v.mmsi) {
                        markers[v.mmsi].getPopup().setContent(popupHtml);
                    }
                } else {
                    const marker = L.marker(latLng, { icon: icon }).addTo(map);
                    marker._vesselData = v;
                    const popup = L.popup({ closeButton: false, offset: [0, -10] }).setContent(popupHtml);
                    marker.bindPopup(popup);

                    marker.on('click', () => {
                        activeMMSI = v.mmsi;
                        marker.openPopup();
                    });

                    markers[v.mmsi] = marker;
                }
            });
        };
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
  return HTMLResponse(content=HTML_PAGE, status_code=200)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
  await websocket.accept()
  try:
    while True:
      now_str = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
      data = []
      for v in fleet:
        v.move(base_step_sea=0.0012, base_step_port=0.015)
        data.append({
            "mmsi": v.mmsi,
            "name": v.name,
            "callsign": v.callsign,
            "imo": v.imo,
            "type_name": v.type_name,
            "lat": round(v.lat, 6),
            "lon": round(v.lon, 6),
            "cog": round(v.cog, 1),
            "sog": v.sog,
            "color": v.color,
            "record_time": now_str,
        })
      await websocket.send_json(data)
      await asyncio.sleep(2.0)
  except WebSocketDisconnect:
    pass


if __name__ == "__main__":
  import uvicorn

  uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
