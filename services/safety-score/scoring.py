import sqlite3
from shapely.geometry import LineString, Point
from datetime import datetime, timezone

DB_PATH = "data/safety.db"

# Human-friendly labels (mostly passthrough for FinalCaseTypeTrans)
INCIDENT_LABELS = {
    "Arson/Fire Call": "Arson/Fire",
    "Assault Call": "Assault",
    "Bomb Threat Call": "Bomb Threat",
    "Burglary Call": "Burglary",
    "Criminal Information Call": "Criminal Info",
    "Criminal Damage Call": "Criminal Damage",
    "Drugs Call": "Drugs/Alcohol",
    "Drunk Driver Call": "DUI / Drunk Driver",
    "Extra Patrol Request Call": "Extra Patrol",
    "Drunk Disturbing Call": "Public Intoxication",
    "Fight Call": "Fight / Altercation",
    "Robbery Call": "Robbery",
    "Runaway Juvenile Call": "Runaway Juvenile",
    "Sexual Abuse Call": "Sexual Abuse",
    "Shooting Call": "Shooting",
    "Shots Fired Call": "Shots Fired",
    "Stolen Vehicle Call": "Stolen Vehicle",
    "Suspicious Person/Vehicle Call": "Suspicious Person/Vehicle",
    "Theft/Burglary From Vehicle Call": "Vehicle Theft/Burglary",
    "Unknown Trouble Call": "Unknown Trouble",
}

# Severity weights tuned for pedestrian safety context
SEVERITY_WEIGHT = {
    "Arson/Fire Call": 0.7,
    "Assault Call": 0.9,
    "Bomb Threat Call": 0.95,
    "Burglary Call": 0.6,
    "Criminal Information Call": 0.2,
    "Criminal Damage Call": 0.4,
    "Drugs Call": 0.5,
    "Drunk Driver Call": 0.3,
    "Extra Patrol Request Call": 0.1,
    "Drunk Disturbing Call": 0.3,
    "Fight Call": 0.7,
    "Robbery Call": 0.8,
    "Runaway Juvenile Call": 0.2,
    "Sexual Abuse Call": 1.0,
    "Shooting Call": 1.0,
    "Shots Fired Call": 0.9,
    "Stolen Vehicle Call": 0.4,
    "Suspicious Person/Vehicle Call": 0.3,
    "Theft/Burglary From Vehicle Call": 0.5,
    "Unknown Trouble Call": 0.2,
}

def days_since(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", ""))
    except Exception:
        return 365
    delta = datetime.now(timezone.utc) - dt.replace(tzinfo=timezone.utc)
    return delta.days

def friendly_breakdown(breakdown):
    """Convert raw incident_type to user-friendly labels"""
    return {
        INCIDENT_LABELS.get(k.strip(), k.strip()): v
        for k, v in breakdown.items()
    }

def score_route(points, buffer_m=50):
    """
    points: list of dicts [{"lat":.., "lon":..}, ...]
    buffer_m: radius (in meters) around the route to consider
    """
    if len(points) < 2:
        point = Point(points[0]["lon"], points[0]["lat"])
        deg_buffer = buffer_m / 111_000  # rough deg-to-m conversion
        route_buffer = point.buffer(deg_buffer)
    else:
        line = LineString([(p["lon"], p["lat"]) for p in points])
        deg_buffer = buffer_m / 111_000
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
        sev = SEVERITY_WEIGHT.get(itype.strip(), 0.2)  # default to low severity
        rec = max(0.1, 1 / (1 + days_since(dt)))       # decay older crimes
        risk = sev * rec
        total_risk += risk
        breakdown[itype.strip()] = breakdown.get(itype.strip(), 0) + 1

    # Normalize to 0..1 safety score
    safety = 1 / (1 + total_risk)
    return round(safety, 3), friendly_breakdown(breakdown)
