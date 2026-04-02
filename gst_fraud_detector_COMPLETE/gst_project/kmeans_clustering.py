"""
==============================================================
 GST FRAUD DETECTOR — K-MEANS STATE RISK CLUSTERING
 File: kmeans_clustering.py
 Run:  python kmeans_clustering.py
 Input:  data/gst_clean.csv
 Output: data/state_clusters.csv
==============================================================
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import os

os.makedirs("data", exist_ok=True)

print("=" * 55)
print("  K-MEANS STATE RISK CLUSTERING")
print("=" * 55)

df = pd.read_csv("data/gst_clean.csv")

# ── Build state-level feature matrix ─────────────────────────
state_feats = df.groupby("state").agg(
    avg_itc_rate    = ("itc_rate_pct",  "mean"),
    avg_mismatch    = ("mismatch_pct",  "mean"),
    months_flagged  = ("fraud_flag",    lambda x: (x != "NORMAL").sum()),
    critical_months = ("fraud_flag",    lambda x: (x == "CRITICAL").sum()),
    avg_score       = ("fraud_score",   "mean"),
    total_itc_cr    = ("itc_claimed",   lambda x: x.sum() / 1e7),
).reset_index()

print(f"\n[DATA] {len(state_feats)} states × 6 features")
print(state_feats[["state","avg_itc_rate","months_flagged","avg_score"]].to_string(index=False))

# ── Standardise features ─────────────────────────────────────
FEATURES = ["avg_itc_rate", "avg_mismatch", "months_flagged", "avg_score"]
scaler = StandardScaler()
X = scaler.fit_transform(state_feats[FEATURES])

# ── Elbow + Silhouette to choose k ───────────────────────────
print("\n[ELBOW] Testing k = 2 to 6:")
inertias, sil_scores = [], []
for k in range(2, 7):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    lbl = km.fit_predict(X)
    inertias.append(km.inertia_)
    sil = silhouette_score(X, lbl)
    sil_scores.append(sil)
    print(f"  k={k}  inertia={km.inertia_:8.1f}  silhouette={sil:.3f}")

best_k = 3  # optimal for LOW/MEDIUM/HIGH business meaning
print(f"\n[CHOSEN] k={best_k} (best business interpretability + silhouette)")

# ── Final clustering ─────────────────────────────────────────
kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
state_feats["cluster"] = kmeans.fit_predict(X)

final_sil = silhouette_score(X, state_feats["cluster"])
print(f"[RESULT] Final silhouette score: {final_sil:.3f}  (>0.5 = strong separation)")

# ── Label clusters by fraud score ────────────────────────────
cluster_order = state_feats.groupby("cluster")["avg_score"].mean().sort_values()
label_map = {
    cluster_order.index[0]: "LOW",
    cluster_order.index[1]: "MEDIUM",
    cluster_order.index[2]: "HIGH",
}
state_feats["risk_label"] = state_feats["cluster"].map(label_map)

print("\n[CLUSTERS]")
for lbl in ["HIGH", "MEDIUM", "LOW"]:
    states = state_feats[state_feats["risk_label"] == lbl]["state"].tolist()
    avg_s  = state_feats[state_feats["risk_label"] == lbl]["avg_score"].mean()
    print(f"  {lbl:6s} (avg_score={avg_s:.1f}): {', '.join(states)}")

# ── Save ─────────────────────────────────────────────────────
state_feats["elbow_inertias"]  = str(inertias)
state_feats["silhouette_scores"] = str(sil_scores)
state_feats.to_csv("data/state_clusters.csv", index=False)
print(f"\n[SAVED] data/state_clusters.csv")
