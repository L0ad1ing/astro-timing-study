# Pre-registration — the BPHS rule engine, every checkable event type (written and committed before any run)

Requested by the author (2026-10-03): "Test for all possible events that can be checked in the database."
The engine (src/rules/engine.py + reader.py) holds every rule of Brihat Parasara Hora Sastra (both volumes, 2,697
rules, each cited to a page). 1,922 timing rules predict a datable event. This test asks one question: on the dates
real events happened, does the engine, run as designed, point at those dates more than at the same person's
control dates, beyond what a wrong chart with the same birth moment gives?

## Data
Astro-Databank (Parse/astro_master_data.db), training half 0, known birth times (Ascendant present), case-control
sets from src/preprocessing.case_control_sets: the event date vs the same person's same calendar date at -3, -1, +1,
+3 years (Death: -4..-1), at least 3 usable dates. Gender from the chart pages (scripts/run_rao.genders); birth
latitude/longitude from the source (needed for the Gulika/Pranapada/day-birth rules).

Event types (18, every type in the database that the rules make a prediction about):
Death, Marriage, Divorce, Birth_Child, Career_Peak, Prize, Job_Start, Job_End, Arrest, Trial, Illness, Accident,
Relationship_Begin, Relationship_End, Death_of_relative (all), and its label subsets Death of father, Death of mother,
Death of mate (labels 'Death of Father' / '(his|her) father died', likewise mother, and mate = 'Death of Mate' /
'(his|her) (wife|husband) died').
Not testable: Financial (145) and Relocation (59) — no BPHS rule names them and their polarity is undefined;
'Other' (unlabelled).
Prize: events within +-3 days of an Olympic Games are removed before analysis (the known calendar artifact,
docs/results_discovery_v2_parity_check.json).

## The engine score (fixed in advance; nothing is trained)
For each date, reader.Reader.read(chart, jd, kinds=('timing',)) runs the full pipeline: fire every timing rule,
weigh (rule scales and the synthesis weighting by dignity, Shadbala and avastha), apply the rules' effects
(cancel, reverse, weaken, strengthen). For event type T the score is the sum of signed weights (+ for direction '+',
- for '-', after reversals; cancelled rules weigh 0) of the fired rules relevant to T:
- rules whose event is T;
- for the relative subsets and for pooled Death_of_relative: rules for 'Death_of_relative'; for a pooled
  Death_of_relative set whose label is father/mother/mate, also that subset's rules;
- 'Positive' rules for Marriage, Birth_Child, Career_Peak, Prize, Job_Start, Relationship_Begin;
  'Negative' rules for every other type (engine.NEGATIVE_EVENTS).
Per set, C = share of control dates the event date outscores (ties count 1/2), models.per_set_c.

## Null: mismatched charts (keeps everything except the chart)
Each set is scored a second time with the natal longitudes of a random other person from all half-0 sets
(numpy seed 7), keeping the person's own birth moment, place, gender and dates. Age, calendar and the event's
place in the person's life are identical; only the chart differs. Any age-driven pattern in the rules (dasha
progress, age-based rules) is present in both and cancels.

## Primary outcome and pass rule (per event type)
dC = mean over sets of C(actual chart) - C(mismatched chart), paired bootstrap (2,000 resamples), Bonferroni over
18 types (0.14%-99.86% interval).
PASS only if: Bonferroni lower bound of dC > 0, AND C(actual) 95% interval lies above 0.5, AND the placebo is
clean: with the -1 y control as pseudo-event (validation.placebo_c_index slot order) the placebo dC (actual -
mismatched) 95% interval includes 0 or lies below it.
Confirmation (once, per PASS): the same dC on half 1, 95% lower bound > 0. Only a confirmed PASS is reported as a
finding.

## Secondary (reported, not decisive)
1. Unweighted engine: each fired relevant rule counts +-1 (rule's own direction), no synthesis, no effects.
2. Direct rules only: Positive/Negative pooled rules left out.
3. Per rule: for each rule and each type it is relevant to (>= 30 sets), per-set firing difference
   (event - mean of controls), actual minus mismatched; t-statistic; Benjamini-Hochberg FDR 5% over all
   rule x type tests. Reported: how many are significant in the rule's claimed direction vs the opposite direction
   (under no effect these counts are equal).
4. Learned combination: LightGBM LambdaRank (models.PARAMS) on the 1,922 rule-firing indicators, 5 folds grouped by
   person AND event month (harmonic_date_leak_check.grouped_folds), vs DEMO (age + calendar year + sex), paired
   dC with Bonferroni over 18, placebo.

## Caveats stated in advance
- Birth_Child (~40 sets in half 0) and Relationship_* are too small to detect anything but a huge effect; their
  results are reported but should be read as underpowered.
- Job_Start and Relationship_End have no direct rule; they are scored by the pooled Positive/Negative rules only.
- Astro-Databank events are those notable enough to be recorded; this tests the rules on that population only.
- The synthesis weighting is the engine's formula built on the book's principles (docs/rule_engine_design.md);
  secondary 1 shows the result without it.

## Expectations (mine, before running)
No type passes. dC within +-0.01 everywhere. Every earlier method (23 isolated methods, Rao, strength) was at chance
under the leak-proof design. Per-rule: significant counts roughly equal in both directions.

## Disclosure
Before this file was committed, the script was smoke-tested on 600 sets (an every-n-th sample of half 0) to check
the code runs (output in data/, marked invalid). Nothing in the design above was changed after it.
