# ------ MERGE ALL GENERATED CSV FILES INTO MASTER FILE ------
import glob
import os
import pandas as pd
csv_folder = "data/raw/csv"
master_path = "data/raw/csv/upsc_master_questions.csv"

all_csvs = glob.glob(os.path.join(csv_folder, "*.csv"))

df_list = []
for csv in all_csvs:
    try:
        df_list.append(pd.read_csv(csv))
    except Exception as e:
        print(f"Skipping {csv}: {e}")

master_df = pd.concat(df_list, ignore_index=True)
master_df.to_csv(master_path, index=False, encoding="utf-8-sig")

print("MASTER CSV SAVED:", master_path)
print("TOTAL ROWS:", len(master_df))
