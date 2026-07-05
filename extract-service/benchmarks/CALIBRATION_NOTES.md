# Confidence Calibration Log

Tracks calibration_report() output over time as the benchmark set grows.
Goal: claimed confidence should roughly match actual field-level accuracy per tier.

## Run 1 — [date of this session], n=3 ground-truth cases (synthetic/hand-picked)
- json_ld:   claimed=0.90  actual=1.00  gap=-0.10  (n=2)
- fallback:  claimed=0.40  actual=1.00  gap=-0.60  (n=4)

**Action taken:** raised fallback confidence ceiling from 0.4 to 0.6 (partial
correction, not full match to observed 1.0 - sample is small and synthetic,
overfitting to it would be premature).

**Known limitation:** benchmark set is still only 3 cases, all hand-picked
and mostly clean. This calibration is a placeholder measurement, not a
statistically reliable one. Re-run and update this log once the benchmark
set includes real-world messy pages (target: 200-500 per the doc).