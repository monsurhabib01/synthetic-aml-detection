"""
Threshold Optimization & Backtesting Module
============================================
BFIU-aligned threshold analysis for Bangladesh MFS transaction monitoring.

10x improvements:
  1.  cost_optimize()           — fn_cost × FN + fp_cost × FP minimisation (real business decision)
  2.  find_threshold()          — constraint-based selector (min_recall AND min_precision)
  3.  bootstrap_ci()            — statistical confidence intervals (n_iterations default 300)
  4.  bfiu_compliance_check()   — detection rate per BDT amount band (STR/CTR/Large)
  5.  segment_analysis()        — per-segment P/R/F1 (tx_type / division / amount_band)
  6.  temporal_drift()          — performance over time windows (concept drift detection)
  7.  bfiu_workload()           — 3-tier analyst pipeline model (triage/investigate/SAR)
  8.  to_excel()                — compliance-grade Excel export (openpyxl)
  9.  summary()                 — single-call decision output with recommendation
  10. 6-panel plot              — cost curve + CI bands + BFIU band detection

Usage:
    bt = ThresholdBacktester(y_true, y_prob)
    bt.run()
    bt.bootstrap_ci()
    bt.bfiu_compliance_check(amounts=df['amount_bdt'])
    bt.cost_optimize(fn_cost=25, fp_cost=1)
    t = bt.find_threshold(min_recall=0.85, min_precision=0.60)
    bt.segment_analysis(df['tx_type'])
    bt.temporal_drift(df['timestamp'], threshold=t)
    bt.bfiu_workload(analyst_capacity_per_day=50, total_txns_per_day=50_000)
    bt.plot(save_path='images/threshold_analysis.png')
    bt.summary()
    bt.to_excel('outputs/threshold_report.xlsx')
"""

from __future__ import annotations

import os
import warnings
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    precision_recall_curve, average_precision_score,
)

warnings.filterwarnings('ignore')

# ── Plot theme ──────────────────────────────────────────────────────────────
plt.style.use('dark_background')
for _p in ['axes.facecolor', 'figure.facecolor', 'savefig.facecolor']:
    plt.rcParams[_p] = '#0a0d16'
plt.rcParams['axes.edgecolor'] = '#181e30'

ACCENT = '#00c2f0'
WARN   = '#f5a623'
DANGER = '#e05a5a'
GREEN  = '#22d46a'
PURPLE = '#b565f3'
GREY   = '#4a5568'


def _metrics(y_true: np.ndarray, preds: np.ndarray) -> tuple[float, float, float, float]:
    """Return (precision, recall, f1, fpr)."""
    tp = int(((preds == 1) & (y_true == 1)).sum())
    fp = int(((preds == 1) & (y_true == 0)).sum())
    fn = int(((preds == 0) & (y_true == 1)).sum())
    tn = int(((preds == 0) & (y_true == 0)).sum())
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    fpr  = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    return prec, rec, f1, fpr


