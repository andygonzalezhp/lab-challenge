#!/usr/bin/env python
"""
Flatten Wearipedia JSON → tidy CSV (timestamp,value) for all six metrics.
Works with every synthetic-data shape (list-wrapped or dict-wrapped).
"""

import json, pathlib, pandas as pd, re
import itertools, re


SRC_DIR = pathlib.Path("task_0b/data/participant_001")
OUT_DIR = SRC_DIR
JSONS   = {
    "hr"      : "hr.json",
    "activity": "activity.json",
    "azm"     : "azm.json",
    "br"      : "br.json",
    "hrv"     : "hrv.json",
    "spo2"    : "spo2.json",
}

# helpers
def load(fn):
    with open(SRC_DIR / fn) as f:
        return json.load(f)

def write_csv(name, df):
    out = OUT_DIR / f"{name}.csv"
    df.to_csv(out, index=False)
    print(f"wrote {out} rows={len(df):,}")

def find_dataset(node, key_re=r".*dataset$"):
    """
    Depth-first search through dicts/lists until we hit a key whose name
    matches key_re (default 'dataset').  Returns (dataset_list, context_dict).
    context_dict is the nearest ancestor dict – we use it to extract date.
    """
    if isinstance(node, dict):
        for k, v in node.items():
            if re.match(key_re, k):
                return v, node          # found the dataset
            ds, ctx = find_dataset(v, key_re)
            if ds is not None:
                return ds, ctx
    elif isinstance(node, list):
        for v in node:
            ds, ctx = find_dataset(v, key_re)
            if ds is not None:
                return ds, ctx
    return None, None

def build_ts(date_str, rec):
    """Compose full ISO timestamp from day date + either time/minute field."""
    if "time"   in rec: return f"{date_str} {rec['time']}"
    if "minute" in rec: return rec["minute"]            # already full
    return rec.get("dateTime") or rec.get("datetime")   # fallback


def iter_datasets(node, key_re=r".*dataset$"):
    """
    Depth-first generator that yields every (dataset_list, context_dict) pair
    anywhere in the JSON tree whose key name matches key_re.
    """
    if isinstance(node, dict):
        for k, v in node.items():
            if re.match(key_re, k):
                yield v, node
            else:
                yield from iter_datasets(v, key_re)
    elif isinstance(node, list):
        for v in node:
            yield from iter_datasets(v, key_re)

#heart rate
def flatten_hr(obj):
    """
    Synthetic hr.json:
      top-level list  -> each item has heart_rate_day[0]
                         -> activities-heart-intraday.dataset[]
    Returns 86 400 × 30 = 2 592 000 rows.
    """
    rows = []
    day_containers = obj if isinstance(obj, list) else [obj]

    for d in day_containers:
        # unwrap the 'heart_rate_day' list
        day_dict = (d.get("heart_rate_day") or [d])[0]

        date_str = (
            day_dict.get("dateTime")                       # real export
            or day_dict.get("activities-heart", [{}])[0].get("dateTime")
        )

        ds = (
            day_dict
            .get("activities-heart-intraday", {})
            .get("dataset", [])
        )

        for rec in ds:
            rows.append(
                {
                    "timestamp": f"{date_str} {rec['time']}",
                    "value":     float(rec["value"]),
                }
            )

    return pd.DataFrame(rows)



#active zone minutes
def flatten_azm(obj):
    rows = []
    # top-level can be list or dict → normalise to list
    containers = obj if isinstance(obj, list) else [obj]

    for container in containers:
        # container["activities-active-zone-minutes-intraday"] is itself a list (1 per day)
        for day in container.get("activities-active-zone-minutes-intraday", []):
            date = day.get("dateTime", "")
            for rec in day.get("minutes", []):
                # full ISO timestamp = "YYYY-MM-DD HH:MM:SS"
                ts = f"{date} {rec['minute']}"
                val_obj = rec["value"]

                # value can be int/float or nested dict – handle both
                if isinstance(val_obj, (int, float)):
                    val = float(val_obj)
                else:                       # dict → sum of all component AZM buckets
                    val = float(sum(val_obj.values()))

                rows.append({"timestamp": ts, "value": val})

    return pd.DataFrame(rows)




#breath rate
def flatten_br(obj):
    rows = []

    # new daily-summary shape (your current json)
    if isinstance(obj, list) and obj and "br" in obj[0]:
        for day in obj:
            for rec in day["br"]:
                ts   = rec["dateTime"]                      # YYYY-MM-DD
                full = rec["value"]["fullSleepSummary"]["breathingRate"]
                rows.append({"timestamp": ts, "value": float(full)})
        return pd.DataFrame(rows)

    # old intraday list shape (records have minute/time/dateTime)
    if isinstance(obj, list):
        for rec in obj:
            ts = (rec.get("minute") or rec.get("time")
                  or rec.get("dateTime") or rec.get("datetime"))
            if ts:
                rows.append({"timestamp": ts,
                             "value": float(rec["value"])})
        return pd.DataFrame(rows)

    #  future dict-wrapped fallback (keeps previous logic)
    for rec in obj.get("br", []):
        ts = rec.get("minute") or rec.get("time") or rec.get("dateTime")
        rows.append({"timestamp": ts, "value": float(rec["value"])})
    return pd.DataFrame(rows)



# hrv
def flatten_hrv(obj, metric="rmssd"):
    """
    Extract HRV minute-level data (default = 'rmssd').
    Falls back gracefully if structure changes.
    """
    rows = []
    # accommodate both list-wrapped and dict-root shapes
    outer = obj if isinstance(obj, list) else [obj]

    for day in outer:
        for hrv_block in day.get("hrv", []):
            for rec in hrv_block.get("minutes", []):
                rows.append({
                    "timestamp": rec["minute"],
                    "value": float(rec["value"][metric])   # pick the metric you want
                })

    return pd.DataFrame(rows)


# spo2
def flatten_spo2(obj):
    rows = []
    for day in obj:                           # list per day
        for rec in day.get("minutes", []):
            rows.append({"timestamp": rec["minute"],
                         "value": float(rec["value"])})
    return pd.DataFrame(rows)

# activity
def flatten_activity(obj):
    """
    Synthetic 'activity.json' has just 30 daily summaries, no intraday list.
    We’ll keep those 30 rows so at least the date → total steps are available.
    """
    rows = [{"timestamp": rec["dateTime"], "value": float(rec["value"])}
            for rec in obj]          # top-level list of 30 dicts
    return pd.DataFrame(rows)

# mapping
FLATTEN = {
    "hr":       flatten_hr,
    "activity": flatten_activity,   # or "steps" if that’s your file
    "azm":      flatten_azm,
    "br":       flatten_br,
    "hrv":      flatten_hrv,
    "spo2":     flatten_spo2,
}


# main
for name, fn in JSONS.items():
    path = SRC_DIR / fn
    if not path.exists():
        print(f"WARNING: {fn} not found – skipped.")
        continue

    tidy = FLATTEN[name](load(fn))
    write_csv(name, tidy)
