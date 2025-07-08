#!/usr/bin/env python3
"""
Daily delta-loader for synthetic Fitbit CSVs.

Supports 4 intraday shapes produced by Wearipedia:

1.  timestamp,value                           (hr.csv after flatten.py)
2.  date,time,<value|steps|minutes>           (azm etc.)
3.  dateTime,value | dateTime,steps           (activity daily total)
4.  single JSON column whose payload holds
    a .dataset list (rare – not used after flatten.py)

On every run we load only rows with ts > last_ts stored in
/checkpoint/last_run.json.
"""

from __future__ import annotations
import os, pathlib, json, ast, io, datetime as dt
from typing import Any, Dict, List

import pandas as pd
import psycopg2


# config
DATA_DIR       = pathlib.Path(os.getenv("DATA_DIR", "/data"))   # mounted CSVs
CHECKPOINT_F   = pathlib.Path("/checkpoint/last_run.json")      # volume
PARTICIPANT_ID = 1


#postgres helpers
def pg_conn():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "db"),
        port=os.getenv("PGPORT", 5432),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres"),
        dbname=os.getenv("PGDATABASE", "wearables"),
    )


def ensure_schema() -> None:
    with pg_conn() as c, c.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_data (
              ts           TIMESTAMPTZ NOT NULL,
              participant  INT         NOT NULL,
              metric       TEXT        NOT NULL,
              value        DOUBLE PRECISION,
              PRIMARY KEY (ts, participant, metric)
            );
            SELECT create_hypertable('raw_data','ts', if_not_exists => TRUE);
            """
        )


def copy_df(df: pd.DataFrame) -> None:
    """Bulk COPY into TimescaleDB (duplicates impossible due to PK + delta)."""
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False)
    buf.seek(0)
    with pg_conn() as c, c.cursor() as cur:
        cur.copy_expert(
            "COPY raw_data (ts, participant, metric, value) FROM STDIN WITH CSV",
            buf,
        )
        c.commit()


#json helpeers
def _safe_load(cell: str | Any) -> Any:
    if not isinstance(cell, str):
        return cell
    try:
        return json.loads(cell)
    except json.JSONDecodeError:
        return ast.literal_eval(cell)


def _first_dataset(node: Any) -> List[Dict]:
    """DFS until we find .dataset list; return []."""
    if isinstance(node, dict):
        if "dataset" in node and isinstance(node["dataset"], list):
            return node["dataset"]
        for v in node.values():
            ds = _first_dataset(v)
            if ds:
                return ds
    elif isinstance(node, list):
        for v in node:
            ds = _first_dataset(v)
            if ds:
                return ds
    return []


# normalizer
def normalise(raw: pd.DataFrame, metric: str) -> pd.DataFrame:
    """
    Return tidy df [timestamp,value] UTC-naïve.
    Raises ValueError on unrecognised schema.
    """

    # already tidy
    if {"timestamp", "value"}.issubset(raw.columns):
        tidy = raw[["timestamp", "value"]]

    # separate date + time cols
    elif {"date", "time"}.issubset(raw.columns):
        vcol = (
            "steps"
            if {"steps"}.issubset(raw.columns)
            else "value"
        )
        tidy = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(raw["date"] + " " + raw["time"]),
                "value": raw[vcol].astype(float),
            }
        )

    #  combined dateTime
    elif "dateTime" in raw.columns:
        if "minutes" in raw.columns:            # SpO₂  (minutes is JSON list)
            rows: List[Dict] = []
            for _, row in raw.iterrows():
                for rec in _safe_load(row["minutes"]):
                    rows.append(
                        {
                            "timestamp": pd.to_datetime(rec["minute"]),
                            "value": float(rec["value"]),
                        }
                    )
            tidy = pd.DataFrame(rows)
        else:                                   # activity daily total
            vcol = "steps" if "steps" in raw.columns else "value"
            tidy = pd.DataFrame(
                {
                    "timestamp": pd.to_datetime(raw["dateTime"]),
                    "value": raw[vcol].astype(float),
                }
            )

    # single JSON payload column (pre-flatten archive – rarely hit)
    elif raw.shape[1] == 1:
        blob = _safe_load(raw.iloc[0, 0])
        date = (
            blob.get("dateTime")
            or blob.get("date")
            or blob.get("activities-heart", [{}])[0].get("dateTime")
            or ""
        )
        rows = []
        for rec in _first_dataset(blob):
            t   = rec.get("time") or rec.get("minute") or "00:00:00"
            val = rec.get("value") or rec.get("steps") or rec.get("minutes") or 0
            rows.append({"timestamp": pd.to_datetime(f"{date} {t}"), "value": float(val)})
        tidy = pd.DataFrame(rows)

    else:
        raise ValueError(f"{metric}.csv: unknown columns {list(raw.columns)}")

    # final clean-up
    tidy["timestamp"] = pd.to_datetime(tidy["timestamp"], utc=True).dt.tz_convert(None)
    tidy["value"] = tidy["value"].astype(float)
    return tidy.sort_values("timestamp")


#checkpoint helpers
def load_checkpoint() -> dt.datetime:
    if CHECKPOINT_F.exists():
        ts = pd.to_datetime(json.load(open(CHECKPOINT_F))["last_ts"])
        return ts.tz_localize(None)
    return dt.datetime(1970, 1, 1)


def save_checkpoint(ts: dt.datetime) -> None:
    CHECKPOINT_F.write_text(json.dumps({"last_ts": ts.isoformat()}))


# main
def main() -> None:
    ensure_schema()
    last_ts = load_checkpoint()

    for csv in DATA_DIR.glob("*.csv"):
        metric = csv.stem.lower()
        raw = pd.read_csv(csv)

        try:
            tidy = normalise(raw, metric)
        except ValueError as e:
            print("WARNING:", e)
            continue

        new_rows = tidy[tidy["timestamp"] > last_ts]
        if new_rows.empty:
            continue

        new_rows.insert(1, "participant", PARTICIPANT_ID)
        new_rows.insert(2, "metric", metric)
        copy_df(new_rows)
        print(f"Ingested {len(new_rows):,} rows → {metric}")

    save_checkpoint(dt.datetime.utcnow())
    print("ingestion complete")


if __name__ == "__main__":
    main()
