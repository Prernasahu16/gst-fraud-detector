"""
==============================================================
 GST FRAUD DETECTOR - INDIA
 File: generate_dataset.py
 Run:  python generate_dataset.py
 Output: data/gst_raw.csv  +  data/gst_clean.csv
==============================================================
"""

import pandas as pd
import numpy as np
import os

np.random.seed(42)
os.makedirs("data", exist_ok=True)

# ── 20 Indian states with real fraud profiles ──────────────────
STATES = {
    "Maharashtra":      {"zone":"West",    "risk":"high",    "base":38000},
    "Uttar Pradesh":    {"zone":"North",   "risk":"extreme", "base":18000},
    "Karnataka":        {"zone":"South",   "risk":"medium",  "base":22000},
    "Tamil Nadu":       {"zone":"South",   "risk":"medium",  "base":20000},
    "Gujarat":          {"zone":"West",    "risk":"high",    "base":24000},
    "Rajasthan":        {"zone":"North",   "risk":"high",    "base":12000},
    "West Bengal":      {"zone":"East",    "risk":"extreme", "base":14000},
    "Andhra Pradesh":   {"zone":"South",   "risk":"medium",  "base":11000},
    "Telangana":        {"zone":"South",   "risk":"medium",  "base":13000},
    "Madhya Pradesh":   {"zone":"Central", "risk":"high",    "base":10000},
    "Bihar":            {"zone":"East",    "risk":"extreme", "base": 7000},
    "Punjab":           {"zone":"North",   "risk":"high",    "base": 9000},
    "Haryana":          {"zone":"North",   "risk":"high",    "base":16000},
    "Delhi":            {"zone":"North",   "risk":"extreme", "base":28000},
    "Odisha":           {"zone":"East",    "risk":"medium",  "base": 8000},
    "Kerala":           {"zone":"South",   "risk":"low",     "base":10000},
    "Jharkhand":        {"zone":"East",    "risk":"high",    "base": 5500},
    "Assam":            {"zone":"NE",      "risk":"medium",  "base": 4000},
    "Chhattisgarh":     {"zone":"Central", "risk":"high",    "base": 4500},
    "Himachal Pradesh": {"zone":"North",   "risk":"low",     "base": 2800},
}

SECTORS = {
    "Iron & Steel":          {"fraud_prone":True,  "legit_itc":0.52, "vol":0.12},
    "Textile & Apparel":     {"fraud_prone":True,  "legit_itc":0.45, "vol":0.14},
    "Construction":          {"fraud_prone":True,  "legit_itc":0.38, "vol":0.16},
    "Chemicals":             {"fraud_prone":True,  "legit_itc":0.48, "vol":0.10},
    "Electronics":           {"fraud_prone":False, "legit_itc":0.42, "vol":0.09},
    "Food Processing":       {"fraud_prone":False, "legit_itc":0.35, "vol":0.08},
    "Pharmaceuticals":       {"fraud_prone":False, "legit_itc":0.40, "vol":0.07},
    "Real Estate":           {"fraud_prone":True,  "legit_itc":0.55, "vol":0.18},
    "Transport & Logistics": {"fraud_prone":False, "legit_itc":0.32, "vol":0.09},
    "Gems & Jewellery":      {"fraud_prone":True,  "legit_itc":0.60, "vol":0.20},
}

RISK_PROFILE = {
    "extreme": {"prob":0.22, "inflate":0.35},
    "high":    {"prob":0.14, "inflate":0.22},
    "medium":  {"prob":0.06, "inflate":0.10},
    "low":     {"prob":0.02, "inflate":0.04},
}

months = pd.date_range("2021-04-01", "2024-03-01", freq="MS")
records = []

