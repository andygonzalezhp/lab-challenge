import pandas as pd, pathlib

ROOT = pathlib.Path("data/participant_001")

for csv_path in ROOT.glob("*.csv"):
    print("Converting", csv_path.name)
    df = pd.read_csv(csv_path, parse_dates=[0])
    parquet_path = csv_path.with_suffix(".parquet")
    df.to_parquet(parquet_path, index=False)
    print(" wrote", parquet_path.name)
print("finished")
