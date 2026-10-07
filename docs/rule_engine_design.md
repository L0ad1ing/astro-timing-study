# Rule engine — design

Goal (requested 2026-10-02): code the classical rules themselves — BPHS, Phaladeepika, Saravali, KP — each as data with
its source, so every rule can be tested, alone and all together, instead of anyone picking which rules to try.

## Rule format (`rules/*.jsonl`, one rule per line)
```json
{"id": "BPHS-MAR-001", "source": "BPHS", "ref": "chapter/verse or page", "kind": "timing",
 "text": "short paraphrase of the rule",
 "when": { condition tree },
 "predicts": {"event": "Marriage", "direction": "+"},
 "status": "draft | verified", "notes": "..."}
```
- `kind: timing` — the condition mixes natal facts with what is running on a date (dashas, transits); `predicts.event`
  is one of the Astro-Databank event types, or `Positive` / `Negative` for rules that only call a period auspicious
  or inauspicious (Positive = marriage, child, career peak, prize, new job; Negative = divorce, illness, accident,
  arrest, trial, job loss, deaths). `predicts.direction`: `+` the rule says the event becomes MORE likely in that
  period, `-` LESS likely (e.g. "sound health" in a dasha = Illness, `-`). Tested on event dates vs the same
  person's control dates.
- `kind: natal` — the condition is about the birth chart only; `predicts` is a domain and direction
  (e.g. `{"domain": "mother", "direction": "-"}`); tested against graded outcomes (questionnaire, not yet collected).
- `status: draft` — encoded from standard practice / memory, citation not yet checked against a page of the text.
  `verified` — checked against the cited page. Only the citation status differs; both are testable.

## Condition language (`src/rules/engine.py`)
Logic: `{"all": [...]}`, `{"any": [...]}`, `{"not": {...}}`.

Planet references: `"Venus"`; `"lord:7"` (lord of the 7th from the Lagna); `"occupants:7"` (planets in the 7th);
`"aspecting:7"` (planets aspecting the 7th by Parashari sign aspect); `"with:lord:5"` (planets in the same sign as
the 5th lord); `"assoc:lord:3"` (planets conjunct, aspecting either way, or in exchange with the 3rd lord);
`"dispositor:<ref>"` (lord of the sign a planet occupies); `"d9lord:7"` (7th lord counted from the Navamsa Lagna).
A reference can stand for several planets; atoms are true if ANY of them satisfies the condition.

Atoms:
| atom | meaning |
|---|---|
| `{"in_house": [ref, [houses], "lagna"|"moon"]}` | planet in one of the houses (whole sign) |
| `{"in_sign": [ref, [signs]]}` | planet in one of the signs (0 = Aries) |
| `{"dignity": [ref, [classes]]}` | D1 dignity class (exalted, moolatrikona, own, great_friend, friend, neutral, enemy, great_enemy, debilitated) |
| `{"strong": ref}` / `{"weak": ref}` | dignity friend or better and not combust / enemy or worse, or combust |
| `{"conjunct": [ref, ref]}` | same sign |
| `{"aspects": [ref, target]}` | Parashari sign aspect; target = ref, `"house:N"` or `"sign:N"` |
| `{"associated": [ref, target]}` | conjunct, or either aspects the other, or sign exchange |
| `{"varga_in_house": ["D9"|"D7"|"D10"|"D12", ref, [houses]]}` | placement counted from that varga's Lagna |
| `{"varga_dignity": ["D9", ref, [classes]]}` | sign-level dignity in the divisional chart (natural friendship) |
| `{"is": [ref, ref]}` | the references share a planet (e.g. `["Sun", "lord:6"]`: the Sun is the 6th lord) |
| `{"combust": ref}` | planet combust (within the Sun's combustion orb) |
| `{"moon_phase": "waxing"|"waning"}` | natal Moon 0-180 deg ahead of the Sun (shukla paksha) or not |
| `{"dasha": [["MD","AD","PD"], ref]}` | the running dasha lord at any listed level is one of the planets |
| `{"transit": [planet, target, "occupies"|"aspects"|"either"]}` | transiting planet's sign relative to `"house:N"`, `"moon_house:N"` or a natal ref's sign; Jupiter/Saturn retrograde also act from the previous sign |
| `{"kc": {fields}}` | running Kalachakra mahadasha (BPHS ch. 48): `amsa` [signs], `pos` [1-9, savya order], `sign`, `prev` (previous dasha sign), `motion` [mandooka/markati/simhavalokana], `cycle` savya/apasavya, `house` [from Lagna], `lord_nature` benefic/malefic, `holds` ref, `holds_n` [ref, n], `holds_dignity` [classes], `role` deha/jeeva/either, plus the kc_natal fields; all listed fields must match |
| `{"kc_natal": {fields}}` | birth pada: `amsa`, `cycle`, `dj_holds_n` [ref, n] planets in Deha+Jeeva signs, `dj_both` ref, `deha_holds`, `jeeva_holds` |
| `{"yoga": name}` | a named natal rule from `rules/yogas.jsonl` |

KP needs its own primitives (Placidus cusps, star and sub lords, significators) — phase 2.

## Testing (same harness as the rest of the study)
1. Each timing rule alone: event-date vs control-date firing rate for its own event type, matched odds ratio;
   Bonferroni over all rules tested; replication across halves; folds grouped by person and month.
2. All rules at once: every rule a feature in the LightGBM ranker vs the 706-feature and age+year+sex baselines.
3. Natal rules: against questionnaire outcomes once collected.
Every batch pre-registered before running, as before.

## Goal extended (user, 2026-10-02): a complete reading engine
The engine should know every rule in the texts, work out which apply to a chart and a date, let rules change and
cancel one another, and produce chart readings - not only the subset testable on the event data.

### Rule format additions
- `predicts.domain` (open label: wealth, travel, education, vehicles, mother, longevity, ...) for any rule; timing
  rules may carry a data `event`, a `domain`, or both. Only rules with an `event` enter the statistical test.
- `effect` - how a rule acts on the other fired rules when it fires itself:
  `{"type": "cancels" | "weakens" | "strengthens" | "reverses", "targets": selector, "factor": x}`;
  selector keys: `ids`, `id_prefix`, `domain`, `event`, `direction`, `kind`, `chapter`.
- `scale` - `{"dignity_of": planet ref}`: the result is multiplied by the book's result share for that planet's
  dignity (vol. 1 ch. 3 v. 59-60), good results by the share, bad results by its complement.

### The reader (src/rules/reader.py)
fire (evaluate every rule) -> weigh (scale) -> interact (cancellations, then reversals, then weaken/strengthen; a
cancelled rule cannot act; every change recorded with the overruling rule's citation) -> combine (net score per
outcome with the rules for, against and cancelled). `Reader().read(person, jd)` returns a Reading with `.text()`.
Shadbala, functional nature and avasthas join the weighing step when vol. 1 ch. 29, 36, 47 are built.

### Build order
1. Finish BPHS vol. 1 (ch. 27-47) encoding every predictive statement, with interactions where the text states them.
2. Backfill the items logged as 'no matching event' in vol. 2 and vol. 1 ch. 1-26 as domain rules (from the ledgers).
3. Strength-based weighing, functional benefics, cancellations stated generally (e.g. an exalted planet does not
   cause the evil it takes part in, vol. 1 ch. 15 v. 17; Rahu/Ketu act for their dispositor/conjunct, vol. 2 ch. 49).
4. KP, Phaladeepika, Saravali the same way. 5. The pre-registered test (event rules only).
