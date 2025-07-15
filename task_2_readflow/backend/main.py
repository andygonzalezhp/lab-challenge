from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import os, psycopg2, datetime as dt
from datetime import timedelta
import bisect
import smtplib, email.message
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Wearables Read-API")

Instrumentator().instrument(app).expose(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # dev: allow all
    allow_credentials=True,
    allow_methods=["*"], 
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


SMTP_HOST = os.getenv("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.getenv("SMTP_PORT", 1025))

def send_mail(to_addr: str, subject: str, body: str):
    msg = email.message.EmailMessage()
    msg["From"] = "clinician@wearipedia.local"
    msg["To"]   = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.send_message(msg)

class Participant(BaseModel):
    id:   int
    name: str

_FAKE_PARTICIPANTS = [
    Participant(id=i, name=f"Participant {i}") for i in range(1, 11)
]

@app.get("/participants", response_model=list[Participant])
def list_participants():
    # in a real system you’d pull from a users table
    return _FAKE_PARTICIPANTS

@app.get("/participants/{pid}", response_model=Participant)
def get_participant(pid: int):
    for p in _FAKE_PARTICIPANTS:
        if p.id == pid:
            return p
    raise HTTPException(404, "participant not found")

class TSResponse(BaseModel):
    timestamps: List[str]
    values:     List[float]
    imputed:    List[bool]

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
    
class AdherenceResponse(BaseModel):
    no_token:        bool
    last_upload:     Optional[str]  # ISO timestamp or null
    sleep_upload_pct: float          # 0–100
    wear_time_pct:    float          # 0–100

class NotifyRequest(BaseModel):
    user_id:     int
    start_date:  dt.date
    end_date:    dt.date
    reason:      str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/adherence", response_model=AdherenceResponse)
def get_adherence(
    start_date: dt.date = Query(...),
    end_date:   dt.date = Query(...),
    user_id:    int     = Query(1),
):
    # no_token: here we always have a token for synthetic data
    no_token = False

    # last_upload: max timestamp in raw_data
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT MAX(ts) FROM raw_data
            WHERE participant = %s
        """, (user_id,))
        last = cur.fetchone()[0]
    last_upload = last.isoformat() if last else None

    # sleep_upload_pct: % of days in range with ANY 'activity' data
    # (we'll approximate sleep upload by days with activity entries)
    total_days = (end_date - start_date).days + 1
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(DISTINCT DATE(ts))
            FROM raw_data
            WHERE participant = %s
              AND metric = 'activity'
              AND ts >= %s
              AND ts < %s
        """, (user_id, start_date, end_date + dt.timedelta(days=1)))
        days_reported = cur.fetchone()[0] or 0
    sleep_upload_pct = round(100 * days_reported / total_days, 2)

    # wear_time_pct: % of expected hr points present
    expected = total_days * 24 * 60 * 60
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM raw_data
            WHERE participant = %s
              AND metric = 'hr'
              AND ts BETWEEN %s AND %s
        """, (user_id, start_date, end_date + dt.timedelta(days=1)))
        hr_count = cur.fetchone()[0] or 0
    wear_time_pct = round(100 * hr_count / expected, 2)

    return AdherenceResponse(
        no_token=no_token,
        last_upload=last_upload,
        sleep_upload_pct=sleep_upload_pct,
        wear_time_pct=wear_time_pct
    )

@app.post("/notify")
def notify_participant(req: NotifyRequest):
    """
    queue an e-mail via mailhog (SMTP on localhost:1025).
    """
    subject = f"Action required – Fitbit adherence alert for participant {req.user_id}"
    body = (
        f"Hello Participant {req.user_id},\n\n"
        "Your recent Fitbit data shows:\n"
        f"{req.reason}\n"
        f"Study window: {req.start_date} – {req.end_date}\n\n"
        "Please make sure you wear & sync your device regularly.\n\n"
        "Thank you."
    )
    # in a real deployment `to_addr` would be the participant’s e-mail.
    send_mail("participant@example.com", subject, body)
    return {"status": "queued"}

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

    if table == "raw_data":
        interval = dt.timedelta(seconds=1)
    elif table == "data_1m":
        interval = dt.timedelta(minutes=1)
    elif table == "data_1h":
        interval = dt.timedelta(hours=1)
    else:  # data_1d
        interval = dt.timedelta(days=1)

    data_dict = {ts: float(val) for ts, val in rows}
    known_ts  = sorted(data_dict.keys())

    tz = known_ts[0].tzinfo
    t_start = dt.datetime.combine(start_date, dt.time.min, tzinfo=tz)
    t_end   = dt.datetime.combine(end_date + dt.timedelta(days=1), dt.time.min, tzinfo=tz)

    full_ts, full_vals, imputed_flags = [], [], []
    t = t_start
    while t < t_end:
        full_ts.append(t)
        if t in data_dict:
            # exact data point exists
            full_vals.append(data_dict[t])
            imputed_flags.append(False)
        else:
            # find nearest known points
            i = bisect.bisect_left(known_ts, t)
            if i == 0:
                v = data_dict[known_ts[0]]
            elif i == len(known_ts):
                v = data_dict[known_ts[-1]]
            else:
                t0, t1 = known_ts[i-1], known_ts[i]
                v0, v1 = data_dict[t0], data_dict[t1]
                frac = (t - t0).total_seconds() / (t1 - t0).total_seconds()
                v = v0 + (v1 - v0) * frac
            full_vals.append(v)
            imputed_flags.append(True)
        t += interval

    return TSResponse(
        timestamps=[ts.isoformat() for ts in full_ts],
        values=full_vals,
        imputed=imputed_flags
    )