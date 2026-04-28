"""
detect_anomalies.py
Rule-Based AML Transaction Monitoring Engine
Mirrors real-world TMR (Transaction Monitoring Rule) approach used in
NICE Actimize, Oracle FCCM, and BD FI compliance systems.

Risk Score = weighted sum of rule hits (0–100)
  Score  0–29  → LOW    risk
  Score 30–59  → MEDIUM risk  
  Score 60–100 → HIGH   risk (SAR candidate)
"""

import pandas as pd
import numpy as np

# ── Rule Weights (tunable) ──────────────────────────────────────────────────
RULE_WEIGHTS = {
    "RULE_STRUCTURING":    35,  # High — deliberate threshold evasion
    "RULE_VELOCITY":       25,  # High — account takeover / layering signal
    "RULE_LATE_NIGHT":     15,  # Medium — suspicious timing
    "RULE_ROUND_AMOUNT":   10,  # Booster only — standalone not suspicious in BD MFS
    "RULE_DORMANT_SPIKE":  30,  # High — dormant account reactivation
    "RULE_HIGH_VALUE":     10,  # Low — alone not suspicious
}


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


# ── Rule Definitions ─────────────────────────────────────────────────────────

def rule_structuring(df: pd.DataFrame, threshold=10_000, window_hours=24, min_txns=3) -> pd.Series:
    """
    Flag senders with ≥3 txns in 24h all below threshold (structuring/smurfing).
    """
    df = df.copy()
    df["_hit"] = False

    for sender, group in df.groupby("sender_id"):
        group = group.sort_values("timestamp")
        for i, row in group.iterrows():
            window = group[
                (group["timestamp"] >= row["timestamp"]) &
                (group["timestamp"] < row["timestamp"] + pd.Timedelta(hours=window_hours)) &
                (group["amount_bdt"] < threshold) &
                (group["amount_bdt"] >= threshold * 0.80)
            ]
            if len(window) >= min_txns:
                df.loc[window.index, "_hit"] = True

    return df["_hit"]


def rule_velocity(df: pd.DataFrame, window_minutes=60, min_txns=5) -> pd.Series:
    """
    Flag accounts sending ≥5 txns within any 60-minute rolling window.
    """
    df = df.copy()
    df["_hit"] = False

    for sender, group in df.groupby("sender_id"):
        group = group.sort_values("timestamp")
        for i, row in group.iterrows():
            window = group[
                (group["timestamp"] >= row["timestamp"]) &
                (group["timestamp"] < row["timestamp"] + pd.Timedelta(minutes=window_minutes))
            ]
            if len(window) >= min_txns:
                df.loc[window.index, "_hit"] = True

    return df["_hit"]


def rule_late_night(df: pd.DataFrame, start_hour=1, end_hour=4) -> pd.Series:
    """
    Flag txns occurring between 01:00–04:00 AM local time.
    """
    hour = df["timestamp"].dt.hour
    return (hour >= start_hour) & (hour < end_hour)


def rule_round_amount(df: pd.DataFrame, min_amount=50_000, profile_multiplier=5) -> pd.Series:
    """
    Round amounts are NORMAL in BD MFS — people routinely send 500, 1000,
    5000, 10000 BDT for rent, bazar, remittance etc.

    Flag ONLY when BOTH true:
      1. Amount >= 50,000 BDT (above daily casual use)
      2. Amount >= 5x sender's own median transaction (profile outlier)

    Eliminates false positives from normal cash-out/send-money behavior.
    BD fintech context: round figures are culturally normative in MFS usage.
    """
    sender_median = df.groupby("sender_id")["amount_bdt"].transform("median")
    is_large_round = (df["amount_bdt"] % 10_000 == 0) & (df["amount_bdt"] >= min_amount)
    is_profile_outlier = df["amount_bdt"] >= (sender_median * profile_multiplier)
    return is_large_round & is_profile_outlier


def rule_dormant_spike(df: pd.DataFrame, inactive_days=30, spike_threshold=10_000) -> pd.Series:
    """
    Flag accounts with no activity for 30+ days that suddenly transact above spike_threshold.
    Uses vectorized groupby+shift — no row iteration.
    """
    d = df[["transaction_id", "sender_id", "timestamp", "amount_bdt"]].copy()
    d = d.sort_values(["sender_id", "timestamp"])
    d["prev_ts"] = d.groupby("sender_id")["timestamp"].shift(1)
    d["gap_days"] = (d["timestamp"] - d["prev_ts"]).dt.days
    hit_mask = (d["gap_days"] >= inactive_days) & (d["amount_bdt"] >= spike_threshold)
    hit_ids = set(d.loc[hit_mask, "transaction_id"])
    return df["transaction_id"].isin(hit_ids)


