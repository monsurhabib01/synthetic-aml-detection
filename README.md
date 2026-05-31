# Bangladesh MFS AML Detection System

**Rule-Based Transaction Monitoring Engine for bKash/Nagad | BFIU-Calibrated**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## 🎯 Project Overview

A production-grade rule-based Transaction Monitoring Engine (TME) built specifically for Bangladesh's Mobile Financial Services (MFS) ecosystem. Behavioral patterns are calibrated to bKash, Nagad, and Rocket transaction flows under BFIU (Bangladesh Financial Intelligence Unit) guidelines.

**The problem it solves**: Global AML systems generate massive false positives on BD MFS data — flagging normal BDT 500/1000/5000 round-amount transactions as suspicious. This engine is calibrated to BD-specific norms.

---

## 🔍 AML Rules Engine

| Rule | Weight | Logic |
|------|--------|-------|
| STRUCTURING | 35 | ≥3 txns in 24h all between 80–100% of BDT 10,000 threshold |
| DORMANT_SPIKE | 30 | Account inactive 30+ days suddenly transacts above BDT 10,000 |
| VELOCITY | 25 | ≥5 txns within any 60-minute rolling window |
| LATE_NIGHT | 15 | Transactions between 01:00–04:00 AM |
| ROUND_AMOUNT | 10 | ≥BDT 50,000 AND ≥5× sender's own median (eliminates false positives) |
| HIGH_VALUE | 10 | Single txn above BDT 20,000 |

**Risk Score** = weighted sum of rule hits (0–100)
- `0–29` → LOW risk
- `30–59` → MEDIUM risk (review queue)
- `60–100` → HIGH risk (SAR candidate)

---

## 📁 Repository Structure

```
synthetic-aml-detection/
│
├── generate_data.py        # Synthetic bKash-style MFS transaction generator
├── detect_anomalies.py     # Rule-based TME with composite risk scoring
├── visualize.py            # Compliance dashboard (6 visualizations)
├── requirements.txt        # Dependencies
├── images/                 # Dashboard screenshots
└── README.md
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/monsurhabib01/synthetic-aml-detection.git
cd synthetic-aml-detection
pip install -r requirements.txt

# Step 1: Generate synthetic transaction data
python generate_data.py

# Step 2: Run the AML rule engine
python detect_anomalies.py

# Step 3: View compliance dashboard
python visualize.py
```

Output saved to `outputs/`:
- `raw_transactions.csv` — generated data (~10,000 rows)
- `flagged_transactions.csv` — HIGH/MEDIUM risk transactions
- `scored_transactions.csv` — full dataset with risk scores

---

## 📊 Synthetic Data — Anomaly Types

| Anomaly | Count | Description |
|---------|-------|-------------|
| STRUCTURING | ~150 | Multiple txns just below BDT 10,000 threshold in clusters |
| VELOCITY | ~80 | 6–12 txns within 60 minutes from same account |
| LATE_NIGHT | ~120 | Txns between 01:00–04:00 AM |
| ROUND_AMOUNT | ~100 | BDT 50K/100K/200K/500K transfers |
| DORMANT_SPIKE | ~50 | Dormant account reactivation with high-value txn |
| NORMAL | ~9,500 | Realistic BD MFS transactions |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Data Processing | Python 3.8+, Pandas, NumPy |
| Rule Engine | Custom weighted composite scoring |
| Visualization | Matplotlib, Seaborn |
| Data Format | CSV (extensible to SQL/NoSQL) |

---

## 🎓 BD Domain Knowledge Applied

- **BFIU regulatory framework**: BDT 100K CTR threshold, STR requirements
- **BD MFS behavioral norms**: 60%+ round-amount transactions are culturally normal (rent, bazar, remittance)
- **cash_out dominance**: 38% of BD MFS transactions are withdrawals
- **False positive reduction**: Round Amount rule only fires at ≥BDT 50K AND ≥5× user median

---

## 🔮 Roadmap

- [ ] ML layer — supervised anomaly detection with labeled data
- [ ] Real-time API integration
- [ ] Multi-account smurfing/layering detection
- [ ] Auto-generated CTR/STR report format
- [ ] Network graph analysis for layering patterns

---

## 📧 Contact

**Monsur Habib** — AML Data Analyst | Dhaka, Bangladesh
- 🌐 [aitipseveryday.com](https://aitipseveryday.com)
- 💼 [fiverr.com/mdmonsurhabib](https://www.fiverr.com/mdmonsurhabib)
- 📧 habibmonsur01@gmail.com

---

## 📄 License

MIT — see [LICENSE](LICENSE)
