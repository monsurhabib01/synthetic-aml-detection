# Bangladesh MFS AML Detection System

**Rule-Based Transaction Monitoring Engine for bKash/Nagad | BFIU-Calibrated**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## 🎯 Project Overview

A production-grade rule-based Transaction Monitoring Engine (TME) built specifically for Bangladesh's Mobile Financial Services (MFS) ecosystem. Calibrated to bKash, Nagad, and Rocket transaction flows under BFIU (Bangladesh Financial Intelligence Unit) guidelines.

**Problem it solves**: Global AML systems generate massive false positives on BD MFS data — flagging normal BDT 500/1000/5000 round-amount transactions as suspicious. This engine is calibrated to BD-specific norms.

---

## 🔍 AML Rules Engine (6 Rules)

| Rule | Weight | Logic |
|------|--------|-------|
| STRUCTURING | 35 | ≥3 txns in 24h all between 80–100% of BDT 10,000 threshold |
| DORMANT_SPIKE | 30 | Account inactive 30+ days → high-value txn above BDT 10,000 |
| VELOCITY | 25 | ≥5 txns within any 60-minute rolling window |
| LATE_NIGHT | 15 | Transactions between 01:00–04:00 AM |
| ROUND_AMOUNT | 10 | ≥BDT 50,000 AND ≥5× sender's own median (eliminates false positives) |
| HIGH_VALUE | 10 | Single txn above BDT 20,000 |

**Risk Score** = weighted sum (0–100) → LOW / MEDIUM / HIGH tiers

---

## 📁 Repository Structure

```
synthetic-aml-detection/
│
├── generate_data.py        # Synthetic bKash-style MFS transaction generator
├── detect_anomalies.py     # Rule-based TME with composite risk scoring
├── visualize.py            # Compliance dashboard (6 visualizations)
├── requirements.txt
├── data/                   # Generated CSV outputs
├── images/                 # Dashboard screenshots
└── README.md
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/monsurhabib01/synthetic-aml-detection.git
cd synthetic-aml-detection
pip install -r requirements.txt

python generate_data.py      # Generate synthetic transactions
python detect_anomalies.py   # Run AML rule engine
python visualize.py          # View compliance dashboard
```

---

## 🎓 BD Domain Knowledge Applied

- **BFIU regulatory framework**: BDT 100K CTR threshold, STR requirements
- **BD MFS behavioral norms**: Round amounts (BDT 500/1000/5000) are culturally normal — not suspicious
- **cash_out dominance**: 38% of BD MFS transactions are withdrawals
- **False positive reduction**: ROUND_AMOUNT rule fires only at ≥BDT 50K AND ≥5× user median

---

## 🔮 Roadmap

- [ ] ML layer — supervised anomaly detection
- [ ] Multi-account smurfing/layering detection
- [ ] Auto-generated CTR/STR report format
- [ ] Real-time API integration

---

## 📧 Contact

**Monsur Habib** — AML Data Analyst | Dhaka, Bangladesh

- 🌐 [aitipseveryday.com](https://aitipseveryday.com)
- 💼 [fiverr.com/mdmonsurhabib](https://www.fiverr.com/mdmonsurhabib)
- 📧 habibmonsur01@gmail.com

---

## 📄 License

MIT License — free for educational and portfolio use.
