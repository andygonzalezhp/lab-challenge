import os, pathlib, pandas as pd, psycopg2, io, json, datetime as dt

DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", "/data"))
STATE_FN = pathlib.Path("/app/last_run.json")
PARTICIPANT_ID = 1

def conn():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "db"),
        port=os.getenv("PGPORT", 5432),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres"),
        dbname=os.getenv("PGDATABASE", "wearables"),
    )

def ensure_schema(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_data (
          ts TIMESTAMPTZ NOT NULL,
          participant INTEGER NOT NULL,
          metric TEXT NOT NULL,
          value DOUBLE PRECISION,
          PRIMARY KEY (ts, participant, metric)
        );
        SELECT create_hypertable('raw_data','ts', if_not_exists => TRUE);
    """)

def copy_df(conn, df):
    buf = io.StringIO()
    df.to_csv(buf, header=False, index=False)
    buf.seek(0)
    with conn.cursor() as cur:
        cur.copy_expert(
            "COPY raw_data (ts, participant, metric, value) FROM STDIN WITH CSV",
            buf,
        )
    conn.commit()

def load_state():
    return json.load(open(STATE_FN)) if STATE_FN.exists() else {"last_ts":"1970-01-01T00:00:00Z"}

def save_state(ts):
    json.dump({"last_ts": ts}, open(STATE_FN,"w"))

def main():
    last_ts = pd.to_datetime(load_state()["last_ts"])
    with conn() as c, c.cursor() as cur:
        ensure_schema(cur)

    for p in DATA_DIR.glob("*.parquet"):
        metric = p.stem
        df = pd.read_parquet(p)
        df = df[df["timestamp"] > last_ts]
        if df.empty: continue
        df.insert(1, "participant", PARTICIPANT_ID)
        df.insert(2, "metric", metric)
        copy_df(conn(), df)
        print(f"Ingested {len(df):,} rows → {metric}")

    save_state(dt.datetime.utcnow().isoformat())
    print("✅ ingestion complete")

if __name__ == "__main__":
    main()