# ────────────────────────────────────────────────────────────────────────────
class ThresholdBacktester:
    """
    Production-grade threshold analysis for AML/fraud ML models.

    BFIU regulatory context (Bangladesh):
      - STR threshold : BDT 500 K  — any suspicious transaction must be reported
      - CTR threshold : BDT 1 M    — all cash transactions above this are reported
      - Large txn     : BDT 5 M    — high-value alert, mandatory enhanced due diligence
      - Min recall    : 0.85       — internal benchmark to avoid regulatory exposure
      - FN cost ratio : ~25×       — each missed SAR ≈ 25× the cost of a false alert
    """

    # ── BFIU constants (BDT) ─────────────────────────────────────────────
    BFIU_STR_THRESHOLD   = 500_000
    BFIU_CTR_THRESHOLD   = 1_000_000
    BFIU_LARGE_THRESHOLD = 5_000_000
    BFIU_MIN_RECALL      = 0.85          # regulatory safety floor

    # ── 3-tier analyst pipeline (minutes per alert) ───────────────────────
    TRIAGE_MIN     = 5    # quick scan: is it real?
    INVEST_MIN     = 45   # full investigation
    SAR_FILING_MIN = 90   # SAR drafting + approval

    def __init__(self, y_true: np.ndarray, y_prob: np.ndarray):
        self.y_true  = np.asarray(y_true, dtype=int)
        self.y_prob  = np.asarray(y_prob, dtype=float)
        self.results:    pd.DataFrame = pd.DataFrame()
        self.ci_results: pd.DataFrame = pd.DataFrame()
        self._bfiu_band_results: Optional[pd.DataFrame] = None
        self._cost_result:       Optional[dict]          = None
        self._drift_result:      Optional[pd.DataFrame]  = None
        self.opt_f1:        Optional[float] = None
        self.opt_recall:    Optional[float] = None
        self.opt_precision: Optional[float] = None
        self.opt_cost:      Optional[float] = None

    # ────────────────────────────────────────────────────────────────────
    # 1. Core sweep
    # ────────────────────────────────────────────────────────────────────

    def run(self, thresholds: Optional[np.ndarray] = None) -> pd.DataFrame:
        """
        Sweep thresholds and compute P/R/F1/FPR/TP/FP/FN/TN at each point.
        Call this before any other method.
        """
        if thresholds is None:
            thresholds = np.round(np.arange(0.05, 0.96, 0.05), 2)

        rows = []
        for t in thresholds:
            preds = (self.y_prob >= t).astype(int)
            tp = int(((preds == 1) & (self.y_true == 1)).sum())
            fp = int(((preds == 1) & (self.y_true == 0)).sum())
            fn = int(((preds == 0) & (self.y_true == 1)).sum())
            tn = int(((preds == 0) & (self.y_true == 0)).sum())
            prec, rec, f1, fpr = _metrics(self.y_true, preds)
            rows.append({
                'threshold':     round(float(t), 3),
                'precision':     round(prec, 4),
                'recall':        round(rec,  4),
                'f1':            round(f1,   4),
                'fpr':           round(fpr,  4),
                'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
                'flagged_count': int(preds.sum()),
                'flagged_pct':   round(preds.mean() * 100, 2),
                'missed_sars':   fn,
            })

        self.results = pd.DataFrame(rows)
        self.opt_f1  = float(self.results.loc[self.results['f1'].idxmax(), 'threshold'])

        _hr = self.results[self.results['recall'] >= 0.90]
        self.opt_recall = float(_hr['threshold'].max()) if len(_hr) else None

        _hp = self.results[self.results['precision'] >= 0.80]
        self.opt_precision = float(_hp['threshold'].max()) if len(_hp) else None

        return self.results

    # ────────────────────────────────────────────────────────────────────
    # 2. Constraint-based threshold finder
    # ────────────────────────────────────────────────────────────────────

    def find_threshold(
        self,
        min_recall:    Optional[float] = None,
        min_precision: Optional[float] = None,
        min_f1:        Optional[float] = None,
        max_fpr:       Optional[float] = None,
    ) -> Optional[float]:
        """
        Return the HIGHEST threshold satisfying ALL constraints.
        Higher threshold = fewer alerts = lower analyst cost.

        Example — BFIU-safe, analyst-feasible:
            t = bt.find_threshold(min_recall=0.85, min_precision=0.60)
        """
        self._require_run()
        mask = pd.Series([True] * len(self.results))
        if min_recall    is not None: mask &= self.results['recall']    >= min_recall
        if min_precision is not None: mask &= self.results['precision'] >= min_precision
        if min_f1        is not None: mask &= self.results['f1']        >= min_f1
        if max_fpr       is not None: mask &= self.results['fpr']       <= max_fpr
        feasible = self.results[mask]
        if feasible.empty:
            print("⚠  No threshold satisfies all constraints. Relax one or more bounds.")
            return None
        t = float(feasible['threshold'].max())
        row = feasible.loc[feasible['threshold'] == t].iloc[0]
        print(f"✓ find_threshold result  : {t}")
        print(f"  Recall {row['recall']:.3f}  |  Precision {row['precision']:.3f}  "
              f"|  F1 {row['f1']:.3f}  |  Flagged {row['flagged_pct']:.1f}%")
        return t

    # ────────────────────────────────────────────────────────────────────
    # 3. Cost-sensitive optimisation
    # ────────────────────────────────────────────────────────────────────

    def cost_optimize(
        self,
        fn_cost: float = 25.0,
        fp_cost: float = 1.0,
    ) -> dict:
        """
        Find the threshold minimising expected total cost:
            total_cost = fn_cost × FN  +  fp_cost × FP

        AML cost intuition (BD MFS context):
          fn_cost : regulatory penalty + reputational risk. Ratio typically 10–50×.
          fp_cost : analyst hours. At BDT 500/hr, 45-min investigation ≈ BDT 375.
          Default fn_cost=25 implies each missed SAR costs ~25× a false alert.
        """
        self._require_run()
        df = self.results.copy()
        df['fn_component']    = fn_cost * df['fn']
        df['fp_component']    = fp_cost * df['fp']
        df['total_cost']      = df['fn_component'] + df['fp_component']
        df['cost_normalised'] = df['total_cost'] / df['total_cost'].max()

        opt_row       = df.iloc[df['total_cost'].idxmin()]
        self.opt_cost = float(opt_row['threshold'])

        default_row = df[df['threshold'] == 0.50]
        savings_pct = None
        if not default_row.empty:
            default_cost = float(default_row['total_cost'].iloc[0])
            savings_pct  = (default_cost - float(opt_row['total_cost'])) / default_cost * 100

        result = {
            'optimal_threshold':  self.opt_cost,
            'total_cost':         float(opt_row['total_cost']),
            'fn_component':       float(opt_row['fn_component']),
            'fp_component':       float(opt_row['fp_component']),
            'recall':             float(opt_row['recall']),
            'precision':          float(opt_row['precision']),
            'fn':                 int(opt_row['fn']),
            'fp':                 int(opt_row['fp']),
            'savings_vs_0_5_pct': round(savings_pct, 1) if savings_pct is not None else None,
            '_cost_df':           df[['threshold','total_cost','fn_component','fp_component']],
        }
        self._cost_result = result

        print(f"\n=== Cost-Optimised Threshold  (fn_cost={fn_cost}×, fp_cost={fp_cost}×) ===")
        print(f"  Optimal threshold  : {self.opt_cost}")
        print(f"  Total cost         : {opt_row['total_cost']:.0f} units")
        print(f"  ├─ FN component    : {opt_row['fn_component']:.0f}  ({int(opt_row['fn'])} missed SARs)")
        print(f"  └─ FP component    : {opt_row['fp_component']:.0f}  ({int(opt_row['fp'])} false alerts)")
        print(f"  Recall             : {opt_row['recall']:.3f}  |  Precision : {opt_row['precision']:.3f}")
        if savings_pct is not None:
            print(f"  Cost saving vs 0.5 : {savings_pct:.1f}%")
        return result

    # ────────────────────────────────────────────────────────────────────
    # 4. Bootstrap confidence intervals
    # ────────────────────────────────────────────────────────────────────

    def bootstrap_ci(
        self,
        thresholds:   Optional[list] = None,
        n_iterations: int   = 300,
        ci:           float = 0.95,
        random_state: int   = 42,
    ) -> pd.DataFrame:
        """
        Bootstrap confidence intervals for P/R/F1 at each threshold.

        A single test-set evaluation may over/understate true performance.
        Bootstrap gives the stability envelope — critical when justifying
        threshold choice to compliance teams or regulators.
        """
        if thresholds is None:
            thresholds = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50,
                          0.55, 0.60, 0.65, 0.70]

        rng   = np.random.default_rng(random_state)
        n     = len(self.y_true)
        alpha = (1 - ci) / 2
        records = []

        for t in thresholds:
            boot_p, boot_r, boot_f1 = [], [], []
            for _ in range(n_iterations):
                idx   = rng.integers(0, n, size=n)
                preds = (self.y_prob[idx] >= t).astype(int)
                p, r, f, _ = _metrics(self.y_true[idx], preds)
                boot_p.append(p); boot_r.append(r); boot_f1.append(f)
            records.append({
                'threshold': round(float(t), 3),
                'p_lo':   round(float(np.quantile(boot_p,  alpha)),     4),
                'p_med':  round(float(np.quantile(boot_p,  0.5)),       4),
                'p_hi':   round(float(np.quantile(boot_p,  1 - alpha)), 4),
                'r_lo':   round(float(np.quantile(boot_r,  alpha)),     4),
                'r_med':  round(float(np.quantile(boot_r,  0.5)),       4),
                'r_hi':   round(float(np.quantile(boot_r,  1 - alpha)), 4),
                'f1_lo':  round(float(np.quantile(boot_f1, alpha)),     4),
                'f1_med': round(float(np.quantile(boot_f1, 0.5)),       4),
                'f1_hi':  round(float(np.quantile(boot_f1, 1 - alpha)), 4),
            })

        self.ci_results = pd.DataFrame(records)
        print(f"✓ Bootstrap CI ({int(ci*100)}%, {n_iterations} iterations)")
        print(self.ci_results[['threshold','r_lo','r_med','r_hi','p_lo','p_med','p_hi']].to_string(index=False))
        return self.ci_results

    # ────────────────────────────────────────────────────────────────────
    # 5. BFIU amount-band compliance check
    # ────────────────────────────────────────────────────────────────────

    def bfiu_compliance_check(
        self,
        amounts:   pd.Series,
        threshold: Optional[float] = None,
    ) -> pd.DataFrame:
        """
        Detection rate broken down by BFIU-defined BDT amount bands.

        Answers the key regulatory question: for transactions that MUST be
        reported under BFIU rules (>= BDT 500K and suspicious), what fraction
        is our model actually catching?

        Bands:
          Below STR   : < BDT 500 K
          STR-eligible: BDT 500 K – 1 M   (must file STR if suspicious)
          CTR-eligible: BDT 1 M   – 5 M   (must file CTR if cash)
          Large (EDD) : >= BDT 5 M         (enhanced due diligence mandatory)
        """
        amounts = np.asarray(amounts, dtype=float)
        assert len(amounts) == len(self.y_true), "amounts must match y_true length"

        thresholds_to_check = (
            [threshold] if threshold is not None
            else [0.20, 0.30, 0.40, 0.50, 0.60]
        )
        band_defs = [
            ('Below STR',    amounts < self.BFIU_STR_THRESHOLD),
            ('STR-eligible', (amounts >= self.BFIU_STR_THRESHOLD) & (amounts < self.BFIU_CTR_THRESHOLD)),
            ('CTR-eligible', (amounts >= self.BFIU_CTR_THRESHOLD) & (amounts < self.BFIU_LARGE_THRESHOLD)),
            ('Large (EDD)',  amounts >= self.BFIU_LARGE_THRESHOLD),
        ]

        rows = []
        for t in thresholds_to_check:
            preds = (self.y_prob >= t).astype(int)
            for band_name, mask in band_defs:
                yt_band   = self.y_true[mask]
                yp_band   = preds[mask]
                n_true    = yt_band.sum()
                tp        = int(((yp_band == 1) & (yt_band == 1)).sum())
                fn        = int(((yp_band == 0) & (yt_band == 1)).sum())
                det_rate  = tp / n_true if n_true > 0 else np.nan
                rows.append({
                    'threshold':      round(float(t), 3),
                    'band':           band_name,
                    'n_transactions': int(mask.sum()),
                    'n_true_anomaly': int(n_true),
                    'n_flagged':      int(yp_band.sum()),
                    'tp':             tp,
                    'fn':             fn,
                    'detection_rate': round(det_rate, 4) if not np.isnan(det_rate) else None,
                    'bfiu_compliant': det_rate >= self.BFIU_MIN_RECALL if not np.isnan(det_rate) else None,
                })

        df = pd.DataFrame(rows)
        self._bfiu_band_results = df

        print("\n=== BFIU Amount-Band Compliance Check ===")
        print(df[['threshold','band','n_true_anomaly','detection_rate','bfiu_compliant']].to_string(index=False))

        non_compliant = df[
            (df['band'].isin(['STR-eligible','CTR-eligible','Large (EDD)'])) &
            (df['bfiu_compliant'] == False)
        ]
        if len(non_compliant):
            print(f"\n⚠  {len(non_compliant)} high-value band × threshold combos below {self.BFIU_MIN_RECALL} recall:")
            for _, row in non_compliant.iterrows():
                print(f"   threshold={row['threshold']}  band={row['band']}  "
                      f"detection_rate={row['detection_rate']}")
        return df

    # ────────────────────────────────────────────────────────────────────
    # 6. Per-segment analysis
    # ────────────────────────────────────────────────────────────────────

    def segment_analysis(
        self,
        segments:   pd.Series,
        thresholds: Optional[list] = None,
    ) -> pd.DataFrame:
        """
        Per-segment threshold performance.
        Pass any categorical Series: tx_type, division, amount_band, etc.

        Reveals which segments drive high FPR (e.g. MOBILE_RECHARGE flagged
        often but rarely suspicious) — enabling segment-specific thresholds.
        """
        segments = np.asarray(segments)
        assert len(segments) == len(self.y_true), "segments must match y_true length"

        thresholds  = thresholds or [0.30, 0.40, 0.50, 0.60]
        unique_segs = sorted(set(segments))
        rows = []

        for seg in unique_segs:
            mask  = segments == seg
            yt    = self.y_true[mask]
            yp    = self.y_prob[mask]
            n_seg = mask.sum()
            n_pos = int(yt.sum())
            for t in thresholds:
                preds = (yp >= t).astype(int)
                p, r, f, _ = _metrics(yt, preds)
                rows.append({
                    'segment':       seg,
                    'threshold':     round(float(t), 3),
                    'n':             int(n_seg),
                    'n_anomaly':     n_pos,
                    'anomaly_rate':  round(n_pos / n_seg * 100, 1) if n_seg else 0,
                    'precision':     round(p, 4),
                    'recall':        round(r, 4),
                    'f1':            round(f, 4),
                    'flagged_pct':   round(preds.mean() * 100, 2),
                    'flagged_count': int(preds.sum()),
                })

        df = pd.DataFrame(rows)
        print("\n=== Per-Segment Threshold Analysis ===")
        pivot = df.pivot_table(
            index='segment', columns='threshold',
            values='recall', aggfunc='first'
        ).round(3)
        pivot.columns = [f"recall@{c}" for c in pivot.columns]
        print(pivot.to_string())
        print("\n(Full DataFrame returned for further analysis)")
        return df

    # ────────────────────────────────────────────────────────────────────
    # 7. Temporal drift detection
    # ────────────────────────────────────────────────────────────────────

    def temporal_drift(
        self,
        timestamps: pd.Series,
        threshold:  float,
        n_windows:  int = 4,
    ) -> pd.DataFrame:
        """
        Evaluate performance across equal-width time windows.
        Detects concept drift — AML patterns evolve as launderers adapt.

        A >5pp recall drop between window 1 and the last window is a strong
        signal the model needs retraining on recent data.
        """
        timestamps = pd.to_datetime(timestamps)
        assert len(timestamps) == len(self.y_true)

        t_min, t_max = timestamps.min(), timestamps.max()
        window_td    = (t_max - t_min) / n_windows
        rows = []

        for i in range(n_windows):
            wstart = t_min + i * window_td
            wend   = t_min + (i + 1) * window_td
            mask   = (timestamps >= wstart) & (timestamps < wend)
            if i == n_windows - 1:
                mask = timestamps >= wstart

            yt = self.y_true[mask.values]
            yp = self.y_prob[mask.values]

            if len(yt) == 0 or yt.sum() == 0:
                rows.append({'window': i+1, 'start': wstart.date(), 'end': wend.date(),
                             'n': 0, 'n_anomaly': 0, 'precision': None,
                             'recall': None, 'f1': None, 'flagged_pct': None})
                continue

            preds = (yp >= threshold).astype(int)
            p, r, f, _ = _metrics(yt, preds)
            rows.append({
                'window':      i + 1,
                'start':       wstart.date(),
                'end':         wend.date(),
                'n':           int(mask.sum()),
                'n_anomaly':   int(yt.sum()),
                'precision':   round(p, 4),
                'recall':      round(r, 4),
                'f1':          round(f, 4),
                'flagged_pct': round(preds.mean() * 100, 2),
            })

        df = pd.DataFrame(rows)
        self._drift_result = df

        print(f"\n=== Temporal Drift  (threshold={threshold}) ===")
        print(df[['window','start','end','n','recall','precision','f1']].to_string(index=False))

        valid = df.dropna(subset=['recall'])
        if len(valid) >= 2:
            recall_drop = float(valid['recall'].iloc[0]) - float(valid['recall'].iloc[-1])
            if recall_drop > 0.05:
                print(f"\n⚠  Recall drop {recall_drop:.3f} (window 1→{n_windows}). Retrain recommended.")
            else:
                print(f"\n✓ Recall stable across time windows (Δ={recall_drop:+.3f}).")
        return df

    # ────────────────────────────────────────────────────────────────────
    # 8. BFIU 3-tier workload model
    # ────────────────────────────────────────────────────────────────────

    def bfiu_workload(
        self,
        analyst_capacity_per_day: int   = 50,
        total_txns_per_day:       int   = 10_000,
        sar_conversion_rate:      float = 0.15,
        analyst_daily_hours:      float = 7.5,
    ) -> pd.DataFrame:
        """
        3-tier BFIU analyst pipeline model.

        Tier 1 — Triage       : TRIAGE_MIN     min/alert (all flagged)
        Tier 2 — Investigation: INVEST_MIN     min/alert (sar_conversion_rate survive triage)
        Tier 3 — SAR Filing   : SAR_FILING_MIN min/SAR   (true positives only)

        Returns per-threshold FTE requirement and BFIU viability flag.
        """
        self._require_run()
        scale        = total_txns_per_day / len(self.y_true)
        mins_per_day = analyst_daily_hours * 60
        rows = []

        for _, row in self.results.iterrows():
            daily_alerts   = int(row['flagged_count'] * scale)
            investigations = int(daily_alerts * sar_conversion_rate)
            sars_filed     = int(row['tp'] * scale * sar_conversion_rate)
            total_mins     = (daily_alerts    * self.TRIAGE_MIN +
                              investigations  * self.INVEST_MIN +
                              sars_filed      * self.SAR_FILING_MIN)
            fte_needed  = total_mins / mins_per_day
            rows.append({
                'threshold':       row['threshold'],
                'recall':          row['recall'],
                'precision':       row['precision'],
                'daily_alerts':    daily_alerts,
                'daily_invest':    investigations,
                'daily_sars':      sars_filed,
                'daily_missed':    int(row['fn'] * scale),
                'fte_needed':      round(fte_needed, 1),
                'utilisation_pct': round(min(fte_needed / max(analyst_capacity_per_day,1)*100, 999.9), 1),
                'feasible':        fte_needed <= analyst_capacity_per_day,
                'bfiu_viable':     (fte_needed <= analyst_capacity_per_day and
                                    row['recall'] >= self.BFIU_MIN_RECALL),
            })

        df = pd.DataFrame(rows)
        print(f"\n=== BFIU 3-Tier Workload Model ===")
        print(f"Daily volume: {total_txns_per_day:,} | Analyst capacity: {analyst_capacity_per_day} FTE | "
              f"SAR conversion: {sar_conversion_rate*100:.0f}%\n")
        print(df[['threshold','recall','daily_alerts','daily_invest',
                  'daily_sars','daily_missed','fte_needed','bfiu_viable']].to_string(index=False))

        viable = df[df['bfiu_viable']]
        if len(viable):
            best = viable.iloc[0]
            print(f"\n✓ BFIU-Viable Threshold : {best['threshold']}")
            print(f"  Daily SARs: {int(best['daily_sars'])} | Missed: {int(best['daily_missed'])} | FTE: {best['fte_needed']}")
        else:
            print("\n⚠  No threshold meets recall≥0.85 AND analyst capacity.")
            print("   Options: (a) hire more analysts  (b) improve model precision  (c) pre-screening.")
        return df

    # ────────────────────────────────────────────────────────────────────
    # 9. 6-panel plot
    # ────────────────────────────────────────────────────────────────────

    def plot(self, save_path: Optional[str] = None, show_ci: bool = True):
        """
        6-panel threshold analysis:
          [0,0] P/R/F1 with bootstrap CI bands
          [0,1] Cost curve  (FN + FP + total)
          [1,0] TP/FP/FN stacked area
          [1,1] Flagged % workload zones
          [2,0] Precision-Recall curve with operating points
          [2,1] BFIU band detection heatmap / temporal drift
        """
        self._require_run()
        df  = self.results
        fig, axes = plt.subplots(3, 2, figsize=(15, 14))
        fig.suptitle(
            'Threshold Backtesting — AML Decision Boundary Analysis\n'
            'BD BFIU-Aligned Compliance Framework',
            color='white', fontsize=13, fontweight='bold', y=1.01
        )

        # [0,0] P/R/F1 + CI bands
        ax = axes[0, 0]
        ax.plot(df['threshold'], df['precision'], color=ACCENT, lw=2, label='Precision')
        ax.plot(df['threshold'], df['recall'],    color=GREEN,  lw=2, label='Recall')
        ax.plot(df['threshold'], df['f1'],        color=WARN,   lw=2, label='F1')
        if show_ci and not self.ci_results.empty:
            ci = self.ci_results
            ax.fill_between(ci['threshold'], ci['r_lo'],  ci['r_hi'],  alpha=0.18, color=GREEN)
            ax.fill_between(ci['threshold'], ci['p_lo'],  ci['p_hi'],  alpha=0.18, color=ACCENT)
            ax.fill_between(ci['threshold'], ci['f1_lo'], ci['f1_hi'], alpha=0.18, color=WARN)
        ax.axhline(self.BFIU_MIN_RECALL, color=DANGER, ls=':', lw=1.2,
                   label=f'BFIU min recall ({self.BFIU_MIN_RECALL})')
        if self.opt_f1:
            ax.axvline(self.opt_f1, color=WARN, ls='--', lw=1, alpha=0.5)
        ax.set_title('Precision / Recall / F1  (CI bands if bootstrap run)', color='white')
        ax.set_xlabel('Threshold'); ax.set_ylabel('Score')
        ax.set_ylim([0, 1.08]); ax.legend(fontsize=8)

        # [0,1] Cost curve
        ax = axes[0, 1]
        if self._cost_result and '_cost_df' in self._cost_result:
            cdf = self._cost_result['_cost_df']
            ax.plot(cdf['threshold'], cdf['total_cost'],   color=DANGER, lw=2,   label='Total cost')
            ax.plot(cdf['threshold'], cdf['fn_component'], color=WARN,   lw=1.5, ls='--', label='FN component')
            ax.plot(cdf['threshold'], cdf['fp_component'], color=ACCENT, lw=1.5, ls='--', label='FP component')
            if self.opt_cost:
                ax.axvline(self.opt_cost, color=GREEN, ls='--', lw=1.5, label=f'Optimal @ {self.opt_cost}')
            ax.set_title('Cost-Sensitive Analysis  (FN vs FP trade-off)', color='white')
            ax.set_ylabel('Total cost (arbitrary units)')
        else:
            ax.text(0.5, 0.5, 'Run .cost_optimize() to populate',
                    ha='center', va='center', color=GREY, transform=ax.transAxes)
            ax.set_title('Cost Curve  (not yet computed)', color='white')
        ax.set_xlabel('Threshold'); ax.legend(fontsize=8)

        # [1,0] TP/FP/FN stacked area
        ax = axes[1, 0]
        ax.stackplot(df['threshold'], df['tp'], df['fp'], df['fn'],
                     labels=['True Positive', 'False Positive', 'Missed SAR (FN)'],
                     colors=[GREEN, WARN, DANGER], alpha=0.85)
        ax.set_title('TP / FP / FN Breakdown', color='white')
        ax.set_xlabel('Threshold'); ax.set_ylabel('Count'); ax.legend(fontsize=8)

        # [1,1] Alert volume workload zones
        ax = axes[1, 1]
        colours = [GREEN if f < 10 else WARN if f < 30 else DANGER for f in df['flagged_pct']]
        ax.bar(df['threshold'], df['flagged_pct'], width=0.04, color=colours,
               edgecolor='#181e30', alpha=0.9)
        ax.axhline(5,  color=GREEN,  ls=':', lw=1, label='5%  low workload')
        ax.axhline(15, color=WARN,   ls=':', lw=1, label='15% medium')
        ax.axhline(30, color=DANGER, ls=':', lw=1, label='30% high')
        ax.set_title('Flagged Transactions %  (workload zones)', color='white')
        ax.set_xlabel('Threshold'); ax.set_ylabel('Flagged (%)'); ax.legend(fontsize=8)

        # [2,0] PR curve
        ax = axes[2, 0]
        prec_arr, rec_arr, _ = precision_recall_curve(self.y_true, self.y_prob)
        ap = average_precision_score(self.y_true, self.y_prob)
        ax.plot(rec_arr, prec_arr, color=PURPLE, lw=2, label=f'PR curve (AP={ap:.3f})')
        for label, (t, col) in [('F1 opt', (self.opt_f1, WARN)), ('Cost opt', (self.opt_cost, GREEN))]:
            if t is not None:
                r = self.results[np.isclose(self.results['threshold'], t, atol=0.01)]
                if len(r):
                    ax.scatter(r.iloc[0]['recall'], r.iloc[0]['precision'], color=col,
                               s=90, zorder=5, label=f'{label} @ {t}')
        ax.axhline(0.5, color=GREY, ls=':', lw=1)
        ax.set_title('Precision-Recall Curve', color='white')
        ax.set_xlabel('Recall'); ax.set_ylabel('Precision')
        ax.set_xlim([0, 1]); ax.set_ylim([0, 1.06]); ax.legend(fontsize=8)

        # [2,1] BFIU band heatmap OR temporal drift
        ax = axes[2, 1]
        if self._bfiu_band_results is not None:
            bdf   = self._bfiu_band_results
            pivot = bdf.pivot_table(index='band', columns='threshold',
                                    values='detection_rate', aggfunc='first')
            cmap  = plt.get_cmap('RdYlGn')
            im    = ax.imshow(pivot.values, cmap=cmap, aspect='auto', vmin=0, vmax=1)
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels([str(c) for c in pivot.columns], rotation=45, fontsize=8)
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels(pivot.index, fontsize=8)
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    val = pivot.values[i, j]
                    if not np.isnan(val):
                        ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                                fontsize=7.5, color='black' if val > 0.5 else 'white')
            plt.colorbar(im, ax=ax, fraction=0.046)
            ax.set_title('BFIU Band Detection Rate  (green=compliant)', color='white')
        elif self._drift_result is not None:
            ddf = self._drift_result.dropna(subset=['recall'])
            ax.plot(ddf['window'], ddf['recall'],    color=GREEN,  marker='o', lw=2, label='Recall')
            ax.plot(ddf['window'], ddf['precision'], color=ACCENT, marker='s', lw=2, label='Precision')
            ax.plot(ddf['window'], ddf['f1'],        color=WARN,   marker='^', lw=2, label='F1')
            ax.axhline(self.BFIU_MIN_RECALL, color=DANGER, ls=':', lw=1.2, label='BFIU floor')
            ax.set_title('Temporal Drift  (performance over time)', color='white')
            ax.set_xlabel('Time Window'); ax.set_ylabel('Score'); ax.legend(fontsize=8)
        else:
            ax.text(0.5, 0.5, 'Run .bfiu_compliance_check(amounts)\nor .temporal_drift(timestamps, t)',
                    ha='center', va='center', color=GREY, transform=ax.transAxes, fontsize=10)
            ax.set_title('BFIU Band Detection  (not yet computed)', color='white')

        plt.tight_layout()
        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
            plt.savefig(save_path, dpi=120, bbox_inches='tight')
            print(f"✓ Saved → {save_path}")
        plt.show()

    # ────────────────────────────────────────────────────────────────────
    # 10. Summary + report + Excel export
    # ────────────────────────────────────────────────────────────────────

    def summary(self):
        """Single-screen decision summary with actionable recommendation."""
        self._require_run()
        print("=" * 68)
        print("  AML THRESHOLD DECISION SUMMARY")
        print(f"  Dataset: {len(self.y_true):,} transactions | "
              f"{self.y_true.sum():,} anomalies ({self.y_true.mean()*100:.1f}%)")
        print("=" * 68)
        rows_data = []
        for label, t in [('Best F1', self.opt_f1), ('Recall ≥ 0.90', self.opt_recall),
                         ('Precision ≥ 0.80', self.opt_precision), ('Cost-optimised', self.opt_cost)]:
            if t is None:
                rows_data.append({'Mode': label, 'Threshold': '-', 'Recall': '-',
                                  'Precision': '-', 'F1': '-', 'Flagged%': '-'})
                continue
            row = self.results[np.isclose(self.results['threshold'], t, atol=0.01)]
            if len(row):
                row = row.iloc[0]
                rows_data.append({
                    'Mode': label, 'Threshold': t,
                    'Recall': f"{row['recall']:.3f}", 'Precision': f"{row['precision']:.3f}",
                    'F1': f"{row['f1']:.3f}", 'Flagged%': f"{row['flagged_pct']:.1f}%",
                })
        print(pd.DataFrame(rows_data).to_string(index=False))
        print("\n  RECOMMENDATION")
        t_rec = self.find_threshold(min_recall=self.BFIU_MIN_RECALL, min_precision=0.50)
        if t_rec:
            row = self.results[np.isclose(self.results['threshold'], t_rec, atol=0.01)].iloc[0]
            print(f"  → Use threshold {t_rec}  (recall={row['recall']:.3f}, "
                  f"precision={row['precision']:.3f}, flagged={row['flagged_pct']:.1f}%)")
            print(f"    Satisfies BFIU min recall ({self.BFIU_MIN_RECALL}) while maximising precision.")
        else:
            print(f"  → Model needs improvement — cannot meet recall≥{self.BFIU_MIN_RECALL} + precision≥0.50.")
        print("=" * 68)

    def report(self) -> str:
        """Compact text report (backward-compatible)."""
        self._require_run()
        lines = [
            "=" * 60, "   AML THRESHOLD BACKTESTING REPORT",
            "   BD BFIU-Aligned Compliance Analysis", "=" * 60,
            f"\nDataset : {len(self.y_true):,} transactions | "
            f"{self.y_true.sum():,} anomalies ({self.y_true.mean()*100:.1f}%)",
            "\n--- OPTIMAL OPERATING POINTS ---",
            f"  Best F1           : {self.opt_f1}",
            f"  Recall >= 0.90    : {self.opt_recall}",
            f"  Precision >= 0.80 : {self.opt_precision}",
            f"  Cost-optimised    : {self.opt_cost}",
            "\n--- BFIU GUIDANCE ---",
            f"  STR trigger : BDT {self.BFIU_STR_THRESHOLD:,}",
            f"  CTR trigger : BDT {self.BFIU_CTR_THRESHOLD:,}",
            f"  Min recall  : {self.BFIU_MIN_RECALL}",
            "  Regulatory compliance → recall-optimised threshold",
            "  Cost-constrained     → cost-optimised threshold",
            "\n--- KEY THRESHOLD TABLE ---",
        ]
        key = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70]
        subset = self.results[self.results['threshold'].isin(key)]
        lines.append(subset[['threshold','precision','recall','f1','flagged_pct','missed_sars']].to_string(index=False))
        lines.append("=" * 60)
        return "\n".join(lines)

    def to_excel(self, path: str = 'outputs/threshold_report.xlsx'):
        """
        Export compliance-grade Excel report:
          Sheet 1 — Summary      (optimal thresholds + recommendation)
          Sheet 2 — Full Sweep   (all thresholds with metrics)
          Sheet 3 — BFIU Bands   (amount-band detection rates)
          Sheet 4 — Bootstrap CI (confidence intervals)
        """
        try:
            import openpyxl
        except ImportError:
            print("openpyxl not installed. Run: pip install openpyxl")
            return
        self._require_run()
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            self.results.to_excel(writer, sheet_name='Full Sweep', index=False)
            if self._bfiu_band_results is not None:
                self._bfiu_band_results.to_excel(writer, sheet_name='BFIU Bands', index=False)
            if not self.ci_results.empty:
                self.ci_results.to_excel(writer, sheet_name='Bootstrap CI', index=False)
            pd.DataFrame({
                'Mode':      ['Best F1', 'Recall >= 0.90', 'Precision >= 0.80', 'Cost-optimised'],
                'Threshold': [self.opt_f1, self.opt_recall, self.opt_precision, self.opt_cost],
            }).to_excel(writer, sheet_name='Summary', index=False)
        print(f"✓ Excel report saved → {path}")

    # ────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ────────────────────────────────────────────────────────────────────

    def _require_run(self):
        if self.results.empty:
            raise RuntimeError("Call .run() first.")


