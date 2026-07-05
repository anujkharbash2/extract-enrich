# Confidence Calibration Log

## Run 1 — n=3 ground-truth cases (synthetic/hand-picked)
- json_ld:   claimed=0.90  actual=1.00  gap=-0.10  (n=2)
- fallback:  claimed=0.40  actual=1.00  gap=-0.60  (n=4)

**Action taken:** raised fallback confidence from 0.4 to 0.6 (partial correction,
not full match to observed 1.0 - sample is small and synthetic, overfitting to
it would be premature).

**Correction note:** first attempt changed the `min(confidence, 0.4)` ceiling in
main.py, which had no effect since the classifier itself already returns 0.4 for
DOM-heuristic detections (min(0.4, 0.6) = 0.4 regardless). Real fix was updating
the confidence value inside classifier.py's DOM-heuristic branch.

**Known limitation:** benchmark set is still only 3 cases, all hand-picked and
mostly clean. Re-run and update this log once the benchmark set includes real-world
messy pages (target: 200-500 per the doc).