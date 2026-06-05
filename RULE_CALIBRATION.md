# Rule Calibration — BD-Specific AML Logic

This document explains why each rule threshold is set the way it is, based on Bangladesh Financial Intelligence Unit (BFIU) guidelines and real-world Mobile Financial Services (MFS) behavioral patterns.

---

## Why BD-Specific Calibration Matters

Most publicly available fraud detection datasets (PaySim, Kaggle financial crime datasets) model Western or generic transaction behavior. Applying them directly to South Asian MFS data produces extremely high false positive rates because:

- **Round amounts are normal in BD**: rent (BDT 5,000–15,000), bazar money (BDT 500–2,000), rickshaw/CNG fares, and utility bills are almost always round figures in Bangladesh
- **High cash-out volume is normal**: 38% of BD MFS transactions are cash withdrawals — this would look suspicious in a Western card-payment context
- **Low per-transaction limits**: bKash daily limit is BDT 25,000 — structuring thresholds must be calibrated accordingly
- **Mobile number as account ID**: BD mobile format `01X-XXXXXXXX` (11 digits, starts with 013/014/015/016/017/018/019)

---

## Rule-by-Rule Rationale

### STRUCTURING (weight: 35)

```python
rule_structuring(df, threshold=10_000, window_hours=24, min_txns=3)
```

**BFIU context**: Bangladesh Bank's guidelines require Suspicious Transaction Reports (STRs) for activity designed to evade the BDT 100,000 Cash Transaction Report (CTR) threshold. The BDT 10,000 threshold used here models the lower reporting limit applied by most MFS platforms internally.

**Logic**: ≥3 transactions within 24 hours, all between BDT 8,000–9,999 (80–100% of threshold). This pattern — known as smurfing — is the most common structuring method in BD MFS.

**Why weight 35**: Structuring is an intentional act (mens rea present). It is the single most reliable indicator of money laundering in MFS data.

---

### DORMANT_SPIKE (weight: 30)

```python
rule_dormant_spike(df, inactive_days=30, spike_threshold=10_000)
```

**Context**: Account dormancy followed by sudden activity is a well-documented layering technique — accounts are "seasoned" (opened, left idle to build history) then activated for illicit transfers.

**Logic**: No outbound activity for ≥30 days, followed by a transaction above BDT 10,000.

**BD-specific**: 30-day window matches Bangladesh Bank's account activity review cycle for MFS agents.

---

### VELOCITY (weight: 25)

```python
rule_velocity(df, window_minutes=60, min_txns=5)
```

**Context**: ≥5 transactions from a single account within 60 minutes suggests either automated transaction layering or account takeover (fraudster rapidly moving funds before the account is frozen).

**BD-specific**: Normal bKash users rarely initiate more than 2–3 transactions per hour. The 5-transaction threshold gives enough headroom for legitimate power users (agents, small merchants).

---

### LATE_NIGHT (weight: 15)

```python
rule_late_night(df, start_hour=1, end_hour=4)
```

**Context**: Transactions between 01:00–04:00 AM are outside normal behavioral patterns for retail MFS users. This window (not midnight, not early morning) captures the period with highest signal-to-noise ratio for suspicious activity.

**Weight 15**: This is a supporting signal, not a standalone indicator. It boosts the composite score when combined with other rules (e.g., STRUCTURING + LATE_NIGHT = high confidence).

---

### ROUND_AMOUNT (weight: 10)

```python
rule_round_amount(df, min_amount=50_000, profile_multiplier=5)
```

**Critical BD calibration point**: This rule intentionally ignores BDT 500, 1,000, 2,000, 5,000, 10,000, 15,000, 20,000 round amounts — all of which are extremely common in BD MFS for legitimate purposes.

**The rule fires ONLY when both conditions are true:**
1. Amount is a multiple of BDT 10,000 AND ≥ BDT 50,000 (above daily casual use)
2. Amount is ≥ 5× the sender's own historical median transaction amount (profile outlier)

**Why profile-relative**: A person who regularly sends BDT 40,000 transactions sending BDT 50,000 is not suspicious. But a person whose median is BDT 1,000 sending BDT 50,000 is an extreme outlier.

**Weight 10**: This is a booster rule — rarely standalone suspicious, but increases confidence when combined with structuring or velocity hits.

---

### HIGH_VALUE (weight: 10)

```python
rule_high_value(df, threshold=20_000)
```

**Context**: BDT 20,000 is near the bKash single-transaction limit. High-value transactions warrant review but are not inherently suspicious — remittances, business payments, and emergency transfers all legitimately reach this level.

**Weight 10**: Weakest rule. Primarily useful as a volume signal and for feeding the composite risk score.

---

## Risk Tier Calibration

| Tier | Score Range | Recommended Action |
|------|-------------|--------------------|
| LOW | 0–29 | No action required |
| MEDIUM | 30–59 | Analyst review queue |
| HIGH | 60–100 | SAR candidate — escalate |

The 60-point HIGH threshold is deliberately conservative — it requires either a STRUCTURING hit (35) + any secondary signal, or a DORMANT_SPIKE (30) + VELOCITY (25), or similar combinations. A single LOW-weight rule alone (LATE_NIGHT=15, HIGH_VALUE=10) cannot produce a HIGH-tier score without corroborating evidence.

This mirrors the "multi-rule corroboration" requirement in real compliance systems to reduce alert fatigue.

---

## BFIU Regulatory Reference

| Regulation | Threshold | Notes |
|------------|-----------|-------|
| Cash Transaction Report (CTR) | BDT 100,000 | Single transaction or aggregate within a day |
| Suspicious Transaction Report (STR) | No threshold | Behavior-based, no minimum amount |
| bKash daily transaction limit | BDT 25,000 (send) | Varies by account tier |
| Nagad daily limit | BDT 30,000 | Personal account |

---

## Further Reading

- [BFIU Guidelines for Reporting Entities](https://www.bfiu.gov.bd)
- [Bangladesh Bank BRPD Circular on MFS](https://www.bb.org.bd)
- FATF Guidance on Risk-Based Approach for Money Services Businesses