# ────────────────────────────────────────────────────────────────────────────
# CLI demo
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== ThresholdBacktester — Demo Mode ===\n")

    data_path = os.path.join(os.path.dirname(__file__), 'outputs', 'scored_transactions.csv')
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, parse_dates=['timestamp'])
        required = {'ml_score', 'is_anomaly', 'amount_bdt', 'tx_type', 'timestamp'}
        if required.issubset(df.columns):
            y_true     = df['is_anomaly'].values
            y_prob     = df['ml_score'].values
            amounts    = df['amount_bdt']
            segments   = df['tx_type']
            timestamps = df['timestamp']
            print(f"Loaded {len(df):,} rows from {data_path}")
        else:
            df = None
    else:
        df = None

    if df is None:
        print("outputs/scored_transactions.csv not found — running synthetic demo...")
        rng  = np.random.default_rng(42)
        n    = 8_000
        y_true = rng.binomial(1, 0.07, n)
        y_prob = np.where(y_true == 1, rng.beta(5, 2, n), rng.beta(2, 9, n))
        amounts    = pd.Series(np.where(y_true==1, rng.lognormal(14,1.5,n), rng.lognormal(11,1.2,n)))
        segments   = pd.Series(rng.choice(['P2P','B2P','CASH_IN','CASH_OUT','REMITTANCE'],
                                          n, p=[0.45,0.25,0.15,0.10,0.05]))
        timestamps = pd.Series(pd.date_range('2024-01-01', periods=n, freq='1h'))

    bt = ThresholdBacktester(y_true, y_prob)
    bt.run()
    bt.bootstrap_ci(n_iterations=200)
    bt.cost_optimize(fn_cost=25, fp_cost=1)
    bt.bfiu_compliance_check(amounts)
    bt.segment_analysis(segments)
    bt.temporal_drift(timestamps, threshold=0.35)
    bt.bfiu_workload(analyst_capacity_per_day=50, total_txns_per_day=50_000)
    bt.summary()
    print(bt.report())
    bt.plot(save_path='images/threshold_analysis.png')
    bt.to_excel('outputs/threshold_report.xlsx')
