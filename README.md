# Python AML & Fraud Detection Toolkit

**Production-Style Transaction Monitoring | bKash/Nagad MFS | BFIU-Calibrated Rules | LightGBM ML**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![LightGBM](https://img.shields.io/badge/LightGBM-ML%20Layer-009900?style=flat-square)](https://lightgbm.readthedocs.io)
[![Jupyter](https://img.shields.io/badge/Jupyter-3%20Notebooks-F37626?style=flat-square&logo=jupyter&logoColor=white)](notebooks/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Gumroad](https://img.shields.io/badge/Gumroad-Get%20Full%20Toolkit-FF90E8?style=flat-square)](https://monsurhabib.gumroad.com)

> **A complete fraud detection portfolio project** — synthetic MFS data generation, BFIU-calibrated rule engine, LightGBM ML classifier, and SAR candidate export. Built with real-world AML patterns used in fintech and banking compliance teams.

---

## 🗺️ Pipeline Overview

```
Synthetic bKash-Style Data (10,000+ txns)
              ↓
  Rule Engine — 6 BFIU-Calibrated Rules
  (STRUCTURING · VELOCITY · DORMANT_SPIKE · LATE_NIGHT · ROUND_AMOUNT · HIGH_VALUE)
              ↓
  Composite Risk Score (0–100) → LOW / MEDIUM / HIGH
              ↓
  LightGBM ML Layer — reduces false positives, improves precision
              ↓
  SAR Candidates Export (.csv) — prioritised alert queue
```

---

## 📓 Jupyter Notebooks

Three step-by-step notebooks — run them in order from the repo root.

| # | Notebook | Covers | Runtime |
|---|---|---|---|
| 01 | [`01_data_generation.ipynb`](notebooks/01_data_generation.ipynb) | Synthetic BD MFS data + full EDA + temporal analysis | ~30s |
| 02 | [`02_rule_engine.ipynb`](notebooks/02_rule_engine.ipynb) | BFIU rule engine + risk scoring + precision/recall per rule | ~2 min |
| 03 | [`03_ml_detection.ipynb`](notebooks/03_ml_detection.ipynb) | LightGBM + feature engineering + ROC/PR curves + SAR export | ~1 min |

---

## 🎯 Who This Is For

- 🎓 **Data science job seekers** building a fintech portfolio that shows real AML domain knowledge
- 💼 **AML/compliance analysts** learning to apply Python to transaction monitoring workflows
- 🏗️ **Fintech developers** who need a working proof-of-concept AML rule engine
- 📋 **ACAMS/ICA exam preppers** wanting hands-on exposure to real TME logic

---

## ⚙️ AML Rule Engine (6 Rules)

| Rule | Weight | What It Detects |
|------|--------|-----------------|
| `STRUCTURING` | 35 | ≥3 txns in 24h all between 80–100% of BDT 10,000 threshold (smurfing) |
| `DORMANT_SPIKE` | 30 | Account inactive 30+ days → sudden high-value transaction (EDD trigger) |
| `VELOCITY` | 25 | ≥5 txns within any 60-minute window (layering / account takeover) |
| `LATE_NIGHT` | 15 | Transactions between 01:00–04:00 AM |
| `ROUND_AMOUNT` | 10 | ≥BDT 50,000 AND ≥5× sender's own median — eliminates BD MFS false positives |
| `HIGH_VALUE` | 10 | Single txn above BDT 20,000 |

**Risk Score** = weighted sum (0–100) → `LOW` / `MEDIUM` / `HIGH` tiers

> **Key design decision:** Global AML tools generate massive false positives on South Asian MFS data because round amounts (BDT 500, 1,000, 5,000) are culturally normal. This engine is calibrated to eliminate that noise. See [`RULE_CALIBRATION.md`](RULE_CALIBRATION.md) for full rationale.

---

## 🚀 Quick Start

```bash
git clone https://github.com/monsurhabib01/synthetic-aml-detection.git
cd synthetic-aml-detection
pip install -r requirements.txt

# Option A: Run Python scripts
python generate_data.py      # Step 1: Generate 10,000+ synthetic transactions
python detect_anomalies.py   # Step 2: Rule engine → scored_transactions.csv
python visualize.py          # Step 3: Compliance dashboard (6 charts)

# Option B: Run Jupyter notebooks (recommended)
jupyter notebook
# Open notebooks/ and run 01 → 02 → 03
```

---

## 📁 Project Structure

```
synthetic-aml-detection/
├── notebooks/
│   ├── 01_data_generation.ipynb    ← EDA + BD MFS context
│   ├── 02_rule_engine.ipynb        ← BFIU rules + scoring
│   └── 03_ml_detection.ipynb       ← LightGBM + SAR export
├── generate_data.py                ← Synthetic bKash transaction generator
├── detect_anomalies.py             ← Rule-based TME + risk scoring
├── visualize.py                    ← Compliance dashboard
├── requirements.txt
├── USAGE_GUIDE.md                  ← Beginner-friendly walkthrough
├── RULE_CALIBRATION.md             ← BFIU rule rationale + threshold logic
└── outputs/                        ← Auto-created: CSVs + charts
```

---

## 📊 Output Files

| File | Description |
|------|-------------|
| `outputs/raw_transactions.csv` | 10,000+ synthetic BD MFS transactions |
| `outputs/scored_transactions.csv` | All transactions + rule flags + risk_score + risk_tier |
| `outputs/flagged_transactions.csv` | Alert queue — risk_score > 0 |
| `outputs/sar_candidates.csv` | HIGH-tier + ML high-score SAR candidates |

---

## 🇧🇩 BD Domain Knowledge Applied

| Context | Detail |
|---------|--------|
| **BFIU threshold** | BDT 10,000 Suspicious Transaction Report threshold (Circular No. 5, 2019) |
| **MFS behavioral norms** | Round amounts (500–10,000 BDT) are normal — rent, bazar, remittance |
| **Cash-out dominance** | 38% of BD MFS transactions are withdrawals — modeled in tx type weights |
| **Account numbering** | BD mobile format `01X-XXXXXXXX` used as account IDs |
| **Geographic distribution** | 8 divisions — Dhaka 45%, Chittagong 20%, others proportional to population |

---

## 🧑‍💻 What This Demonstrates (For Job Applications)

- **Domain knowledge** — BFIU regulatory framework, BDT thresholds, BD MFS behavioral norms
- **Data engineering** — Synthetic data generation with controlled anomaly injection
- **Rule engine design** — Weighted composite scoring, rolling window logic, per-account profiling
- **ML on imbalanced data** — LightGBM with `scale_pos_weight`, threshold tuning, PR-AUC evaluation
- **False positive reduction** — Profile-relative thresholds vs absolute cutoffs
- **Compliance output** — SAR-candidate identification in production-compatible format

---

## 🛠️ Tech Stack

Python 3.9+ · Pandas · NumPy · Scikit-learn · LightGBM · Matplotlib · Seaborn · Jupyter

---

## 📋 Roadmap

- [x] Rule-based TME with 6 BFIU-calibrated AML rules
- [x] Composite risk scoring (0–100) with LOW / MEDIUM / HIGH tiers
- [x] 3 Jupyter notebooks (data → rules → ML)
- [x] LightGBM ML layer with feature engineering + SAR export
- [ ] Multi-account smurfing / layering network graph
- [ ] Auto-generated SAR/CTR PDF report
- [ ] REST API wrapper for real-time scoring

---

## Contact

**Monsur Habib** — AML Data Analyst · Dhaka, Bangladesh

🌐 [aitipseveryday.com](https://aitipseveryday.com) · 💼 [Fiverr](https://www.fiverr.com/mdmonsurhabib) · 📧 habibmonsur01@gmail.com

---

## License

MIT — free for educational and portfolio use.
