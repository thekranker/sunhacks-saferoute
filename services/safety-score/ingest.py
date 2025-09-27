import pandas as pd
import sqlite3
from pathlib import Path

# URL for Chicago crime dataset (limit for hackathon speed)
URL = "https://data.cityofchicago.org/resource/ijzp-q8t2.csv?$limit=5000&$where=date>'2025-06-01T00:00:00'"
DB_PATH = Path("data/safety.db")

def main():
    print("Downloading Chicago dataset...")
    df = pd.read_csv(URL)

    # Keep only what you need
    keep_cols = ["case_number","primary_type","latitude","longitude","date"]
    df = df[keep_cols].dropna()

    df = df.rename(columns={
        "case_number":"id",
        "primary_type":"incident_type",
        "latitude":"latitude",
        "longitude":"longitude",
        "date":"datetime"
    })

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    df.to_sql("incidents", con, if_exists="replace", index=False)
    con.commit(); con.close()
    print("Loaded", len(df), "rows into", DB_PATH)

if __name__ == "__main__":
    main()

