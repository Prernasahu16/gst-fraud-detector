"""
==============================================================
 GST FRAUD DETECTOR - DATA CLEANING
 File: clean_data.py
 Run:  python clean_data.py
 Input:  data/gst_raw.csv
 Output: data/gst_clean.csv
==============================================================
"""

import pandas as pd
import numpy as np
import os

os.makedirs("data", exist_ok=True)

print("=" * 55)
print("  GST FRAUD DETECTOR — DATA CLEANING PIPELINE")
print("=" * 55)

# ── LOAD ──────────────────────────────────────────────────────
df = pd.read_csv("data/gst_raw.csv")
print(f"\n[LOAD] Raw rows: {len(df):,}  |  Cols: {len(df.columns)}")

print("\n[PROFILE] Issues found:")
print(f"  Null gstr3b_tax_paid : {df['gstr3b_tax_paid'].isna().sum()}")
print(f"  Negative itc_claimed : {(df['itc_claimed'] < 0).sum()}")
print(f"  Duplicate rows       : {df.duplicated().sum()}")

valid_states = [
    "Maharashtra","Uttar Pradesh","Karnataka","Tamil Nadu","Gujarat",
    "Rajasthan","West Bengal","Andhra Pradesh","Telangana","Madhya Pradesh",
    "Bihar","Punjab","Haryana","Delhi","Odisha","Kerala","Jharkhand",
    "Assam","Chhattisgarh","Himachal Pradesh"
]
typos_found = df[~df["state"].isin(valid_states)]["state"].unique()
print(f"  State name typos     : {list(typos_found)}")

# ── FIX 1: Standardise state names ───────────────────────────
state_corrections = {
    "Maharastra":    "Maharashtra",
    "Uttar pradesh": "Uttar Pradesh",
}
df["state"] = df["state"].replace(state_corrections)
print(f"\n[FIX-1] State name typos corrected")

# ── FIX 2: Remove duplicates ─────────────────────────────────
before = len(df)
df = df.drop_duplicates(subset=["state","sector","month_year"]).reset_index(drop=True)
print(f"[FIX-2] Removed {before - len(df)} duplicate rows")

# ── FIX 3: Negative ITC → absolute value ─────────────────────
neg_mask = df["itc_claimed"] < 0
df.loc[neg_mask, "itc_claimed"] = df.loc[neg_mask, "itc_claimed"].abs()
print(f"[FIX-3] Corrected {neg_mask.sum()} negative ITC values (abs)")

# ── FIX 4: Impute null gstr3b_tax_paid ───────────────────────
null_count = df["gstr3b_tax_paid"].isna().sum()
df["gstr3b_tax_paid"] = (
    df.groupby(["state", "sector"])["gstr3b_tax_paid"]
    .transform(lambda x: x.fillna(x.median()))
)
print(f"[FIX-4] Imputed {null_count} null tax_paid values (state-sector median)")

# ── FIX 5: Recalculate ITC rate after cleaning ───────────────
df["itc_rate_pct"] = np.where(
    df["gstr1_declared_sales"] > 0,
    (df["itc_claimed"] / df["gstr1_declared_sales"] * 100).round(2),
    0.0
)

# ── FIX 6: Recalculate fraud flag ────────────────────────────
def flag(row):
    if row["itc_claimed"] > row["gstr1_declared_sales"]:
        return "CRITICAL"
    elif row["itc_rate_pct"] > 85:
        return "HIGH_RISK"
    elif row["itc_rate_pct"] > 65:
        return "MEDIUM_RISK"
    return "NORMAL"

df["fraud_flag"] = df.apply(flag, axis=1)

# ── FIX 7: Recalculate fraud score ───────────────────────────
def score(row):
    s = 0
    if row["itc_claimed"] > row["gstr1_declared_sales"]: s += 40
    elif row["itc_rate_pct"] > 85:                        s += 25
    elif row["itc_rate_pct"] > 65:                        s += 12
    if abs(row["mismatch_pct"]) > 30:                     s += 20
    if row["gstr3b_tax_paid"] < row["gstr1_declared_sales"] * 0.04: s += 15
    if row["fraud_prone_sector"]:                          s += 10
    return min(s, 100)

df["fraud_score"] = df.apply(score, axis=1)

# ── SAVE ──────────────────────────────────────────────────────
df.to_csv("data/gst_clean.csv", index=False)

print(f"\n[DONE] Clean dataset: {len(df):,} rows  →  data/gst_clean.csv")
print("\n[SUMMARY] Fraud flags in clean data:")
for flag_val, cnt in df["fraud_flag"].value_counts().items():
    pct = cnt / len(df) * 100
    print(f"  {flag_val:<15}  {cnt:>5}  ({pct:.1f}%)")

print(f"\n[VERIFY] No nulls remaining: {df.isnull().sum().sum() == 0}")
print(f"[VERIFY] No negative ITC:    {(df['itc_claimed'] < 0).sum() == 0}")
print(f"[VERIFY] No duplicates:      {df.duplicated().sum() == 0}")
