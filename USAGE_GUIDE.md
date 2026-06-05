# Usage Guide

Step-by-step instructions for running the AML detection system from scratch.

---

## Prerequisites

- Python 3.9 or higher
- pip (comes with Python)
- ~50 MB disk space for output files

No prior AML knowledge required. The guide explains what each step does.

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/monsurhabib01/synthetic-aml-detection.git
cd synthetic-aml-detection

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Step 1 — Generate Synthetic Transactions

```bash
python generate_data.py
```

**What this does:**
Generates a realistic dataset of ~10,000 transactions modeled on Bangladesh Mobile Financial Services (bKash/Nagad patterns). Five types of anomalies are injected at known positions:

| Anomaly | Count | Description |
|---------|-------|-------------|
| STRUCTURING | ~150 | Multiple txns just below BDT 10,000 threshold |
| VELOCITY | ~80 | Burst of 6–12 txns within 60 minutes |
| LATE_NIGHT | 120 | Transactions between 01:00–04:00 AM |
| ROUND_AMOUNT | 100 | Large exact-round transfers (50K, 100K, 200K, 500K BDT) |
| DORMANT_SPIKE | 50 | Inactive account → sudden high-value transaction |

**Output:** `outputs/raw_transactions.csv`

```
Columns: transaction_id, timestamp, sender_id, receiver_id,
         tx_type, amount_bdt, division, anomaly_flag
```

> `anomaly_flag` is the **ground truth label** — useful for evaluating rule precision.

---

## Step 2 — Run the AML Rule Engine

```bash
python detect_anomalies.py
```

**What this does:**
Applies 6 rule-based detectors to every transaction. Each rule returns a binary hit (0/1). The hits are multiplied by rule weights and summed into a `risk_score` (0–100).

Expected terminal output:
```
⚙️  Running rule engine...
  → Rule: Structuring... 182 hits
  → Rule: Velocity... 94 hits
  → Rule: Late Night... 120 hits
  → Rule: Round Amount... 61 hits
  → Rule: Dormant Spike... 50 hits
  → Rule: High Value... 471 hits

=======================================================
  AML DETECTION SUMMARY REPORT
=======================================================
  Total transactions analyzed :   10,250
  Flagged (any rule hit)      :      820
  HIGH risk (SAR candidates)  :      127
  MEDIUM risk (review queue)  :      284
=======================================================
```

**Output files:**
- `outputs/scored_transactions.csv` — all transactions with risk scores
- `outputs/flagged_transactions.csv` — only transactions with `risk_score > 0`

**Understanding the output columns:**

| Column | Description |
|--------|-------------|
| `risk_score` | 0–100 composite score |
| `risk_tier` | `LOW` / `MEDIUM` / `HIGH` |
| `RULE_STRUCTURING` | 1 if structuring rule fired, else 0 |
| `RULE_VELOCITY` | 1 if velocity rule fired, else 0 |
| `rules_triggered` | Comma-separated list of all rules that fired |

---

## Step 3 — View the Compliance Dashboard

```bash
python visualize.py
```

**What this generates (6 charts):**

1. **Risk tier distribution** — breakdown of LOW / MEDIUM / HIGH transactions
2. **Rule hit counts** — which rules fired most
3. **Transaction volume over time** — time-series of daily transaction counts
4. **Amount distribution by risk tier** — box plots showing amount ranges per tier
5. **Hourly heatmap** — transaction activity by hour of day
6. **Division-level flagging rate** — geographic breakdown of HIGH-risk transactions

Charts are saved to the `images/` folder and displayed interactively.

---

## Customizing Thresholds

All rule parameters are tunable. To adjust:

**In `detect_anomalies.py` — change rule weights:**
```python
RULE_WEIGHTS = {
    "RULE_STRUCTURING":    35,   # increase to be more aggressive
    "RULE_VELOCITY":       25,
    "RULE_LATE_NIGHT":     15,
    "RULE_ROUND_AMOUNT":   10,
    "RULE_DORMANT_SPIKE":  30,
    "RULE_HIGH_VALUE":     10,
}
```

**To change risk tier cutoffs:**
```python
# Current: 0–29 LOW, 30–59 MEDIUM, 60–100 HIGH
df["risk_tier"] = pd.cut(
    df["risk_score"],
    bins=[-1, 29, 59, 100],
    labels=["LOW", "MEDIUM", "HIGH"]
)
```

**To change the structuring threshold (default BDT 10,000):**
```python
df["RULE_STRUCTURING"] = rule_structuring(df, threshold=10_000).astype(int)
# Change threshold=10_000 to match your jurisdiction's reporting limit
```

---

## Evaluating Rule Performance

Since `anomaly_flag` in the raw data is the ground truth, you can measure precision and recall:

```python
import pandas as pd
from sklearn.metrics import classification_report

df = pd.read_csv('outputs/scored_transactions.csv')

# Binary: flagged vs not flagged
y_true = (df['anomaly_flag'] != 'NORMAL').astype(int)
y_pred = (df['risk_score'] > 0).astype(int)

print(classification_report(y_true, y_pred))
```

This is a good addition to any fintech portfolio — showing you understand precision/recall tradeoffs in AML is a strong interview signal.

---

## Common Issues

**`ModuleNotFoundError: No module named 'pandas'`**
```bash
pip install -r requirements.txt
```

**`FileNotFoundError: outputs/raw_transactions.csv`**
Run `generate_data.py` first before `detect_anomalies.py`.

**Dashboard window doesn't open**
Add this to the top of `visualize.py`:
```python
import matplotlib
matplotlib.use('Agg')   # for headless/server environments
```
This saves charts to `images/` instead of displaying interactively.
