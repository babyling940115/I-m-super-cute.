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
                random.randint(9200000, 9
