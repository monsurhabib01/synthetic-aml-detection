"""
generate_data.py
Synthetic MFS Transaction Data Generator — bKash style
Injects 5 AML-relevant anomaly types into realistic transaction data.

Anomaly Types:
  1. STRUCTURING      — multiple txns just below 10,000 BDT reporting threshold
  2. VELOCITY         — >5 txns within 60 minutes from same account
  3. LATE_NIGHT       — txns between 01:00–04:00 AM
  4. ROUND_AMOUNT     — exact large round-number transfers (50k, 100k, 200k)
  5. DORMANT_SPIKE    — account inactive 30+ days suddenly doing high-value txn
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

SEED = 42
np.random.seed(SEED)
random.seed(SEED)

# ── Config ──────────────────────────────────────────────────────────────────
N_NORMAL        = 9_500
N_STRUCTURING   = 150   # injected in clusters of 3–5
N_VELOCITY      = 80
N_LATE_NIGHT    = 120
N_ROUND_AMOUNT  = 100
N_DORMANT_SPIKE = 50

START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2024, 3, 31)
DATE_RANGE_DAYS = (END_DATE - START_DATE).days

TX_TYPES = ['cash_out', 'send_money', 'cash_in', 'payment', 'add_money']
TX_TYPE_WEIGHTS = [0.38, 0.30, 0.18, 0.10, 0.04]  # cash_out dominates in BD MFS

DIVISIONS = ['Dhaka', 'Chittagong', 'Sylhet', 'Rajshahi', 'Khulna', 'Barishal', 'Rangpur', 'Mymensingh']
DIV_WEIGHTS = [0.45, 0.20, 0.10, 0.08, 0.07, 0.04, 0.04, 0.02]

N_CUSTOMERS = 300

# ── Helpers ──────────────────────────────────────────────────────────────────
def random_account():
    return f"01{random.randint(3,9)}{random.randint(10_000_000, 99_999_999)}"

def random_timestamp(start=START_DATE, days=DATE_RANGE_DAYS):
    offset = timedelta(
        days=random.randint(0, days),
        hours=random.randint(7, 22),     # normal business hours
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    return start + offset

def make_row(sender, receiver, amount, tx_type, ts, anomaly_flag="NORMAL"):
    return {
        "transaction_id": f"TXN{random.randint(100_000_000, 999_999_999)}",
        "timestamp":      ts,
        "sender_id":      sender,
        "receiver_id":    receiver,
        "tx_type":        tx_type,
        "amount_bdt":     int(round(amount)),  # whole BDT — no paisa in BD MFS
        "division":       np.random.choice(DIVISIONS, p=DIV_WEIGHTS),
        "anomaly_flag":   anomaly_flag
    }

# Pre-generate customer pool (NORMAL transactions only)
customers = [random_account() for _ in range(N_CUSTOMERS)]

# Separate pool for dormant spike — these accounts don't appear in normal txns
dormant_pool = [random_account() for _ in range(N_DORMANT_SPIKE)]

# ── 1. Normal Transactions ───────────────────────────────────────────────────
rows = []
for _ in range(N_NORMAL):
    sender   = random.choice(customers)
    receiver = random.choice([c for c in customers if c != sender])
    tx_type  = np.random.choice(TX_TYPES, p=TX_TYPE_WEIGHTS)

    # 60% chance of round amount — realistic BD MFS behavior
    # (rent, bazar, rickshaw, utility bills are almost always round)
    if random.random() < 0.60:
        common_rounds = [500, 1000, 1500, 2000, 3000, 5000, 8000, 10000, 15000, 20000]
        amount = random.choice(common_rounds)
    else:
        amount = np.random.lognormal(mean=7.0, sigma=1.0)
        amount = min(amount, 25_000)
        amount = round(amount)

    ts = random_timestamp()
    rows.append(make_row(sender, receiver, amount, tx_type, ts, "NORMAL"))

# ── 2. Structuring (Smurfing) ────────────────────────────────────────────────
THRESHOLD = 10_000
structuring_senders = random.choices(customers, k=35)

for sender in structuring_senders:
    cluster_size = random.randint(3, 5)
    base_ts = random_timestamp()
    for i in range(cluster_size):
        amount   = random.randint(8_500, 9_999)
        receiver = random.choice([c for c in customers if c != sender])
        ts       = base_ts + timedelta(minutes=random.randint(5, 45))
        rows.append(make_row(sender, receiver, amount, 'send_money', ts, "STRUCTURING"))

# ── 3. Velocity Burst ────────────────────────────────────────────────────────
velocity_senders = random.choices(customers, k=10)

for sender in velocity_senders:
    burst_count = random.randint(6, 12)
    base_ts = random_timestamp()
    for i in range(burst_count):
        amount   = random.randint(500, 5_000)
        receiver = random.choice([c for c in customers if c != sender])
        ts       = base_ts + timedelta(minutes=random.randint(0, 59))
        rows.append(make_row(sender, receiver, amount, random.choice(['send_money', 'payment']), ts, "VELOCITY"))

# ── 4. Late Night Transactions ───────────────────────────────────────────────
for _ in range(N_LATE_NIGHT):
    sender   = random.choice(customers)
    receiver = random.choice([c for c in customers if c != sender])
    amount   = random.randint(1_000, 20_000)
    tx_type  = np.random.choice(TX_TYPES, p=TX_TYPE_WEIGHTS)
    base_ts  = START_DATE + timedelta(days=random.randint(0, DATE_RANGE_DAYS))
    ts       = base_ts.replace(hour=random.randint(1, 3), minute=random.randint(0, 59))
    rows.append(make_row(sender, receiver, amount, tx_type, ts, "LATE_NIGHT"))

# ── 5. Round Amount ──────────────────────────────────────────────────────────
ROUND_AMOUNTS = [50_000, 100_000, 200_000, 500_000]
for _ in range(N_ROUND_AMOUNT):
    sender   = random.choice(customers)
    receiver = random.choice([c for c in customers if c != sender])
    amount   = random.choice(ROUND_AMOUNTS)
    ts       = random_timestamp()
    rows.append(make_row(sender, receiver, amount, 'send_money', ts, "ROUND_AMOUNT"))

# ── 6. Dormant Account Spike ─────────────────────────────────────────────────
for acc in dormant_pool:
    early_ts    = START_DATE + timedelta(days=random.randint(0, 8))
    receiver    = random.choice(customers)
    seed_amount = random.randint(200, 1_000)
    rows.append(make_row(acc, receiver, seed_amount, 'cash_in', early_ts, "NORMAL"))

    spike_ts = early_ts + timedelta(days=random.randint(35, 80))
    if spike_ts > END_DATE:
        spike_ts = END_DATE - timedelta(days=1)
    receiver = random.choice(customers)
    amount   = random.randint(15_000, 25_000)
    rows.append(make_row(acc, receiver, amount, 'cash_out', spike_ts, "DORMANT_SPIKE"))

# ── Assemble & Save ──────────────────────────────────────────────────────────
df = pd.DataFrame(rows)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)

os.makedirs("outputs", exist_ok=True)
df.to_csv("outputs/raw_transactions.csv", index=False)

print(f"✅ Generated {len(df):,} transactions")
print(df["anomaly_flag"].value_counts())
print(f"\nDate range: {df['timestamp'].min().date()} → {df['timestamp'].max().date()}")
