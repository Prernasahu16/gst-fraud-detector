"""
==============================================================
 GST FRAUD DETECTOR — MASTER RUN SCRIPT
 File: run_all.py
 Run:  python run_all.py
 This runs the full pipeline in sequence:
   1. Generate raw dataset (7,200 rows)
   2. Clean data
   3. K-Means clustering
   4. Generate all 3 charts
==============================================================
"""

import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("data",    exist_ok=True)
os.makedirs("visuals", exist_ok=True)

steps = [
    ("generate_dataset.py",  "STEP 1: Generating dataset"),
    ("clean_data.py",         "STEP 2: Cleaning data"),
    ("kmeans_clustering.py",  "STEP 3: K-Means clustering"),
    ("generate_charts.py",    "STEP 4: Generating charts"),
]

for script, label in steps:
    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")
    result = subprocess.run(
        [sys.executable, script],
        capture_output=False
    )
    if result.returncode != 0:
        print(f"\n❌ Failed at {script}. Stopping.")
        sys.exit(1)

print("\n" + "="*55)
print("  ALL STEPS COMPLETE")
print("="*55)
print("\n  Files generated:")
print("  📁 data/gst_raw.csv")
print("  📁 data/gst_clean.csv")
print("  📁 data/state_clusters.csv")
print("  📁 visuals/01_master_dashboard.png")
print("  📁 visuals/02_sector_deep_dive.png")
print("  📁 visuals/03_state_scorecard.png")
print("\n  To launch dashboard:")
print("  streamlit run app.py")
print("="*55)
