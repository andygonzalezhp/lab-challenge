from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os, psycopg2, datetime as dt
from datetime import timedelta

app = FastAPI(title="Wearables Read-API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

def get_conn():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "db"),
        port=os.getenv("PGPORT", "5432"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres"),
        dbname=os.getenv("PGDATABASE", "wearables"),
    )

class TSResponse(BaseModel):
    timestamps: List[str]
    values:     List[float]

def choose_table(start_date: dt.date, end_date: dt.date):
    delta = end_date - start_date
    if delta <= timedelta(days=1):
        return "raw_data", "ts"
    elif delta <= timedelta(days=7):
        return "data_1m", "bucket"
    elif delta <= timedelta(days=30):
        return "data_1h", "bucket"
    else:
        return "data_1d", "bucket"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/data", response_model=TSResponse)
def get_data(
    start_date: dt.date = Query(...),
    end_date:   dt.date = Query(...),
    metric:     str     = Query(...),
    user_id:    int     = Query(1),
):
    if end_date < start_date:
        raise HTTPException(400, "end_date earlier than start_date")

    # pick the right table & timestamp column
    table, ts_col = choose_table(start_date, end_date)

    sql = f"""
    SELECT {ts_col} AS ts, value
    FROM   {table}
    WHERE  {ts_col} BETWEEN %s AND %s
      AND  participant = %s
      AND  metric = %s
    ORDER  BY {ts_col}
    """

    params = (
        start_date,
        end_date + dt.timedelta(days=1),
        user_id,
        metric
    )

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(404, "no data")

    ts_list, val_list = zip(*rows)
    return TSResponse(
        timestamps=[t.isoformat() for t in ts_list],
        values=list(map(float, val_list))
    )