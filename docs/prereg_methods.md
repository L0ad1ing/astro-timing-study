# Pre-registration — isolated methods, agreement and consensus (written before building/running)

Requested by the author (2026-10-01): isolate many techniques, compare which agree, test consensus; include tropical,
Hellenistic and medical astrology.

Each METHOD maps (person, date) to activated HOUSES and PLANETS. An event type is "flagged" by a method when a
target house is activated or its significator planet is activated.
Targets (house; significator): Marriage 7; Venus | Divorce 7; Venus | Birth_Child 5; Jupiter | Career_Peak, Prize,
Job_Start 10; Sun | Arrest, Trial 12/6; Saturn | Illness 6; Saturn | Accident 8; Mars | death of father 9; Sun |
death of mother 4; Moon | death of spouse 7; Venus | own Death 8; Saturn.

Methods (sidereal Lahiri for Vedic; tropical for Western/Hellenistic; whole-sign houses throughout):
 V1 Vimshottari: MD and AD lords -> houses they rule and occupy; planets {MD, AD}
 V2 BCP chain (completed age): houses/planets within 2 steps of the active house
 V3 Chara dasha (K.N. Rao, AD from the MD sign backward): AD sign's house and houses it Jaimini-aspects; planets in it
 V4 Tajika: Muntha's house; Muntha lord
 V5 double transit: houses Jupiter (occ./5/7/9) and Saturn (occ./3/7/10) both influence; planets in them
 V6 Jupiter transit: houses Jupiter occupies or aspects; planets in them
 W1 secondary progressions: natal planets within 1 deg of a conj/sq/trine/opp from progressed Sun or Moon; houses they rule
 W2 solar arc: natal planets/angles within 1 deg of conj/sq/opp from solar-arc-directed planets; houses they rule (+1/10 for Asc/MC)
 W3 solar return (tropical, birth place): natal house of the return Ascendant; its ruler
 W4 outer transits: natal planets within 1 deg of a conj/sq/trine/opp from transiting Jupiter, Saturn, Uranus, Neptune, Pluto
 H1 profection (tropical): profected house and houses ruled by the Lord of the Year; LOY
 H2 zodiacal releasing from the Lot of Spirit (sect-aware; L1 years / L2 months by sign; loosening of the bond):
    L2 sign's house; its ruler
 H3 firdaria (day/night order, Chaldean sub-periods; nodes without sub-periods): ruler and sub-ruler; houses they rule
 M1 medical (Illness, Accident, own Death only): transiting Saturn or Mars within 1.5 deg of conj/sq/opp to the
    Ascendant ruler, Sun or Moon (tropical)
 M2 Vedic medical (Illness, Accident, own Death only): MD or AD lord is a maraka (rules 2 or 7) for Death; rules 6 or 8
    for Illness; rules or occupies 8 for Accident

Data: Astro-Databank, both halves (no fitting), known birth times; event date vs the same person's dates -3,-1,+1,+3
years (own death: -4..-1, sampled to 5,000 events). Analyses:
 1. Each method x event type: rate flagged on event dates vs controls; matched odds ratio with 95% CI.
 2. Agreement: phi correlation between methods on control dates (built-in agreement).
 3. Consensus: number of methods flagging (k); P(event-date k > control k), ties half; plus placebo (control 1 year
    before the event as pseudo-event vs the others) — must be ~0.50 for a consensus result to count.
Expectations (mine): individual methods OR 0.9-1.1 for nearly all cells; strong built-in correlations among period
methods; consensus 0.49-0.52 with placebo ~0.50. With ~200 method x event cells, about 10 nominal p<0.05 results
are expected by chance; only cells with OR CI excluding 1 AND replicated in both data halves count.

## Addendum (2026-10-01, before any run): medieval, Tajika, nakshatras
Requested by the author. Firdaria is reclassified as medieval (MD1); H3 becomes zodiacal releasing from the Lot of Fortune.
 H3 zodiacal releasing from the Lot of Fortune: L2 sign's house; its ruler
 MD1 firdaria (as H3 was defined)
 MD2 distribution: Ascendant (tropical) directed 0.98565 deg/year through the Egyptian bounds; the bound lord
     (distributor) and the houses it rules
 MD3 Lord of the Year in transit: the (tropical) house the profected Lord of the Year is transiting
 TJ2 Tajika annual Lagna (sidereal solar return at the birth place): its natal house; its lord
 TJ3 Mudda dasha: start lord = (birth nakshatra no. + completed years - 2) mod 9 in Vimshottari order from Ketu,
     periods proportional to Vimshottari years within the Tajika year from the solar return; the lord's houses
     (rules/occupies) and the lord
 N1 tara of the transiting Moon (nakshatra counted from the birth star, 9-fold): event types Marriage, Birth_Child,
    Career_Peak, Prize, Job_Start flagged on taras 2,4,6,8,9; all other event types on taras 3,5,7
 N2 janma nakshatra transit: Saturn (hard events) or Jupiter (Marriage, Birth_Child, Career_Peak, Prize, Job_Start)
    in the birth star or its 10th/19th (anujanma, trijanma)
 N3 star lord: the nakshatra lord of the antardasha lord; houses it rules/occupies; the star lord
(V4 is Tajika Muntha = TJ1.) Same analyses, expectations and counting rule as above.
