# astro-timing-study

**Can astrology tell *when* something will happen in a person's life?**

This repository is a large, pre-registered test of that question. It uses about 75,000 dated life events
(marriages, divorces, prizes, arrests, illnesses, deaths…) of famous people with recorded birth times. It tests
23 classical timing techniques from seven traditions, a published marriage-timing rulebook, a practitioner's own
method, machine learning on raw planetary geometry, and an automated search for new rules.

**The answer, in one line:** once the test was airtight, nothing did better than chance. Not a single technique,
not combinations of techniques, not the machine. Twice, something looked like a real signal; both times it turned
out to be a quirk of the data, and both are explained below because they are the most useful part of the study.

---

## Contents

1. [The question and why it is testable](#1-the-question-and-why-it-is-testable)
2. [The data](#2-the-data)
3. [How the test works](#3-how-the-test-works)
4. [The experiments, in the order they were run](#4-the-experiments-in-the-order-they-were-run)
5. [The two things that looked real and weren't](#5-the-two-things-that-looked-real-and-werent)
6. [What it adds up to](#6-what-it-adds-up-to)
7. [Limitations](#7-limitations)
8. [FAQ](#8-faq)
9. [Repository layout and how to run it](#9-repository-layout-and-how-to-run-it)

---

## 1. The question and why it is testable

Astrological timing techniques make a concrete claim: given a birth chart, certain periods are "activated" for
certain areas of life. In Vedic astrology, a dasha of the 7th-house lord brings marriage. In Hellenistic astrology,
a profection to the 10th brings career events. Transiting Saturn on a sensitive point brings hardship.

If that is true, then across thousands of real lives, **a person's actual event dates should be "activated"
more often than that same person's ordinary dates.** That is something you can count.

## 2. The data

- **Source:** [Astro-Databank](https://www.astro.com/astro-databank), the best-known collection of birth data for
  public figures. Each record has a birth date, time and place, a reliability rating for the birth time (Rodden
  ratings AA, A, B…), and often a list of dated life events.
- **Size:** about 75,000 usable dated events after cleaning.
- **Cleaning, before any test:**
  - A parser bug that read some coordinates as zero, which gave 28% of people wrong birth times, was fixed and the
    data rebuilt.
  - Events falling within 1.5 days of a birthday were dropped. These are mostly placeholder dates: 7% of events,
    against under 1% expected by chance.
  - "Death" was split into the person's own death and the death of a relative.
  - Scraped non-events, such as page footers and cross-references, were removed.
  - Six extra event types were added from the source's "Other" bucket: prize, job start, job end, trial,
    relationship begin and relationship end.
- **Split:** people are divided into two halves by a hash of their name. Models are only ever fit on one half.
- **Not included in this repository:** the data itself, because Astro-Databank's terms apply. See
  [`data/README.md`](data/README.md).

## 3. How the test works

### Each person is compared only with themselves

For every event, the comparison ("control") dates are **the same person's same calendar date 1 and 3 years before
and after.** For someone's own death the controls are 1 to 4 years *before*, since there are no dates after it.

> Example: a wedding on 11 October 1975 is compared with 11 October 1972, 1974, 1976 and 1978 in the same
> person's life.

This removes almost everything that could fake a result:

| Held constant | Why it matters |
|---|---|
| Birth chart | The same natal chart is used on every date |
| Birth-time accuracy | The same person, so the same rating |
| Fame, era, culture | The same life |
| Season and the Sun's position | The same calendar date |

The only thing that differs between the event date and the controls is **where the planets were.** If a technique
works, it should "fire" on the event date more often than on the controls.

### The score

- For rule-based techniques, the score is how often a rule fires on event dates versus control dates. It is
  reported as a matched odds ratio, where 1.0 means no difference.
- For models, the score is the probability that the real date ranks above a control date, where **0.50 is a coin
  flip.** This is a C-index (concordance).

### Rules that kept the test honest

- **Pre-registration:** before each experiment, the hypothesis, the target houses and planets, the statistic, the
  pass bar and the author's *expected* result were written down and committed (`docs/prereg_*.md`). Nothing was
  adjusted after seeing results.
- **Out-of-sample only:** every reported model score comes from people the model never saw.
- **Falsification tests**, which a real effect must survive:

| Check | What it does | What a real effect does |
|---|---|---|
| **Fake event date** | A control date is treated as if it were the event | Scores about 0.50 |
| **Shifted window** | The whole test is moved two years earlier, where nothing happened | Finds nothing |
| **Swapped chart** | The features are recomputed with a random stranger's birth chart | Loses its signal |
| **Age-only baseline** | A model that knows only age (later also calendar year and sex) | Is beaten by the astrology model |
| **Replication** | The result is checked again in the other half of the data | Holds up there too |
| **Multiple testing** | Many tests are run at once (Bonferroni) | Still clears the corrected bar |

## 4. The experiments, in the order they were run

### Experiment 1: classical features plus machine learning

- **What was tested:** 706 yes/no features per date. They cover:
  - transits to the birth chart
  - Vimshottari maha-, antar- and pratyantar-dashas
  - Jaimini Chara dasha and Yogini dasha
  - the Tajika annual chart
  - Ashtakavarga, Sade Sati and double transit
  - transits to the D9 and D10 charts

  These were fed into a gradient-boosted ranking model (LightGBM).
- **Result:** a small within-person signal for a few event types, around **0.53–0.55**, which passed the
  fake-date and swapped-chart checks. **It did not translate into usable timing.** When asked to pick which of 20
  three-month windows an event fell in, the model ranked the right one first 5–7% of the time, against 5% for
  guessing.
- **A caught false alarm:** an early model seemed to time *own death* well (11.8% top-window hits, against 5%).
  The shifted-window check scored the same, because the model was simply recognising the *latest* dasha period of a
  life. That is why the shifted-window check is mandatory.
- **New event types** (training half): Prize 0.531, Trial 0.545, Job start 0.513, Job end 0.518 (Job end failed the
  swapped-chart check). None picked windows above chance in a way that held up.

### Experiment 2: K.N. Rao's marriage-timing rules

- **What was tested:** the eight parameters and three observations from *Astrology and Timing of Marriage*
  (K.N. Rao, Bharatiya Vidya Bhavan). The code was checked against the book's own worked case studies before
  running. The book reports that "six or more" parameters apply in about 86% of the 218 marriages it studied, but it
  never checked ordinary dates.
- **Data:** 3,663 marriages with known birth times.

| | Wedding dates | Same people, other dates |
|---|---|---|
| Six or more of the eight parameters apply | **34.3%** | **34.3%** |
| P1 (dasha lords connected to marriage) | 99.6% | 99.6% |
| P4 (Jupiter and Saturn double transit) | 81.4% | 81.8% |

Every parameter came out the same on wedding dates and ordinary dates. Models built on the Rao features scored
0.500. **The rules aren't wrong about weddings; they're true of almost any date.**

### Experiment 3: a practitioner's Bhrigu Chakra "chain" method

- **What was tested:** a method described by the author.
  1. Each year of life activates one house (age 1 is the 1st house, age 12 the 12th, then the cycle repeats).
  2. The method then follows links outward: the house leads to its lord and the planets in it, and each planet leads
     to the house it sits in and the houses it rules.
  3. Houses closer to the start of the chain count more.
- **Two counting conventions were tested:** completed age and running year.
- **Result:** marriage **0.501** (n = 7,349), prize 0.505, arrest 0.498. Every type was between 0.47 and 0.52,
  except relationship end at 0.559 (n = 110, interval 0.502–0.618). With 18 event types per convention, one interval
  just clearing 0.50 is what chance produces. The running-year convention gave the same picture.
- **A separate small blind test** used the consultation engine (`scripts/blind_test.py`) on one volunteer with a
  verified birth time. The engine wrote readings for a real past period and for decoy years, and the volunteer picked
  the real one 1 time out of 4, which is chance.

### Experiment 4: 23 techniques, each on its own, then combined

- **What was tested:** each technique says which houses and planets are "activated" on a date. An event counts as
  flagged if its target house or natural significator is activated: the 7th house or Venus for marriage, the 10th
  house or the Sun for career, and so on, all fixed in advance.

| Tradition | Techniques |
|---|---|
| Vedic | Vimshottari dasha, the BCP chain, Chara dasha, Tajika Muntha, double transit, Jupiter transit |
| Tajika | Annual Lagna, Mudda dasha |
| Nakshatra | Tara from the birth star, birth-star transits, star lord |
| Western | Secondary progressions, solar arc, solar return, outer-planet transits |
| Hellenistic | Annual profections, zodiacal releasing from Spirit and from Fortune |
| Medieval | Firdaria, distribution through the bounds, Lord of the Year by transit |
| Medical | Saturn and Mars to the vital points, maraka and 6th/8th-lord dasha periods |

- **Results:**
  - **Each technique alone:** 15 of 300 technique × event combinations looked significant, which is exactly what
    luck produces at the 5% level. **None replicated** in the other half of the data.
  - **Combined:** counting how many techniques agree didn't help. On wedding dates an average of **6.25** techniques
    flagged marriage; on the same people's other dates, **6.22**. Consensus scores were 0.49–0.52 for every event
    type.
  - **Built-in agreement:** some techniques agree because they share machinery, not because they confirm each
    other. Double transit and Jupiter transit correlate at 0.46, and Tajika Muntha and annual profections at 0.46
    (both advance one sign a year). More techniques agreeing is not more evidence.

### Experiment 5: let the machine find the geometry itself

- **The idea:** maybe signs, houses and hand-written rules are the problem. So throw them out and give a model the
  raw geometry.
- **What was tested:** 2,480 continuous features per date.
  - Every angle between every pair of planets, and between today's planets and the birth chart, encoded as smooth
    waves that peak on the classical aspects: conjunction, opposition, trine, square, sextile, quintile, octile.
  - Planetary speeds, stations and declinations.
  - The model had to beat an **age-only model**, because slow-moving planets quietly encode age, and events cluster
    by age. The 84 purest "age clock" features, such as Saturn's angle to its own birth position, were removed.
- **First result:** five event types appeared to pass, with Prize scoring **0.71** against 0.51 for age alone.
- **Why it wasn't real:** the "sky-only" features, which are identical for everyone on a given day and therefore
  cannot know anything about a person, did as well as the personal ones. Swapping in a stranger's birth chart barely
  mattered. See [Section 5](#5-the-two-things-that-looked-real-and-werent): this was **shared-date leakage.** With it
  blocked:

| Event type | First run | Leak blocked | Age only |
|---|---|---|---|
| Prize | 0.713 | 0.512 | 0.500 |
| Arrest | 0.607 | 0.484 | 0.467 |
| Career peak | 0.602 | 0.506 | 0.494 |
| Trial | 0.611 | 0.473 | 0.499 |
| Death of relative | 0.573 | 0.440 | 0.492 |

The other half of the data told the same story. The gain over age was +0.15 to +0.30 for events in months the model
had seen during training, and −0.10 to −0.01 for months it hadn't.

### Experiment 6: an automated, interpretable rule miner

- **What was tested:** a search for readable rules, such as "Mars within 5° of a square to natal Venus".
- **The search, on the training months only:**
  - About 10,300 candidate rules per event type: single thresholds, plus two-condition rules from shallow
    decision trees.
  - The top 20 per type went forward, 220 rules across 11 event types.
- **Holdout, used once:** events in **February, May, August and November.**
  - No person, month or date was shared with training, and an audit confirmed it.
  - Comparison dates were also cleaned of any year with another recorded event nearby.
  - Each rule had to beat a baseline that knows **age, calendar year and sex**, at p < 0.01 / 220.
- **Result:** **17 rules survived, all of them for prizes.** The strongest had p = 10⁻²⁹. Nearly all of them
  depended on the angle between Mars and Saturn. The other 10 event types produced nothing, and the best rule often
  flipped direction on the holdout.
- **Why it wasn't real:** it was **the Olympic Games.** See [Section 5](#5-the-two-things-that-looked-real-and-werent).
  Each correction removed more rules:

| Correction | Rules still passing (of 17) |
|---|---|
| None (pre-registered result) | 17 |
| Adjust for even/odd year | 9 |
| Adjust for each calendar year and the Olympic season pattern | 1 |
| **Remove events that took place during an Olympic Games** | **0** |

## 5. The two things that looked real and weren't

These apply to any machine-learning study on dated records, not only astrology.

### Shared-date leakage

**13–41% of events share their exact date with another person in the database:** the same awards night,
co-defendants at one trial, both spouses' divorce, siblings losing the same parent.

Splitting the data by person is the standard safeguard against leakage, but here it isn't enough. If person A is in
training and person B in testing, and both have an event on Oscar night, the model learns "the sky on that night
means an event" from A and recognises it for B. The sky is the same for everyone on a given day, so any feature
that can pin down the date becomes a memorisation channel.

**The fix:** group the split by event date (here, by month) as well as by person. Also include a "sky-only" feature
set as a tripwire: if features that know nothing about individuals score as well as personal ones, the model is
reading the calendar.

### Periodic features meet periodic controls

**64.5% of prize events fall in even years,** compared with about 50% for every other event type. The top years
are 1996, 2021, 2012, 2008 and 2000: Olympic years. A large share of "prizes" in the data are Olympic medals.

- Mars and Saturn line up every **2.01 years.**
- The control dates were 1 and 3 years away, both odd numbers.
- So on every control date, the Mars–Saturn cycle was in the *opposite* phase from the event. A two-year planetary
  cycle became a perfect even-year detector.
- The holdout months happened to include February (Winter Games) and August (Summer Games). **41%** of held-out
  prize events took place during an Olympic Games.

**The lesson:** if a feature has a cycle and your controls are spaced on a cycle, check whether the two line up. Any
regular rhythm in the data (Olympics, elections, biennial awards, fiscal years) can become a huge fake effect.

## 6. What it adds up to

| Approach | Result |
|---|---|
| 706 classical features + machine learning | Tiny within-person signal; window prediction at chance |
| K.N. Rao's marriage rules | Chance (34.3% vs 34.3%) |
| BCP chain method | Chance (0.50) |
| 23 techniques, alone | Chance; nothing replicated |
| 23 techniques, combined | Chance (6.25 vs 6.22 techniques agreeing) |
| Continuous geometry + machine learning | Date memorisation |
| Automated rule mining | The Olympic calendar |

On this evidence, astrological techniques don't time life events better than chance. That holds for every technique
tested, every way of combining them, and every rule a machine could find in the geometry.

What this study does **not** address is why many people find a birth chart useful as a mirror for reflection.
That's a different claim, and it isn't about prediction.

## 7. Limitations

- **Famous people only.** Their lives and records may differ from everyone else's.
- **Data quality varies.** Birth-time ratings range from AA (birth certificate) to A (memory), and event dates
  range from exact to approximate.
- **Event times are unknown,** so the planets are computed at noon on the event date. Methods that depend on the
  fast-moving Moon (about 13° a day) are the least reliable here.
- **One target convention per event** (one house set and one significator). Other traditional mappings weren't
  tested.
- **Noise can hide a small effect.** It's harder to see noise producing a clean null everywhere while the artifacts
  above were detected clearly and traced to their causes.
- **Redactions:** the pre-registration files have the author's personal details redacted in this public copy;
  methods and pass bars are unchanged. Commit hashes mentioned in the docs refer to the private development history.

## 8. FAQ

**Isn't 0.53–0.55 a real signal?**
It may be a real *statistical* difference, and it survived the fake-date and swapped-chart checks. But it never
turned into the ability to say *when*, and nothing at the level of individual techniques or rules replicated.
Whatever it is, it isn't usable timing, and it may reflect subtler properties of the data.

**Why not use ordinary people's data?**
There is no large public dataset of ordinary people's birth times with dated life events. Astro-Databank is the
standard source.

**Did you pick techniques that were set up to fail?**
The techniques, target houses and significators come from standard practice. They were fixed in advance and
published here. If you think a mapping is wrong, the code makes it easy to change and rerun, and that's exactly the
kind of audit this repository is meant for.

**Couldn't a skilled astrologer do better than rules?**
Possibly. This study tests techniques, not people. A blind test of practitioners is a different design, and the
personal blind tests here are too small to say anything about it.

**What is the consultation engine for, then?**
`src/consultation_agent.py` is a grounded language-model layer that explains a chart's current state. Its own code
caps confidence and refuses dates that weren't computed. It's built as a reflection tool, not a predictor.

## 9. Repository layout and how to run it

```
src/preprocessing.py          Astro-Databank parsing, event cleaning, case-control sets, splits
src/features.py               ephemeris (Swiss Ephemeris, Lahiri), dashas, Tajika, Ashtakavarga, the 706 features
src/methods.py                the 23 isolated techniques
src/rao.py                    K.N. Rao's marriage parameters (benchmarked on the book's case studies)
src/bcp_chain.py              the Bhrigu Chakra chain method
src/models.py, validation.py  ranking models, C-index, fake-date / shifted-window / swapped-chart tests, lock-box
src/harmonic_features.py      continuous harmonic features, age baseline, SHAP importance
src/discovery_v2/             matched controls, leak-free month split, rule miner, conditional-logit evaluator
src/context_builder.py, consultation_agent.py, interactive_cli.py, knowledge_base/
                              the reflection-only consultation layer
scripts/                      one script per pre-registered experiment (run_*.py) plus the post-hoc checks
docs/                         pre-registrations, every results file, ARCHITECTURE.md (full technical description)
tests/                        unit tests on synthetic data and public example charts
```

| Experiment | Pre-registration | Script | Results |
|---|---|---|---|
| New event types (ML) | `prereg_new_events.md` | `run_pipeline.py` | `results_20260930_*.json` |
| K.N. Rao | `prereg_rao.md` | `run_rao.py` | `results_rao_*.json` |
| BCP chain | `prereg_bcp_chain.md` | `bcp_chain_test.py` | `results_bcp_chain_*.json` |
| 23 techniques | `prereg_methods.md` | `run_methods.py` | `results_methods_*.json` |
| Continuous geometry | `prereg_harmonic.md` | `run_harmonic_pipeline.py`, `harmonic_date_leak_check.py` | `results_harmonic_*.json` |
| Rule mining | `prereg_discovery_v2.md` | `run_discovery_v2.py`, `discovery_v2_parity_check.py` | `results_discovery_v2_*.json` |

**Running it:**
1. Install the dependencies (Python 3.11+): `pip install -r requirements.txt`
2. Run the tests: `python -m pytest tests`. They need no data; the parity tests skip without it.
3. For the experiments, build the Astro-Databank extract (see [`data/README.md`](data/README.md)) and set
   `ASTRO_SOURCE_DB` to its path. Then run, for example, `python -m scripts.run_methods`.
4. The consultation layer also needs [Ollama](https://ollama.com) with `qwen3:8b`.

Audits, corrections and replications are welcome. Please open an issue.

## License

Code: MIT (see [`LICENSE`](LICENSE)). Data © Astrodienst / Astro-Databank, not included.
