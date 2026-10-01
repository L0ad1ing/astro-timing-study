# Pre-registration — K.N. Rao marriage-timing parameters (written before evaluating)

Implementation: src/rao.py, from "Astrology and Timing of Marriage" Ch. 2; benchmarked on the book's case
studies 1-2 (20 of 22 parameter/observation verdicts reproduced; differences documented in tests/test_rao.py).

The book's claim: at 218 marriages, P1 applied in 100%, P2 96%, P3 77%, P4 85%, P5 98%, P6 68%, P7 70%,
P8 59%; six or more parameters in 85.8%. No comparison dates were examined.

Test (training half, marriage case-control sets: the wedding date vs the same person's dates 3 and 1 years
before and 1 and 3 years after):
1. Each parameter's rate on wedding dates vs control dates (matched odds ratio, 95% CI). Book implies OR > 1.
2. "Six or more parameters" on wedding dates vs control dates.
3. LightGBM LambdaRank, Rao features only and full features + Rao: out-of-fold C-index, placebo C, window
   test and the mandatory placebo window test, mismatched charts.

My expectation: most parameters are satisfied at high rates on ordinary dates too (P1 and P5 near their
wedding-date rates), so matched odds ratios are near 1 (0.9-1.15) and the Rao-only C-index is 0.49-0.53.
