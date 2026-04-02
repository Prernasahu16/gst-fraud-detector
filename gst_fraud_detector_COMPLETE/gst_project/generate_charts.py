"""
==============================================================
 GST FRAUD DETECTOR — CHART GENERATION (ALL 3 FIGURES)
 File: generate_charts.py
 Run:  python generate_charts.py
 Input:  data/gst_clean.csv  +  data/state_clusters.csv
 Output: visuals/  (3 PNG files, 150 DPI)
==============================================================
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import os

os.makedirs("visuals", exist_ok=True)

# ── Theme ─────────────────────────────────────────────────────
BG   = "#0b0f1a"
CARD = "#111827"
GRID = "#1f2937"
TEXT = "#f1f5f9"
MUTE = "#6b7280"

CRIT   = "#ef4444"
HIGH   = "#f97316"
MED    = "#eab308"
SAFE   = "#22c55e"
ACC    = "#6366f1"
BLUE   = "#3b82f6"

plt.rcParams.update({
    "figure.facecolor":  BG,
    "axes.facecolor":    CARD,
    "axes.edgecolor":    GRID,
    "axes.labelcolor":   MUTE,
    "xtick.color":       MUTE,
    "ytick.color":       MUTE,
    "text.color":        TEXT,
    "grid.color":        GRID,
    "grid.linewidth":    0.5,
    "font.family":       "monospace",
    "axes.titlesize":    10,
    "axes.labelsize":    8,
    "xtick.labelsize":   7.5,
    "ytick.labelsize":   7.5,
})

FLAG_C = {"CRITICAL":CRIT,"HIGH_RISK":HIGH,"MEDIUM_RISK":MED,"NORMAL":SAFE}

# ── Load data ─────────────────────────────────────────────────
df = pd.read_csv("data/gst_clean.csv")
sf = pd.read_csv("data/state_clusters.csv")
df["sort_dt"] = pd.to_datetime(df["month_year"], format="%b-%Y")
print(f"[LOAD] {len(df):,} rows | {df['state'].nunique()} states | {df['sector'].nunique()} sectors")

# ══════════════════════════════════════════════════════════════
#  FIGURE 1 — MASTER FRAUD DASHBOARD  (6 panels)
# ══════════════════════════════════════════════════════════════
print("\n[CHART 1] Building master fraud dashboard...")
fig = plt.figure(figsize=(22, 14), facecolor=BG)
fig.suptitle(
    "INDIA GST RETURN MISMATCH FRAUD DETECTOR  ·  GSTR-1 vs GSTR-3B  ·  FY2022–FY2024",
    fontsize=14, color=ACC, fontweight="bold", y=0.985, fontfamily="monospace"
)
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.52, wspace=0.38)

# ── P1: Flag distribution (bar) ───────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
order = ["CRITICAL","HIGH_RISK","MEDIUM_RISK","NORMAL"]
flag_ct = df["fraud_flag"].value_counts().reindex(
    [f for f in order if f in df["fraud_flag"].values])
clrs1 = [FLAG_C[f] for f in flag_ct.index]
bars1 = ax1.bar(flag_ct.index, flag_ct.values, color=clrs1, width=0.62, zorder=3)
ax1.set_title("Fraud Flag Distribution", color=TEXT, pad=8)
ax1.set_ylabel("Records", color=MUTE)
ax1.tick_params(axis="x", rotation=20)
ax1.grid(axis="y", zorder=0)
for b in bars1:
    h = b.get_height()
    ax1.text(b.get_x()+b.get_width()/2, h+5,
             f"{h:,}", ha="center", va="bottom", fontsize=8, color=TEXT)

# ── P2: State ranking (horizontal stacked bar) ───────────────
ax2 = fig.add_subplot(gs[0, 1:])
sr = df.groupby("state").agg(
    critical  = ("fraud_flag", lambda x: (x=="CRITICAL").sum()),
    high_risk = ("fraud_flag", lambda x: (x=="HIGH_RISK").sum()),
    avg_score = ("fraud_score","mean")
).sort_values("avg_score", ascending=True)
y2 = np.arange(len(sr))
ax2.barh(y2, sr["critical"],   color=CRIT, zorder=3, label="Critical",  height=0.62)
ax2.barh(y2, sr["high_risk"],  left=sr["critical"],
         color=HIGH, zorder=3, label="High Risk", height=0.62)
ax2.set_yticks(y2)
ax2.set_yticklabels(sr.index, fontsize=8)
ax2.set_title("State-wise Critical + High-Risk Flags  (sorted by avg fraud score)", color=TEXT, pad=8)
ax2.set_xlabel("Flag Count", color=MUTE)
ax2.legend(fontsize=8, facecolor=CARD, edgecolor=GRID)
ax2.grid(axis="x", zorder=0)
for b, (_, row) in zip(ax2.patches[:len(sr)], sr.iterrows()):
    ax2.text(sr["critical"].max()+sr["high_risk"].max()+1,
             b.get_y()+b.get_height()/2,
             f"score={row['avg_score']:.0f}",
             va="center", fontsize=6.5, color=MUTE)

# ── P3: Monthly trend (bar + line) ───────────────────────────
ax3 = fig.add_subplot(gs[1, :2])
monthly = df.groupby("sort_dt").agg(
    critical  = ("fraud_flag", lambda x: (x=="CRITICAL").sum()),
    high      = ("fraud_flag", lambda x: (x=="HIGH_RISK").sum()),
    avg_score = ("fraud_score","mean")
).reset_index().sort_values("sort_dt")
x3 = range(len(monthly))
ax3b = ax3.twinx()
ax3.bar(x3, monthly["critical"],
        color=CRIT, alpha=0.8, label="Critical",  zorder=3)
ax3.bar(x3, monthly["high"], bottom=monthly["critical"],
        color=HIGH, alpha=0.8, label="High Risk", zorder=3)
ax3b.plot(x3, monthly["avg_score"],
          color=ACC, lw=2.5, label="Avg Fraud Score", zorder=4)
ax3b.tick_params(axis="y", colors=ACC)
ax3b.set_ylabel("Avg Fraud Score", color=ACC, fontsize=8)
# FY boundary lines
for i, label in enumerate(["FY2022","FY2023","FY2024"]):
    ax3.axvline(i*12, color=GRID, ls="--", lw=0.9)
    ax3.text(i*12+0.4, ax3.get_ylim()[1]*0.90 if ax3.get_ylim()[1] > 0 else 5,
             label, fontsize=7.5, color=MUTE)
ax3.set_xticks([])
ax3.set_title("Monthly Fraud Flag Trend  +  Avg Fraud Score  (36 months)", color=TEXT, pad=8)
ax3.set_ylabel("Flagged Records", color=MUTE)
h1, l1 = ax3.get_legend_handles_labels()
h2, l2 = ax3b.get_legend_handles_labels()
ax3.legend(h1+h2, l1+l2, fontsize=8, facecolor=CARD, edgecolor=GRID, loc="upper left")
ax3.grid(axis="y", zorder=0)

# ── P4: K-Means scatter ──────────────────────────────────────
ax4 = fig.add_subplot(gs[1, 2])
cluster_c = {"HIGH":CRIT,"MEDIUM":HIGH,"LOW":SAFE}
for lbl, grp in sf.groupby("risk_label"):
    ax4.scatter(grp["avg_itc_rate"], grp["months_flagged"],
                color=cluster_c[lbl], label=f"{lbl} risk", s=90, zorder=3, alpha=0.9)
    for _, row in grp.iterrows():
        ax4.annotate(row["state"][:5],
                     (row["avg_itc_rate"], row["months_flagged"]),
                     fontsize=6, color=MUTE, xytext=(3,3), textcoords="offset points")
ax4.set_title(f"K-Means Risk Clusters  (k=3)", color=TEXT, pad=8)
ax4.set_xlabel("Avg ITC Rate %", color=MUTE)
ax4.set_ylabel("Months Flagged", color=MUTE)
ax4.legend(fontsize=8, facecolor=CARD, edgecolor=GRID)
ax4.grid(zorder=0)

# ── P5: Sector × FY heatmap ──────────────────────────────────
ax5 = fig.add_subplot(gs[2, :2])
pivot5 = df.pivot_table(values="fraud_score",
                         index="sector", columns="fiscal_year", aggfunc="mean")
im5 = ax5.imshow(pivot5.values, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=50)
ax5.set_xticks(range(len(pivot5.columns)))
ax5.set_xticklabels(pivot5.columns, fontsize=8)
ax5.set_yticks(range(len(pivot5.index)))
ax5.set_yticklabels(pivot5.index, fontsize=8)
ax5.set_title("Avg Fraud Score: Sector × Fiscal Year  (darker = more suspicious)", color=TEXT, pad=8)
for i in range(len(pivot5.index)):
    for j in range(len(pivot5.columns)):
        v = pivot5.values[i, j]
        ax5.text(j, i, f"{v:.0f}", ha="center", va="center",
                 fontsize=9.5, fontweight="bold",
                 color="black" if v > 25 else "white")
plt.colorbar(im5, ax=ax5, label="Fraud Score", shrink=0.8)

# ── P6: ITC Rate violin per flag ─────────────────────────────
ax6 = fig.add_subplot(gs[2, 2])
flag_order6 = [f for f in ["NORMAL","MEDIUM_RISK","HIGH_RISK","CRITICAL"]
               if f in df["fraud_flag"].values]
vdata = [df[df["fraud_flag"]==f]["itc_rate_pct"].clip(0,130).dropna().values
         for f in flag_order6]
vparts = ax6.violinplot(vdata, showmedians=True)
vcolors = [SAFE, MED, HIGH, CRIT][:len(flag_order6)]
for pc, c in zip(vparts["bodies"], vcolors):
    pc.set_facecolor(c); pc.set_alpha(0.65)
vparts["cmedians"].set_color("white")
for part in ["cbars","cmins","cmaxes"]:
    vparts[part].set_color(MUTE)
ax6.axhline(85,  color=HIGH, ls="--", lw=1, alpha=0.8, label="85% (High Risk)")
ax6.axhline(100, color=CRIT, ls="--", lw=1, alpha=0.8, label="100% (Critical)")
ax6.set_xticks(range(1, len(flag_order6)+1))
ax6.set_xticklabels([f[:6] for f in flag_order6], fontsize=8)
ax6.set_title("ITC Rate % Distribution by Fraud Flag", color=TEXT, pad=8)
ax6.set_ylabel("ITC Claimed / Sales %", color=MUTE)
ax6.legend(fontsize=7.5, facecolor=CARD, edgecolor=GRID)
ax6.grid(axis="y", zorder=0)

fig.savefig("visuals/01_master_dashboard.png", dpi=150,
            bbox_inches="tight", facecolor=BG)
plt.close()
print("  ✓ visuals/01_master_dashboard.png")


# ══════════════════════════════════════════════════════════════
#  FIGURE 2 — SECTOR + FRAUD TYPE DEEP DIVE  (2×3)
# ══════════════════════════════════════════════════════════════
print("[CHART 2] Building sector deep dive...")
fig2, axes2 = plt.subplots(2, 3, figsize=(21, 12), facecolor=BG)
fig2.suptitle("SECTOR & FRAUD TYPE DEEP DIVE  ·  PATTERN ANALYSIS",
              fontsize=13, color=ACC, fontweight="bold", y=0.99)

# ── Sector fraud rate ─────────────────────────────────────────
ax = axes2[0, 0]
sec_rate = df.groupby("sector").apply(
    lambda x: (x["fraud_flag"].isin(["CRITICAL","HIGH_RISK"])).mean() * 100
).sort_values(ascending=False)
sc_colors = [CRIT if v>15 else HIGH if v>8 else MED for v in sec_rate.values]
ax.barh(sec_rate.index, sec_rate.values, color=sc_colors, zorder=3, height=0.7)
ax.set_title("Sector Fraud Rate (% Critical + High Risk)", color=TEXT, pad=8)
ax.set_xlabel("%", color=MUTE)
ax.grid(axis="x", zorder=0)
for i, v in enumerate(sec_rate.values):
    ax.text(v+0.2, i, f"{v:.1f}%", va="center", fontsize=8, color=TEXT)

# ── Fraud type pie ────────────────────────────────────────────
ax = axes2[0, 1]
ft = df[df["fraud_type"] != "NONE"]["fraud_type"].value_counts()
ax.pie(ft.values,
       labels=[t.replace("_"," ").title() for t in ft.index],
       colors=[CRIT, HIGH, ACC],
       autopct="%1.1f%%",
       textprops={"color":TEXT,"fontsize":10},
       wedgeprops={"edgecolor":BG,"linewidth":2})
ax.set_title("Fraud Type Distribution", color=TEXT, pad=8)
ax.set_facecolor(BG)

# ── Zone comparison ───────────────────────────────────────────
ax = axes2[0, 2]
zone_r = df.groupby("zone").agg(
    crit_pct = ("fraud_flag", lambda x: (x=="CRITICAL").mean()*100),
    avg_itc  = ("itc_rate_pct","mean")
).reset_index().sort_values("crit_pct", ascending=False)
xz = np.arange(len(zone_r))
w  = 0.38
axr = ax.twinx()
ax.bar(xz - w/2, zone_r["crit_pct"], w, color=CRIT,  label="Critical %", zorder=3)
axr.bar(xz + w/2, zone_r["avg_itc"],  w, color=ACC,   label="Avg ITC %",  zorder=3, alpha=0.8)
ax.set_xticks(xz)
ax.set_xticklabels(zone_r["zone"], fontsize=8)
ax.set_title("Zone: Critical Flag % vs Avg ITC Rate", color=TEXT, pad=8)
ax.set_ylabel("Critical Flags %", color=CRIT, fontsize=8)
axr.set_ylabel("Avg ITC Rate %", color=ACC, fontsize=8)
axr.tick_params(axis="y", colors=ACC)
ax.grid(axis="y", zorder=0)
lines_a, la = ax.get_legend_handles_labels()
lines_b, lb = axr.get_legend_handles_labels()
ax.legend(lines_a+lines_b, la+lb, fontsize=8, facecolor=CARD, edgecolor=GRID)

# ── ITC rate vs fraud score scatter ──────────────────────────
ax = axes2[1, 0]
sc2 = ax.scatter(df["itc_rate_pct"].clip(0,130), df["fraud_score"],
                 c=df["fraud_score"], cmap="RdYlGn_r",
                 alpha=0.2, s=6, vmin=0, vmax=80)
ax.axvline(65,  color=MED,  ls="--", lw=1, alpha=0.8, label="65% Medium")
ax.axvline(85,  color=HIGH, ls="--", lw=1, alpha=0.8, label="85% High")
ax.axvline(100, color=CRIT, ls="--", lw=1, alpha=0.8, label="100% Critical")
ax.set_title("ITC Rate % vs Fraud Score", color=TEXT, pad=8)
ax.set_xlabel("ITC Claimed / Sales %", color=MUTE)
ax.set_ylabel("Fraud Score (0–100)", color=MUTE)
ax.legend(fontsize=7.5, facecolor=CARD, edgecolor=GRID)
plt.colorbar(sc2, ax=ax, label="Fraud Score", shrink=0.85)

# ── Cluster feature profiles ──────────────────────────────────
ax = axes2[1, 1]
FEATS = ["avg_itc_rate","avg_mismatch","months_flagged","avg_score"]
FEAT_LABELS = ["Avg ITC%","Mismatch%","Months\nFlagged","Avg\nScore"]
clust_agg = sf.groupby("risk_label")[FEATS].mean()
xc = np.arange(len(FEATS))
wc = 0.25
clust_colors = {"HIGH":CRIT,"MEDIUM":HIGH,"LOW":SAFE}
for i, (lbl, row) in enumerate(clust_agg.iterrows()):
    ax.bar(xc + i*wc, row.values, wc,
           color=clust_colors.get(lbl, ACC), label=lbl, zorder=3, alpha=0.85)
ax.set_xticks(xc + wc)
ax.set_xticklabels(FEAT_LABELS, fontsize=8)
ax.set_title("K-Means Cluster Feature Profiles", color=TEXT, pad=8)
ax.legend(fontsize=8, facecolor=CARD, edgecolor=GRID)
ax.grid(axis="y", zorder=0)

# ── Elbow + Silhouette curve ──────────────────────────────────
ax = axes2[1, 2]
# Recompute elbow for plotting
from sklearn.cluster import KMeans as KM
from sklearn.preprocessing import StandardScaler as SS
from sklearn.metrics import silhouette_score as sil_s
df_s2 = pd.read_csv("data/state_clusters.csv")
FEATS2 = ["avg_itc_rate","avg_mismatch","months_flagged","avg_score"]
sc2_ = SS()
X2 = sc2_.fit_transform(df_s2[FEATS2])
inn, sils = [], []
for k in range(2, 7):
    km_ = KM(n_clusters=k, random_state=42, n_init=10)
    lb_ = km_.fit_predict(X2)
    inn.append(km_.inertia_)
    sils.append(sil_s(X2, lb_))
axe2 = ax.twinx()
ax.plot(range(2,7), inn,  color=ACC,  marker="o", ms=7, lw=2, label="Inertia")
axe2.plot(range(2,7), sils, color=SAFE, marker="s", ms=7, lw=2,
          ls="--", label="Silhouette")
ax.axvline(3, color=CRIT, ls=":", lw=1.8, alpha=0.7, label="Chosen k=3")
ax.set_title("Elbow + Silhouette (choose k=3)", color=TEXT, pad=8)
ax.set_xlabel("k (number of clusters)", color=MUTE)
ax.set_ylabel("Inertia", color=ACC, fontsize=8)
axe2.set_ylabel("Silhouette Score", color=SAFE, fontsize=8)
axe2.tick_params(axis="y", colors=SAFE)
h_a, l_a = ax.get_legend_handles_labels()
h_b, l_b = axe2.get_legend_handles_labels()
ax.legend(h_a+h_b, l_a+l_b, fontsize=8, facecolor=CARD, edgecolor=GRID)
ax.grid(zorder=0)

plt.tight_layout()
fig2.savefig("visuals/02_sector_deep_dive.png", dpi=150,
             bbox_inches="tight", facecolor=BG)
plt.close()
print("  ✓ visuals/02_sector_deep_dive.png")


# ══════════════════════════════════════════════════════════════
#  FIGURE 3 — STATE RISK SCORECARD
# ══════════════════════════════════════════════════════════════
print("[CHART 3] Building state risk scorecard...")
fig3, ax3f = plt.subplots(figsize=(17, 9), facecolor=BG)

sf_s = sf.sort_values("avg_score", ascending=True)
bar_c3 = [{"HIGH":CRIT,"MEDIUM":HIGH,"LOW":SAFE}.get(r, MUTE)
           for r in sf_s["risk_label"]]
bars3 = ax3f.barh(sf_s["state"], sf_s["avg_score"],
                   color=bar_c3, zorder=3, height=0.72)

for bar, row in zip(bars3, sf_s.itertuples()):
    w = bar.get_width()
    ax3f.text(w+0.3, bar.get_y()+bar.get_height()/2,
              f"  ITC:{row.avg_itc_rate:.0f}%  |  Flagged:{row.months_flagged}mo  |  {row.risk_label}",
              va="center", fontsize=8, color=MUTE)

ax3f.axvline(20, color=MED,  ls="--", lw=1.2, alpha=0.8)
ax3f.axvline(35, color=CRIT, ls="--", lw=1.2, alpha=0.8)
ax3f.text(20.5, len(sf_s)-0.5, "Medium threshold", fontsize=7.5, color=MED)
ax3f.text(35.5, len(sf_s)-0.5, "High threshold",   fontsize=7.5, color=CRIT)

legend_patches = [
    mpatches.Patch(color=CRIT, label="HIGH risk cluster  (Bihar, Delhi, UP, West Bengal)"),
    mpatches.Patch(color=HIGH, label="MEDIUM risk cluster (9 states)"),
    mpatches.Patch(color=SAFE, label="LOW risk cluster    (7 states)"),
]
ax3f.legend(handles=legend_patches, fontsize=9,
            facecolor=CARD, edgecolor=GRID, loc="lower right")
ax3f.set_title("STATE FRAUD RISK SCORECARD  |  K-Means Composite Index",
               color=ACC, fontsize=14, fontweight="bold", pad=14)
ax3f.set_xlabel("Avg Composite Fraud Score (0–100)", color=MUTE, fontsize=11)
ax3f.grid(axis="x", zorder=0)

fig3.tight_layout()
fig3.savefig("visuals/03_state_scorecard.png", dpi=150,
             bbox_inches="tight", facecolor=BG)
plt.close()
print("  ✓ visuals/03_state_scorecard.png")

print("\n[DONE] All 3 charts saved to visuals/")
