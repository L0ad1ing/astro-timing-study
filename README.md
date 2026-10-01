# astro-timing-study

**Does astrology time life events better than chance?** A pre-registered test on ~75,000 dated life events of
famous people from [Astro-Databank](https://www.astro.com/astro-databank): 23 classical timing techniques from seven
traditions, K.N. Rao's published marriage-timing rules, a practitioner's own method, 2,400 continuous planetary
features with gradient boosting, and an automated rule miner — each checked against falsification tests.

**Short answer: no technique, combination or machine-found rule beat the same person's ordinary dates once the test
was leak-free.** Two apparent discoveries along the way turned out to be data artifacts; both are documented below.

## Design

- **Case-crossover:** every event is compared with the *same person's* same calendar date 1 and 3 years before and
  after (own death: 1–4 years before). The natal chart, birth-time quality, fame and season are identical; only the
  sky differs. Score = probability that the real date ranks above a control date (0.50 = chance).
- **Pre-registration:** every hypothesis, target, statistic and pass bar was written down and committed before its
  run (`docs/prereg_*.md`), including the author's expected result.
- **Falsification tests:** person-grouped cross-validation, placebo dates (a control treated as the event), placebo
  windows (the same test shifted two years earlier), mismatched birth charts, an age-only (later age + calendar year
  + sex) baseline every model must beat, a lock-box, and — after the leaks below — folds grouped by event date and
  a held-out set of calendar months.

## Results

| Approach | Result | Details |
|---|---|---|
| 706 binary classical features, LightGBM | small within-person signal (C ≈ 0.53–0.55) that never turns into picking the right window (top-1 of 20 quarters: 5–7% vs 5% chance) | `src/features.py`, `src/models.py` |
| 23 isolated methods (Vedic, Tajika, Nakshatra, Western, Hellenistic, Medieval, Medical) | 15 of 300 method × event cells nominal at p < 0.05 (≈ chance), none replicated across data halves; consensus at chance (wedding dates: 6.25 methods flag marriage, other dates 6.22) | `docs/results_methods_*.json` |
| K.N. Rao's eight marriage parameters | identical on wedding dates and ordinary dates (six or more apply: 34.3% vs 34.3%) | `docs/results_rao_*.json` |
| A practitioner's Bhrigu Chakra "chain" method | 0.50 under both age conventions | `docs/results_bcp_chain_*.json` |
| 2,480 continuous harmonic features | apparent signal (Prize C 0.71) = **shared-date leakage**; with date-grouped folds nothing beats age | `docs/results_harmonic_*.json` |
| Automated rule mining, leak-free holdout | 17 of 220 rules "survived", all for prizes = **the Olympic calendar**; 0 survive without Games-period events | `docs/results_discovery_v2_*.json` |

### The two artifacts (useful beyond astrology)

1. **Shared-date leakage.** 13–41% of events share an exact date with another person (award nights, co-defendants,
   both spouses). Person-grouped folds let a model memorise "the sky on that night" from one person and recognise it
   for another. Grouping folds by event month removed every gain.
2. **Periodic features × periodic controls.** Prize events are 64.5% in even years (Olympic medals). Mars–Saturn
   repeats every 2.01 years and the controls sit at odd-year offsets, so a two-year planetary cycle became an
   even-year detector; 41% of held-out prize events fell during an Olympic Games. Removing them left nothing.

## Repository

```
src/preprocessing.py        Astro-Databank parsing, event cleaning, case-control sets, splits
src/features.py             ephemeris, dashas (Vimshottari, Chara, Yogini), Tajika, Ashtakavarga, 706 features
src/methods.py              the 23 isolated timing methods
src/rao.py                  K.N. Rao's marriage parameters (benchmarked on the book's case studies)
src/bcp_chain.py            Bhrigu Chakra chain method
src/models.py, validation.py  LambdaRank models, C-index, placebo/window/mismatched-chart tests, lock-box
src/harmonic_features.py    continuous harmonic features, age baseline, TreeSHAP importance
src/discovery_v2/           matched controls, leak-free month split, rule miner, conditional-logit evaluator
src/context_builder.py, consultation_agent.py, interactive_cli.py, knowledge_base/
                            a grounded LLM "consultation" layer (local model via Ollama) with code-enforced
                            safeguards; a reflection tool, not a predictor
scripts/                    one script per pre-registered analysis (run_*.py) plus post-hoc checks
docs/                       pre-registrations, results JSON, ARCHITECTURE.md (full technical description)
tests/                      unit tests (synthetic data and public charts; parity tests skip without the data)
```

## Running it

Python 3.11+: `pip install -r requirements.txt`, then `python -m pytest tests`.

The analyses need the Astro-Databank extract, which is **not included** (Astro-Databank's terms apply). See
`data/README.md` for the expected table; set `ASTRO_SOURCE_DB` to its path, then e.g.
`python -m scripts.run_methods` or `python -m scripts.run_discovery_v2`. The consultation layer needs
[Ollama](https://ollama.com) with `qwen3:8b`.

## Limitations

- Famous people only; birth-time ratings (Rodden AA/A) and event-date quality vary; event times are unknown, so
  transits are computed at noon UT (fast-moving Moon methods are least reliable).
- One target convention per event type (one house set and one significator); other traditional mappings are untested.
- Noise can hide a small effect; it cannot explain why everything lands at chance while the artifacts above are
  detected clearly.
- Pre-registration files have personal details of the author redacted in this public copy; methods and pass bars are
  unchanged. Commit hashes in docs refer to the private development history.

## License

MIT — see `LICENSE`. Data © Astrodienst / Astro-Databank, not included.