def rule_high_value(df: pd.DataFrame, threshold=20_000) -> pd.Series:
    """
    Flag any single txn above 20,000 BDT (near bKash daily limit).
    Weak signal alone but boosts composite score when combined.
    """
    return df["amount_bdt"] >= threshold


# ── Risk Scoring Engine ───────────────────────────────────────────────────────

def compute_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    print("⚙️  Running rule engine...")
    df = df.copy()

    print("  → Rule: Structuring...", end=" ", flush=True)
    df["RULE_STRUCTURING"]   = rule_structuring(df).astype(int)
    print(f"{df['RULE_STRUCTURING'].sum()} hits")

    print("  → Rule: Velocity...", end=" ", flush=True)
    df["RULE_VELOCITY"]      = rule_velocity(df).astype(int)
    print(f"{df['RULE_VELOCITY'].sum()} hits")

    print("  → Rule: Late Night...", end=" ", flush=True)
    df["RULE_LATE_NIGHT"]    = rule_late_night(df).astype(int)
    print(f"{df['RULE_LATE_NIGHT'].sum()} hits")

    print("  → Rule: Round Amount...", end=" ", flush=True)
    df["RULE_ROUND_AMOUNT"]  = rule_round_amount(df).astype(int)
    print(f"{df['RULE_ROUND_AMOUNT'].sum()} hits")

    print("  → Rule: Dormant Spike...", end=" ", flush=True)
    df["RULE_DORMANT_SPIKE"] = rule_dormant_spike(df).astype(int)
    print(f"{df['RULE_DORMANT_SPIKE'].sum()} hits")

    print("  → Rule: High Value...", end=" ", flush=True)
    df["RULE_HIGH_VALUE"]    = rule_high_value(df).astype(int)
    print(f"{df['RULE_HIGH_VALUE'].sum()} hits")

    df["risk_score"] = (
        df["RULE_STRUCTURING"]   * RULE_WEIGHTS["RULE_STRUCTURING"]   +
        df["RULE_VELOCITY"]      * RULE_WEIGHTS["RULE_VELOCITY"]      +
        df["RULE_LATE_NIGHT"]    * RULE_WEIGHTS["RULE_LATE_NIGHT"]    +
        df["RULE_ROUND_AMOUNT"]  * RULE_WEIGHTS["RULE_ROUND_AMOUNT"]  +
        df["RULE_DORMANT_SPIKE"] * RULE_WEIGHTS["RULE_DORMANT_SPIKE"] +
        df["RULE_HIGH_VALUE"]    * RULE_WEIGHTS["RULE_HIGH_VALUE"]
    ).clip(upper=100)

    df["risk_tier"] = pd.cut(
        df["risk_score"],
        bins=[-1, 29, 59, 100],
        labels=["LOW", "MEDIUM", "HIGH"]
    )

    rule_cols = [c for c in df.columns if c.startswith("RULE_")]
    df["rules_triggered"] = df[rule_cols].apply(
        lambda row: ", ".join([c for c in rule_cols if row[c] == 1]) or "NONE",
        axis=1
    )

    return df


def print_summary(df: pd.DataFrame):
    print("\n" + "="*55)
    print("  AML DETECTION SUMMARY REPORT")
    print("="*55)
    print(f"  Total transactions analyzed : {len(df):>8,}")
    print(f"  Flagged (any rule hit)      : {(df['risk_score'] > 0).sum():>8,}")
    print(f"  HIGH risk (SAR candidates)  : {(df['risk_tier'] == 'HIGH').sum():>8,}")
    print(f"  MEDIUM risk (review queue)  : {(df['risk_tier'] == 'MEDIUM').sum():>8,}")
    print()
    print("  Rule Hit Breakdown:")
    for rule, weight in RULE_WEIGHTS.items():
        if rule in df.columns:
            n = df[rule].sum()
            print(f"    {rule:<25} {n:>5,}  (weight={weight})")
    print("="*55)


def save_flagged(df: pd.DataFrame, path="outputs/flagged_transactions.csv"):
    flagged = df[df["risk_score"] > 0].sort_values("risk_score", ascending=False)
    flagged.to_csv(path, index=False)
    print(f"\n✅ Flagged transactions saved → {path}  ({len(flagged):,} rows)")
    return flagged


if __name__ == "__main__":
    df = load_data("outputs/raw_transactions.csv")
    df = compute_risk_score(df)
    print_summary(df)
    flagged = save_flagged(df)
    df.to_csv("outputs/scored_transactions.csv", index=False)
    print(f"✅ Full scored data saved → outputs/scored_transactions.csv")
