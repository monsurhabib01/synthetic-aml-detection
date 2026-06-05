# Python AML & Fraud Detection System

**Production-Style Transaction Monitoring Engine | bKash/Nagad Patterns | BFIU-Calibrated**

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

> **A complete fraud detection portfolio project** — synthetic data generation, rule-based transaction monitoring, composite risk scoring, and a compliance dashboard. Built with real-world AML logic used in fintech and banking.

---

## Who This Is For

- 🎓 **Data science students** building a fintech portfolio project for job applications
- 💼 **AML/compliance analysts** learning to apply Python to transaction monitoring
- 🏗️ **Fintech developers** who need a proof-of-concept AML rule engine
- 📋 **ACAMS/ICA exam preppers** wanting hands-on exposure to real TME logic

---

## What You Will Build

```
10,000+ synthetic transactions  →  Rule Engine (6 AML rules)  →  Risk Scores  →  Dashboard
     (bKash-style MFS)               (BFIU-calibrated)           (0–100 score)    (6 charts)
```

**Output**: A flagged transaction report with `risk_score` and `risk_tier` (LOW / MEDIUM / HIGH) — the same output structure used by real transaction monitoring systems like NICE Actimize and Oracle FCCM.

---

## AML Rules Engine (6 Rules)

| Rule | Weight | What It Detects |
|------|--------|-----------------|
| `STRUCTURING` | 35 | ≥3 txns in 24h all between 80–100% of BDT 10,000 threshold (smurfing) |
| `DORMANT_SPIKE` | 30 | Account inactive 30+ days → sudden high-value transaction |
| `VELOCITY` | 25 | ≥5 txns within any 60-minute window (layering / account takeover) |
| `LATE_NIGHT` | 15 | Transactions between 01:00–04:00 AM |
| `ROUND_AMOUNT` | 10 | ≥BDT 50,000 AND ≥5× sender's own median — eliminates false positives |
| `HIGH_VALUE` | 10 | Single txn above BDT 20,000 |

**Risk Score** = weighted sum (0–100) → `LOW` / `MEDIUM` / `HIGH` tiers

> **Key insight**: Global AML systems generate massive false positives on South Asian MFS data because round amounts (BDT 500, 1,000, 5,000) are culturally normal for rent, bazar, and remittance. This engine is calibrated to eliminate that noise. See [`RULE_CALIBRATION.md`](RULE_CALIBRATION.md) for the full rationale.

---

## Project Structure

```
synthetic-aml-detection/
│
├── generate_data.py        # Synthetic bKash-style MFS transaction generator
├── detect_anomalies.py     # Rule-based TME with composite risk scoring
├── visualize.py            # Compliance dashboard (6 visualizations)
├── requirements.txt        # Dependencies
├── USAGE_GUIDE.md          # Step-by-step guide for beginners
├── RULE_CALIBRATION.md     # BD-specific rule logic and thresholds explained
├── outputs/                # Generated CSV files (auto-created on first run)
└── images/                 # Dashboard screenshots
```

---

## Quick Start

```bash
git clone https://github.com/monsurhabib01/synthetic-aml-detection.git
cd synthetic-aml-detection
pip install -r requirements.txt

python generate_data.py      # Step 1: Generate 10,000+ synthetic transactions
python detect_anomalies.py   # Step 2: Run AML rule engine → scored_transactions.csv
python visualize.py          # Step 3: Render compliance dashboard
```

For a detailed walkthrough, see **[`USAGE_GUIDE.md`](USAGE_GUIDE.md)**.

---

## Output Files

After running all three scripts, the `outputs/` folder contains:

| File | Description |
|------|-------------|
| `raw_transactions.csv` | 10,000+ synthetic transactions with injected anomalies |
| `scored_transactions.csv` | All transactions with `risk_score`, `risk_tier`, and rule columns |
| `flagged_transactions.csv` | Filtered view: only transactions with `risk_score > 0` |

---

## What This Demonstrates (For Job Applications)

- **Domain knowledge**: BFIU regulatory framework, BDT thresholds, BD MFS behavioral norms
- **Data engineering**: Realistic synthetic data generation with injected anomaly patterns
- **Rule engine design**: Weighted composite scoring, rolling window logic, per-account profiling
- **False positive reduction**: Profile-relative thresholds instead of absolute cutoffs
- **Compliance output**: SAR-candidate identification, flagged transaction reports
- **Visualization**: Compliance dashboard with risk distribution, rule breakdown, and time-series analysis

---

## BD Domain Knowledge Applied

| Context | Detail |
|---------|--------|
| **BFIU threshold** | BDT 100,000 CTR threshold; STR required for suspicious patterns regardless of amount |
| **MFS behavioral norms** | Round amounts (500 / 1,000 / 5,000 / 10,000 BDT) are normal — not suspicious |
| **Cash-out dominance** | 38% of BD MFS transactions are withdrawals — modeled in transaction type weights |
| **Account numbering** | BD mobile number format: `01X-XXXXXXXX` used for account IDs |
| **Geographic distribution** | Division-weighted — Dhaka 45%, Chittagong 20%, others proportional |

See [`RULE_CALIBRATION.md`](RULE_CALIBRATION.md) for the full breakdown.

---

## Roadmap

- [x] Rule-based TME with 6 AML rules
- [x] Composite risk scoring (0–100)
- [x] Compliance visualization dashboard
- [ ] ML layer — supervised anomaly detection (IsolationForest + LightGBM)
- [ ] Multi-account smurfing / layering network detection
- [ ] Auto-generated SAR/CTR report (PDF format)
- [ ] REST API wrapper for real-time scoring

---

## Contact

**Monsur Habib** — AML Data Analyst | Dhaka, Bangladesh

- 🌐 [aitipseveryday.com](https://aitipseveryday.com)
- 💼 [Fiverr](https://www.fiverr.com/mdmonsurhabib)
- 📧 habibmonsur01@gmail.com

---

## License

MIT — free for educational and portfolio use.
