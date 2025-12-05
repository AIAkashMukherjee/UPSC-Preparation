import pandas as pd
import json
import os

def csv_to_json(csv_path, json_path):
    # Load CSV
    df = pd.read_csv(csv_path)

    # Convert NaN → None (clean JSON)
    df = df.where(pd.notnull(df), None)

    # Convert to list of dicts
    data = df.to_dict(orient="records")

    # Ensure output folder exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    # Save JSON (compact but readable)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"JSON saved → {json_path}")
    print(f"Total questions → {len(data)}")


if __name__ == "__main__":
    csv_path = "data/raw/csv/upsc_master_questions.csv"
    json_path = "data/processed/questions_bank.json"

    csv_to_json(csv_path, json_path)
