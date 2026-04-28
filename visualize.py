"""
visualize.py
AML Transaction Monitoring — Visualization Suite
6 charts that tell a compliance story, not just pretty plots.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings("ignore")

PALETTE = {
    "normal":  "#2196F3",
    "high":    "#F44336",
    "medium":  "#FF9800",
    "low":     "#4CAF50",
    "accent":  "#9C27B0",
    "bg":      "#0F1117",
    "surface": "#1A1D27",
    "text":    "#E8EAF6",
    "grid":    "#2A2D3A",
}


def load_data():
    scored  = pd.read_csv("outputs/scored_transactions.csv", parse_dates=["timestamp"])
    flagged = pd.read_csv("outputs/flagged_transactions.csv", parse_dates=["timestamp"])
    return scored, flagged


def apply_dark_style(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(PALETTE["surface"])
    ax.tick_params(colors=PALETTE["text"], labelsize=9)
    ax.xaxis.label.set_color(PALETTE["text"])
    ax.yaxis.label.set_color(PALETTE["text"])
    ax.title.set_color(PALETTE["text"])
    for spine in ax.spines.values():
        spine.set_edgecolor(PALETTE["grid"])
    ax.grid(color=PALETTE["grid"], linestyle="--", linewidth=0.5, alpha=0.6)
    if title:  ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    if xlabel: ax.set_xlabel(xlabel, fontsize=9)
    if ylabel: ax.set_ylabel(ylabel, fontsize=9)


def plot_all(scored, flagged):
    fig = plt.figure(figsize=(18, 12), facecolor=PALETTE["bg"])
    fig.suptitle(
        "Synthetic MFS Transaction Anomaly Detection  |  bKash-Style AML Monitoring",
        fontsize=15, fontweight="bold", color=PALETTE["text"], y=0.98
    )

    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    ax4 = fig.add_subplot(gs[1, 0])
    ax5 = fig.add_subplot(gs[1, 1])
    ax6 = fig.add_subplot(gs[1, 2])

    tier_counts = scored["risk_tier"].value_counts().reindex(["HIGH", "MEDIUM", "LOW"])
    colors = [PALETTE["high"], PALETTE["medium"], PALETTE["low"]]
    wedges, texts, autotexts = ax1.pie(
        tier_counts, labels=tier_counts.index, autopct="%1.1f%%",
        colors=colors, startangle=90, wedgeprops=dict(width=0.55),
        textprops={"color": PALETTE["text"], "fontsize": 9}
    )
    for at in autotexts:
        at.set_color(PALETTE["bg"])
        at.set_fontweight("bold")
    ax1.set_facecolor(PALETTE["surface"])
    ax1.set_title("Risk Tier Distribution", fontsize=11, fontweight="bold",
                  color=PALETTE["text"], pad=10)
    total_flagged = (scored["risk_score"] > 0).sum()
    ax1.text(0, 0, f"{total_flagged:,}\nFlagged", ha="center", va="center",
             fontsize=11, fontweight="bold", color=PALETTE["text"])

    normal_amounts  = scored[scored["risk_score"] == 0]["amount_bdt"]
    flagged_amounts = scored[scored["risk_score"] >  0]["amount_bdt"]
    bins = np.linspace(0, 30_000, 50)
    ax2.hist(normal_amounts,  bins=bins, alpha=0.6, color=PALETTE["normal"],
             label=f"Normal ({len(normal_amounts):,})", density=True)
    ax2.hist(flagged_amounts, bins=bins, alpha=0.7, color=PALETTE["high"],
             label=f"Flagged ({len(flagged_amounts):,})", density=True)
    apply_dark_style(ax2, "Amount Distribution: Normal vs Flagged", "Amount (BDT)", "Density")
    ax2.legend(fontsize=8, facecolor=PALETTE["surface"], labelcolor=PALETTE["text"])

    scored["hour"] = scored["timestamp"].dt.hour
    total_by_hour   = scored.groupby("hour").size()
    flagged_by_hour = scored[scored["risk_score"] > 0].groupby("hour").size().reindex(range(24), fill_value=0)
    flag_rate = (flagged_by_hour / total_by_hour * 100).fillna(0)
    bar_colors = [PALETTE["high"] if (1 <= h <= 3) else PALETTE["normal"] for h in range(24)]
    ax3.bar(range(24), flag_rate, color=bar_colors, alpha=0.85, width=0.7)
    ax3.axvspan(0.5, 3.5, alpha=0.15, color=PALETTE["high"])
    ax3.text(2, flag_rate.max() * 0.85, "Late\nNight", ha="center",
             color=PALETTE["high"], fontsize=8, fontweight="bold")
    apply_dark_style(ax3, "Flagged Transaction Rate by Hour", "Hour of Day (0–23)", "Flag Rate (%)")
    ax3.set_xticks(range(0, 24, 2))

    rule_cols  = [c for c in scored.columns if c.startswith("RULE_")]
    rule_hits  = scored[rule_cols].sum().sort_values(ascending=True)
    rule_names = [r.replace("RULE_", "").replace("_", " ").title() for r in rule_hits.index]
    bar_colors4 = [PALETTE["high"] if v > 100 else PALETTE["medium"] for v in rule_hits.values]
    bars = ax4.barh(rule_names, rule_hits.values, color=bar_colors4, alpha=0.85, height=0.6)
    for bar, val in zip(bars, rule_hits.values):
        ax4.text(val + 5, bar.get_y() + bar.get_height()/2,
                 str(val), va="center", color=PALETTE["text"], fontsize=8)
    apply_dark_style(ax4, "AML Rule — Hit Frequency", "Number of Transactions", "")
    ax4.set_facecolor(PALETTE["surface"])

    nonzero_scores = scored[scored["risk_score"] > 0]["risk_score"]
    ax5.hist(nonzero_scores, bins=20, color=PALETTE["accent"], alpha=0.8, edgecolor=PALETTE["bg"])
    ax5.axvline(30, color=PALETTE["medium"], linestyle="--", linewidth=1.5, label="MEDIUM (30)")
    ax5.axvline(60, color=PALETTE["high"],   linestyle="--", linewidth=1.5, label="HIGH (60)")
    apply_dark_style(ax5, "Risk Score Distribution (Flagged Only)", "Composite Risk Score", "Count")
    ax5.legend(fontsize=8, facecolor=PALETTE["surface"], labelcolor=PALETTE["text"])

    scored["month"] = scored["timestamp"].dt.to_period("M")
    monthly_total   = scored.groupby("month").size()
    monthly_flagged = scored[scored["risk_score"] > 0].groupby("month").size()
    monthly_high    = scored[scored["risk_tier"] == "HIGH"].groupby("month").size()
    months = [str(m) for m in monthly_total.index]
    x = np.arange(len(months))
    w = 0.28
    ax6.bar(x - w, monthly_total.values / 1000, w*2.5, label="Total (k)", color=PALETTE["normal"], alpha=0.7)
    ax6.bar(x,     monthly_flagged.reindex(monthly_total.index, fill_value=0).values, w*2.5,
            label="Flagged", color=PALETTE["medium"], alpha=0.8)
    ax6.bar(x + w, monthly_high.reindex(monthly_total.index, fill_value=0).values, w*2.5,
            label="HIGH Risk", color=PALETTE["high"], alpha=0.9)
    ax6.set_xticks(x)
    ax6.set_xticklabels(months, fontsize=9, color=PALETTE["text"])
    apply_dark_style(ax6, "Monthly Transaction Monitoring Trend", "Month", "Count")
    ax6.legend(fontsize=8, facecolor=PALETTE["surface"], labelcolor=PALETTE["text"])

    plt.savefig("outputs/aml_dashboard.png", dpi=150, bbox_inches="tight",
                facecolor=PALETTE["bg"])
    print("✅ Dashboard saved → outputs/aml_dashboard.png")
    plt.show()


if __name__ == "__main__":
    scored, flagged = load_data()
    plot_all(scored, flagged)
