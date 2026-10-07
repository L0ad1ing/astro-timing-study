"""
src/rules/bphs_functional.py — functional nature by Lagna, BPHS vol. 1 ch. 36 v. 19-44 (G.C. Sharma tr., Sagar;
book pp. 481-493). For each Lagna sign: functional malefics, benefics, yoga karakas, killers (marakas) and neutrals, as
the verses list them (paraphrased). v. 2-16 give the principles (kendra lords lose natural beneficence, trikona lords
always good, 3/6/11 lords evil, 2/12/8 lords act by association, kendra+trikona lord = yogakaraka; Rahu/Ketu give
the results of the house they occupy and the planet they join).
"""
FUNCTIONAL = {
    0: {'malefic': {'Saturn', 'Mercury', 'Venus'}, 'benefic': {'Jupiter', 'Sun'}, 'yogakaraka': set(),
        'killer': {'Venus'}, 'note': 'Saturn with Jupiter not a yoga (v. 19-22)'},
    1: {'malefic': {'Jupiter', 'Venus', 'Moon'}, 'benefic': {'Saturn', 'Sun'}, 'yogakaraka': {'Saturn'},
        'killer': {'Jupiter', 'Venus', 'Moon', 'Mars'}, 'note': 'Mercury gives less good (v. 23-24)'},
    2: {'malefic': {'Mars', 'Jupiter', 'Sun'}, 'benefic': {'Venus'}, 'yogakaraka': set(),
        'killer': {'Moon'}, 'note': 'Saturn-Jupiter as for Aries (v. 25-26)'},
    3: {'malefic': {'Venus', 'Mercury'}, 'benefic': {'Mars', 'Jupiter', 'Moon'}, 'yogakaraka': {'Mars'},
        'killer': {'Saturn', 'Sun'}, 'note': 'Saturn and the Sun kill by association (v. 27-28)'},
    4: {'malefic': {'Mercury', 'Venus', 'Saturn'}, 'benefic': {'Mars', 'Jupiter', 'Sun'}, 'yogakaraka': set(),
        'killer': {'Saturn'}, 'note': 'Jupiter-Venus conjunction not auspicious; the Moon good with a benefic (v. 29-30)'},
    5: {'malefic': {'Mars', 'Jupiter', 'Moon'}, 'benefic': {'Mercury', 'Venus'}, 'yogakaraka': {'Mercury', 'Venus'},
        'killer': {'Venus'}, 'note': 'the Sun acts by association (v. 31-32)'},
    6: {'malefic': {'Jupiter', 'Sun', 'Mars'}, 'benefic': {'Saturn', 'Mercury'}, 'yogakaraka': {'Moon', 'Mercury'},
        'killer': {'Mars'}, 'note': 'Jupiter etc. kill; Venus neutral (v. 33-34)'},
    7: {'malefic': {'Venus', 'Mercury', 'Saturn'}, 'benefic': {'Jupiter', 'Moon'}, 'yogakaraka': {'Sun', 'Moon'},
        'killer': {'Mars', 'Venus', 'Mercury', 'Saturn'}, 'note': 'Mars neutral or killer (v. 35-36)'},
    8: {'malefic': {'Venus'}, 'benefic': {'Mars', 'Sun'}, 'yogakaraka': {'Sun', 'Mercury'},
        'killer': {'Saturn', 'Venus'}, 'note': 'Jupiter neutral (v. 37-38)'},
    9: {'malefic': {'Mars', 'Jupiter', 'Moon'}, 'benefic': {'Venus', 'Mercury'}, 'yogakaraka': {'Venus'},
        'killer': {'Mars', 'Jupiter', 'Moon'}, 'note': 'Saturn not a killer; the Sun acts by association (v. 39-40)'},
    10: {'malefic': {'Jupiter', 'Moon', 'Mars'}, 'benefic': {'Venus', 'Saturn'}, 'yogakaraka': {'Venus'},
         'killer': {'Jupiter', 'Sun', 'Mars'}, 'note': 'Mercury medium (v. 41-42)'},
    11: {'malefic': {'Saturn', 'Venus', 'Sun', 'Mercury'}, 'benefic': {'Mars', 'Moon'}, 'yogakaraka': {'Mars', 'Jupiter'},
         'killer': {'Saturn', 'Mercury'}, 'note': 'Mars is not a killer although lord of the 2nd (v. 43-44)'},
}


def nature(lagna: int, planet: str) -> str | None:
    """'yogakaraka' | 'benefic' | 'malefic' | 'neutral' for the seven planets; None for Rahu/Ketu."""
    f = FUNCTIONAL[lagna]
    if planet in f['yogakaraka']:
        return 'yogakaraka'
    if planet in f['benefic']:
        return 'benefic'
    if planet in f['malefic']:
        return 'malefic'
    return 'neutral' if planet not in ('Rahu', 'Ketu') else None
