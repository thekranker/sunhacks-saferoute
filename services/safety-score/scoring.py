import sqlite3
from shapely.geometry import LineString, Point
from datetime import datetime, timezone

DB_PATH = "data/safety.db"

# Simple severity weights
SEVERITY_WEIGHT = {
    "HOMICIDE": 1.0,
    "ASSAULT": 0.8,
    "ROBBERY": 0.7,
    "BURGLARY": 0.5,
    "THEFT": 0.4,
    "MOTOR VEHICLE THEFT": 0.5,
    "CRIMINAL DAMAGE": 0.3,
}

def days_since(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z",""))
    except Exception:
        return 365
    delta = datetime.now(timezone.utc) - dt.replace(tzinfo=timezone.utc)
    return delta.days

def score_route(points, buffer_m=50):
    """
    points: list of dicts [{"lat":.., "lon":..}, ...]
    buffer_m: radius (in meters) around the route to consider
    """
    line = LineString([(p["lon"], p["lat"]) for p in points])
    # Approximate buffer in degrees (good enough for demo)
    deg_buffer = buffer_m / 111_000  # ~111km per degree
    route_buffer = line.buffer(deg_buffer)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT incident_type, latitude, longitude, datetime FROM incidents LIMIT 5000;")
    rows = cur.fetchall()
    con.close()

    total_risk = 0.0
    breakdown = {}
    for itype, lat, lon, dt in rows:
        if lat is None or lon is None:
            continue
        pt = Point(lon, lat)
        if not route_buffer.contains(pt):
            continue
        sev = SEVERITY_WEIGHT.get(itype.upper(), 0.3)
        rec = max(0.1, 1 / (1 + days_since(dt)))  # decay older crimes
        risk = sev * rec
        total_risk += risk
        breakdown[itype] = breakdown.get(itype, 0) + 1

    # Normalize to 0..1 safety score
    safety = 1 / (1 + total_risk)
    return round(safety, 3), breakdown
