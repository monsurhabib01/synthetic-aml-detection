# Notebooks

Three Jupyter notebooks — run them **in order** from the repo root.

| # | Notebook | Covers | Runtime |
|---|---|---|---|
| 01 | `01_data_generation.ipynb` | Synthetic BD MFS data generation + full EDA | ~30s |
| 02 | `02_rule_engine.ipynb` | BFIU rule engine + risk scoring + precision/recall | ~2 min |
| 03 | `03_ml_detection.ipynb` | LightGBM + feature engineering + SAR export | ~1 min |

## Quick Start

```bash
# From repo root
pip install -r requirements.txt
jupyter notebook
# Navigate to notebooks/ and run 01 → 02 → 03
```

## Outputs

```
outputs/
├── raw_transactions.csv       ← from notebook 01
├── scored_transactions.csv    ← from notebook 02
├── flagged_transactions.csv   ← from notebook 02
└── sar_candidates.csv         ← from notebook 03
```