for state, sm in STATES.items():
    rp = RISK_PROFILE[sm["risk"]]
    for sector, sec in SECTORS.items():
        for month in months:
            # Seasonal factor
            seasonal = 1.18 if month.month == 3 else \
                       1.10 if month.month == 12 else \
                       0.88 if month.month == 4 else 1.0
            # YoY growth ~12%
            fy_yr   = month.year if month.month >= 4 else month.year - 1
            fy_growth = 1.0 + 0.12 * (fy_yr - 2021)
            fy_label  = f"FY{fy_yr}-{str(fy_yr+1)[-2:]}"

            sales = round(sm["base"] * fy_growth * seasonal *
                          np.random.uniform(0.85, 1.15) * 1e5)
            tax   = round(sales * np.random.uniform(0.89, 0.99) * 0.18)
            itc_r = np.clip(sec["legit_itc"] + np.random.normal(0, sec["vol"]*0.5),
                            0.10, 0.78)
            itc   = round(sales * itc_r)

            is_fraud   = False
            fraud_type = "NONE"

            if sec["fraud_prone"] and np.random.random() < rp["prob"]:
                is_fraud = True
                pattern  = np.random.choice(
                    ["itc_inflation","sales_suppression","circular_trading"],
                    p=[0.50, 0.30, 0.20])
                fraud_type = pattern
                if pattern == "itc_inflation":
                    itc = round(sales * np.random.uniform(0.88, 1.35))
                elif pattern == "sales_suppression":
                    sales = round(sales * np.random.uniform(0.45, 0.70))
                elif pattern == "circular_trading":
                    sales = round(sales * np.random.uniform(2.5, 4.2))
                    itc   = round(sales * np.random.uniform(0.78, 0.92))

            itc_pct = round(itc / sales * 100, 2) if sales > 0 else 0.0
            mis_pct = round((itc - sales * 0.60) / (sales * 0.60) * 100, 2) if sales > 0 else 0.0

            flag = ("CRITICAL"     if itc > sales else
                    "HIGH_RISK"    if itc_pct > 85 else
                    "MEDIUM_RISK"  if itc_pct > 65 else "NORMAL")

            score = 0
            if itc > sales:       score += 40
            elif itc_pct > 85:    score += 25
            elif itc_pct > 65:    score += 12
            if abs(mis_pct) > 30: score += 20
            if tax < sales*0.04:  score += 15
            if sec["fraud_prone"]: score += 10
            if sm["risk"] in ("extreme","high"): score += 10
            score = min(score, 100)

            records.append({
                "record_id":            len(records)+1,
                "month_year":           month.strftime("%b-%Y"),
                "fiscal_year":          fy_label,
                "state":                state,
                "zone":                 sm["zone"],
                "sector":               sector,
                "fraud_prone_sector":   int(sec["fraud_prone"]),
                "gstr1_declared_sales": sales,
                "gstr3b_tax_paid":      tax,
                "itc_claimed":          itc,
                "itc_rate_pct":         itc_pct,
                "mismatch_pct":         mis_pct,
                "fraud_flag":           flag,
                "fraud_score":          score,
                "is_fraud":             int(is_fraud),
                "fraud_type":           fraud_type,
            })

df = pd.DataFrame(records)

# ── Inject dirty data ──────────────────────────────────────────
null_idx = df.sample(frac=0.025, random_state=1).index
df.loc[null_idx, "gstr3b_tax_paid"] = np.nan

neg_idx = df.sample(frac=0.010, random_state=2).index
df.loc[neg_idx, "itc_claimed"] = df.loc[neg_idx, "itc_claimed"] * -1

dupe_idx = df.sample(15, random_state=3).index
df = pd.concat([df, df.loc[dupe_idx]], ignore_index=True)

typo_idx = df.sample(frac=0.008, random_state=4).index
typos = {"Maharashtra":"Maharastra", "Uttar Pradesh":"Uttar pradesh"}
df.loc[typo_idx, "state"] = df.loc[typo_idx, "state"].map(
    lambda x: typos.get(x, x))

df.to_csv("data/gst_raw.csv", index=False)
print(f"✓ Raw dataset: {len(df):,} rows × {len(df.columns)} cols  →  data/gst_raw.csv")
print(f"  Fraud injected:   {df['is_fraud'].sum()} records")
print(f"  Nulls injected:   {df['gstr3b_tax_paid'].isna().sum()}")
print(f"  Neg ITC:          {(df['itc_claimed']<0).sum()}")
print(f"  Duplicates:       15")
print(f"  Typos:            {len(typo_idx)}")
