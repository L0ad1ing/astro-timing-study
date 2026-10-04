# What the tests found (astro-timing-study, 2026-09-30) — the agent must respect this

Case-crossover tests on ~75,000 dated life events of famous people (Astro-Databank). Every result comes
from people the model never saw, checked with placebo, mismatched-chart and shuffled-label tests.

- No chart-specific signal: comparing a person's event date with their own other years gives C-index 0.47-0.51
  (0.50 = chance), the same as with a random other person's chart. (An earlier figure of 0.53-0.55 was withdrawn on
  2026-10-04: it came from cross-validation folds that leaked shared event dates.)
- Every classical text encoded in full and tested (BPHS, Phaladeepika, KP Readers, later KP books) timed 0 of 18
  event types better than a wrong chart.
- It does not translate into picking the time window: out of 20 three-month windows the real one is ranked
  first about 5-7% of the time (chance 5%) and in the top three 15-20% (chance 15%).
- K.N. Rao's eight marriage parameters and three observations each hold as often on ordinary dates as on
  wedding dates (six or more parameters: 34.3% of wedding dates, 34.3% of other dates).
- Single classical rules tested (Sade Sati, Ashtakavarga thresholds, pratyantardasha in the event house,
  D9/D10 transits, Chara, Yogini and Tajika periods) showed no timing effect on their own.

Consequences for consultations:
1. Describe themes and periods as possibilities to reflect on, never as predictions of specific events.
2. Any dated window is a test prediction: say plainly that these techniques have not shown timing power.
   Every such window is logged and later scored.
3. When a window narrows because of something the user said, say so: it came from the user, not the chart.
