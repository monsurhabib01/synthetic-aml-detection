# Gumroad Product Listing

Copy-paste ready. All sections labelled.

---

## Product Title

```
Python AML & Fraud Detection Toolkit — Jupyter Notebooks + LightGBM + Rule Engine
```

---

## Summary / Subtitle

```
Build a production-style Anti-Money Laundering system in Python: synthetic data, 6 BFIU-calibrated rules, LightGBM ML model, and SAR report export — complete with 3 Jupyter notebooks.
```

---

## Price

**$39**

- Underprice = perceived as low quality; overprice = low conversion from South Asian market
- $39 hits both: accessible to BD/IN/PK job seekers, credible to global fintech devs
- Raise to $49 after 10 reviews

---

## Tags

```
python, machine learning, fraud detection, anti money laundering, AML, fintech,
LightGBM, jupyter notebook, data science portfolio, transaction monitoring,
financial crime, banking analytics, scikit-learn, pandas
```

---

## Full Description

---

**Stop submitting generic data science projects. Land fintech and AML roles with a portfolio project that actually shows domain knowledge.**

Most Python fraud detection projects on GitHub use the same Kaggle credit card dataset everyone has already seen. Hiring managers notice. This toolkit is different — it’s built on realistic Bangladesh MFS (bKash/Nagad) transaction patterns, calibrated to real BFIU reporting rules, and walks you through the exact workflow used by AML compliance teams.

---

### 📦 What’s Inside

**3 Step-by-Step Jupyter Notebooks**

| # | Notebook | What it covers |
|---|---|---|
| 01 | Data Generation & EDA | 10,000+ synthetic bKash-style transactions, anomaly injection, full EDA |
| 02 | Rule Engine | 6 BFIU-calibrated AML rules, weighted risk scoring (0–100), precision/recall analysis |
| 03 | ML Detection | LightGBM classifier, feature engineering, ROC/PR curves, threshold tuning, SAR export |

**Python Source Scripts**
- `generate_data.py` — Synthetic MFS transaction generator (bKash phone format, BDT, 8 divisions)
- `detect_anomalies.py` — Production-style rule engine with composite risk scoring
- `visualize.py` — 6-chart compliance dashboard

**Documentation**
- `USAGE_GUIDE.md` — Step-by-step instructions for beginners
- `RULE_CALIBRATION.md` — Full rationale for every BFIU rule weight (unique — nowhere else)

**Output Files Generated**
- `raw_transactions.csv` — Synthetic dataset ready to explore
- `scored_transactions.csv` — Every transaction with risk scores and rule flags
- `flagged_transactions.csv` — Alert queue (risk_score > 0)
- `sar_candidates.csv` — SAR-candidate export combining rule engine + ML scores

---

### 🎯 Who This Is For

✅ **Data science job seekers** applying to fintech, banking, or AML roles

✅ **AML/compliance analysts** learning Python — you know the domain, this teaches you to code it

✅ **Fintech developers** who need a working proof-of-concept transaction monitoring engine

✅ **CS / BBA students** preparing for ACAMS, ICA, or fintech interviews

---

### ⚙️ The Full Pipeline

```
Synthetic Data (10k txns)
        ↓
Rule Engine (6 BFIU rules)
  → STRUCTURING: ≥3 txns below BDT 10,000 in 24h
  → VELOCITY: ≥5 txns within 60 minutes
  → DORMANT_SPIKE: inactive 30+ days → sudden high-value txn
  → LATE_NIGHT: transactions 01:00–04:00 AM
  → ROUND_AMOUNT: large round BDT vs sender profile
  → HIGH_VALUE: single txn above BDT 20,000
        ↓
Risk Score (0–100) → LOW / MEDIUM / HIGH
        ↓
LightGBM ML Layer (reduces false positives)
        ↓
SAR Candidates Export (.csv)
```

---

### 🔬 What Makes This Different

**BD-specific calibration — not found anywhere else.**

Generic AML tools flag round-number transactions as suspicious. In Bangladesh, round amounts (BDT 500, 1,000, 5,000, 10,000) are perfectly normal — rent, bazar shopping, rickshaw fares. This toolkit is calibrated for that reality. The `ROUND_AMOUNT` rule only fires when an amount is both ≥ BDT 50,000 AND ≥ 5× the sender’s own median — eliminating the false positives that would break a generic model.

Every rule weight is documented against BFIU Circular No. 5 (2019) and the ML/TF Prevention Act 2012. You can explain every number to a compliance officer.

---

### 📊 Tech Stack

Python 3.9+ · Pandas · NumPy · Scikit-learn · LightGBM · Matplotlib · Seaborn · Jupyter

---

### 🎓 What You’ll Be Able to Do After

- Explain the 3-layer AML detection hierarchy (rules → ML → human review) in any interview
- Build a transaction monitoring rule engine from scratch for any MFS dataset
- Train LightGBM on imbalanced financial data with proper `scale_pos_weight` tuning
- Produce a SAR-candidate export in the format real compliance teams use
- Discuss BFIU reporting obligations, structuring, and EDD triggers with domain accuracy

---

### ❓ FAQ

**Do I need AML experience?**
No. Notebooks explain compliance logic behind every code cell.

**Windows / Mac / Linux?**
Yes. Pure Python + standard packages. Works anywhere Jupyter runs.

**Can I use this in my portfolio / GitHub?**
Yes. MIT license.

**Is the data real?**
No. 100% synthetically generated. No real user data, no privacy concerns.

**What Python level do I need?**
Intermediate — comfortable with Pandas DataFrames. No prior ML required for notebooks 01–02.

---

### 🚀 Get It

One-time purchase. Instant download. Includes all future updates.

**$39** — or the price of one hour of freelance work that will pay back 100×.
