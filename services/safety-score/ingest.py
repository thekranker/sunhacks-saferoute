import pandas as pd
import sqlite3
from pathlib import Path
import requests
import io

URL = "https://hub.arcgis.com/api/v3/datasets/d2937ee4e83140559d94080237a6e84c_0/downloads/data?format=csv&spatialRefId=4326&where=1%3D1"
DB_PATH = Path("data/safety.db")

VALID_CATEGORIES = {
    "Arson/Fire Call",
    "Assault Call",
    "Bomb Threat Call",
    "Burglary Call",
    "Criminal Information Call",
    "Criminal Damage Call",
    "Drugs Call",
    "Drunk Driver Call",
    "Extra Patrol Request Call",
    "Drunk Disturbing Call",
    "Fight Call",
    "Robbery Call",
    "Runaway Juvenile Call",
    "Sexual Abuse Call",
    "Shooting Call",
    "Shots Fired Call",
    "Stolen Vehicle Call",
    "Suspicious Person/Vehicle Call",
    "Theft/Burglary From Vehicle Call",
    "Unknown Trouble Call",
}

def download_csv(url: str) -> pd.DataFrame:
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))

def main():
    print("📥 Downloading Tempe dataset...")
    df = download_csv(URL)
    print(f"✅ Loaded {len(df)} rows total")

    # Ensure OccurrenceYear is int
    df["OccurrenceYear"] = pd.to_numeric(df["OccurrenceYear"], errors="coerce")

    # Filter for 2025 only
    df = df[df["OccurrenceYear"] == 2025]

    # Keep only valid categories
    df = df[df["FinalCaseTypeTrans"].isin(VALID_CATEGORIES)]

    if df.empty:
        print("❌ No matching rows found for 2025 + valid categories.")
        return

    # Normalize columns
    keep_cols = {
        "FinalCaseTypeTrans": "incident_type",
        "Latitude": "latitude",
        "Longitude": "longitude",
        "OccurrenceDatetime": "datetime",
    }
    df = df[list(keep_cols.keys())].rename(columns=keep_cols)

    # Drop rows with missing data
    df = df.dropna(subset=["incident_type", "latitude", "longitude", "datetime"])

    # Save to SQLite (overwrite old DB)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()  # 🔥 remove old database
    con = sqlite3.connect(DB_PATH)
    df.to_sql("incidents", con, if_exists="replace", index=False)
    con.commit(); con.close()

    print(f"✅ Loaded {len(df)} filtered rows into {DB_PATH}")

if __name__ == "__main__":
    main()
