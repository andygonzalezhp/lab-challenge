from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os, psycopg2, datetime as dt

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

    sql = """
    SELECT ts, value
    FROM   raw_data
    WHERE  ts BETWEEN %s AND %s
      AND  participant = %s
      AND  metric = %s
    ORDER  BY ts
    """
    with get_conn() as c, c.cursor() as cur:
        cur.execute(sql, (
            start_date,
            end_date + dt.timedelta(days=1),
            user_id, metric
        ))
        rows = cur.fetchall()

    if not rows:
        raise HTTPException(404, "no data")

    ts, vals = zip(*rows)
    return TSResponse(
        timestamps=[t.isoformat() for t in ts],
        values=list(map(float, vals))
    )

