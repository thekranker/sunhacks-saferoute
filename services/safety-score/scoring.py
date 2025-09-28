import sqlite3
import math
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

# Improved severity weights - more balanced and less harsh
SEVERITY_WEIGHT = {
    # High impact on pedestrian safety
    "Assault Call": 0.8,
    "Sexual Abuse Call": 0.9,
    "Shooting Call": 0.9,
    "Shots Fired Call": 0.7,
    "Robbery Call": 0.7,
    "Fight Call": 0.6,
    
    # Moderate impact
    "Arson/Fire Call": 0.5,
    "Bomb Threat Call": 0.6,  # Reduced from 0.95 - often false alarms
    "Burglary Call": 0.4,      # Reduced - primarily property crime
    "Criminal Damage Call": 0.3,
    "Drugs Call": 0.3,        # Reduced - often non-violent
    "Theft/Burglary From Vehicle Call": 0.3,
    "Stolen Vehicle Call": 0.3,
    "Drunk Driver Call": 0.4, # Increased - traffic safety concern
    
    # Low impact - administrative/minor
    "Criminal Information Call": 0.1,
    "Extra Patrol Request Call": 0.05,  # Actually positive - more patrol
    "Drunk Disturbing Call": 0.2,
    "Runaway Juvenile Call": 0.1,
    "Suspicious Person/Vehicle Call": 0.2,
    "Unknown Trouble Call": 0.15,
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

def calculate_route_length(points):
    """Calculate approximate route length in kilometers"""
    if len(points) < 2:
        return 0.1  # Minimum length for single point
    
    total_length = 0.0
    for i in range(1, len(points)):
        # Haversine distance formula for lat/lon points
        lat1, lon1 = math.radians(points[i-1]["lat"]), math.radians(points[i-1]["lon"])
        lat2, lon2 = math.radians(points[i]["lat"]), math.radians(points[i]["lon"])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        total_length += 6371 * c  # Earth's radius in km
    
    return max(total_length, 0.1)  # Minimum 0.1 km

def time_decay_factor(days_ago):
    """Improved time decay - less aggressive than original"""
    if days_ago <= 7:
        return 1.0  # Recent incidents (1 week) - full weight
    elif days_ago <= 30:
        return 0.8  # Last month - 80% weight
    elif days_ago <= 90:
        return 0.6  # Last 3 months - 60% weight
    elif days_ago <= 180:
        return 0.4  # Last 6 months - 40% weight
    elif days_ago <= 365:
        return 0.2  # Last year - 20% weight
    else:
        return 0.1  # Older than 1 year - 10% weight

def score_route(points, buffer_m=50):
    """
    Improved safety scoring algorithm with better normalization and less harsh penalties
    
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

    # Calculate route length for normalization
    route_length_km = calculate_route_length(points)
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT incident_type, latitude, longitude, datetime FROM incidents LIMIT 5000;")
    rows = cur.fetchall()
    con.close()

    # Count incidents by severity category
    high_severity_incidents = 0
    moderate_severity_incidents = 0
    low_severity_incidents = 0
    breakdown = {}
    
    for itype, lat, lon, dt in rows:
        if lat is None or lon is None:
            continue
        pt = Point(lon, lat)
        if not route_buffer.contains(pt):
            continue
            
        # Get severity weight
        severity = SEVERITY_WEIGHT.get(itype.strip(), 0.15)
        time_factor = time_decay_factor(days_since(dt))
        
        # Categorize incidents
        if severity >= 0.6:
            high_severity_incidents += time_factor
        elif severity >= 0.3:
            moderate_severity_incidents += time_factor
        else:
            low_severity_incidents += time_factor
            
        breakdown[itype.strip()] = breakdown.get(itype.strip(), 0) + 1

    # Normalize by route length (incidents per km)
    high_per_km = high_severity_incidents / route_length_km
    moderate_per_km = moderate_severity_incidents / route_length_km
    low_per_km = low_severity_incidents / route_length_km
    
    # Calculate weighted risk score with diminishing returns
    # Using logarithmic scaling to prevent extreme penalties
    risk_score = (
        high_per_km * 0.6 +           # High severity incidents have most impact
        moderate_per_km * 0.3 +       # Moderate severity
        low_per_km * 0.1              # Low severity incidents have minimal impact
    )
    
    # Apply logarithmic scaling to prevent extreme penalties
    # This ensures even high-crime areas don't get completely unusable scores
    if risk_score > 0:
        normalized_risk = math.log(1 + risk_score) / math.log(1 + 10)  # Scale to 0-1 range
    else:
        normalized_risk = 0
    
    # Convert to safety score (0.1 to 1.0 range)
    # Even the worst areas get at least 0.1 (10% safety score)
    safety_score = 0.1 + 0.9 * (1 - normalized_risk)
    
    # Add small bonus for routes with extra patrol requests (indicates police presence)
    patrol_bonus = min(0.05, breakdown.get("Extra Patrol Request Call", 0) * 0.01)
    safety_score = min(1.0, safety_score + patrol_bonus)
    
    return round(safety_score, 3), friendly_breakdown(breakdown)
