"""
src/rules/bphs_dasha.py — dasha systems exactly as BPHS ch. 48 states them (G.C. Sharma tr., Sagar 1995, vol. 2).
Specs and page citations: docs/bphs_ch48_specs.md. Every number here is from those pages.

kalachakra(moon_lon, birth_jd, jd)  -> dict for the running Kalachakra mahadasha, or None past the pada's 9 dashas
kalachakra_natal(moon_lon)          -> amsa label, cycle, Deha and Jeeva signs of the birth pada
chara_years(signs, lagna) / chara(signs, lagna, birth_jd, jd)  -> Chara mahadasha sign and its years

Signs are 0 = Aries ... 11 = Pisces. Years are calendar years: the book adds whole years, months and days to the
birth date (vol. 2 p. 18 timeline), converting fractions at 12 months x 30 days.
"""
from __future__ import annotations

YEAR = 365.25
NAK = 360 / 27
PADA = NAK / 4

# ── Vimshottari (vol. 2 pp. 3-18, ch. 53 pp. 178-181) ────────────────────────
V_LORDS = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']   # from Ashwini
V_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]                                                 # v. 15


def vimshottari(moon_lon: float, birth_jd: float, jd: float) -> dict:
    """MD, AD, PD with how far each has run. v. 12-16: lord of the birth nakshatra, elapsed = fraction of the
    nakshatra traversed x years. ch. 53 v. 1-2: AD = MD years x AD years / 120, starting with the MD lord; PD the
    same within the AD."""
    nak = (moon_lon % 360) / NAK
    i = int(nak) % 9
    t = (nak - int(nak)) * V_YEARS[i] + (jd - birth_jd) / YEAR
    while t >= V_YEARS[i]:
        t -= V_YEARS[i]
        i = (i + 1) % 9
    out = {'MD': {'lord': V_LORDS[i], 'elapsed': t, 'length': V_YEARS[i]}}
    length, start = V_YEARS[i], i
    for level in ('AD', 'PD', 'SD', 'PR'):       # SD sookshma (ch. 64), PR prana (ch. 65): same rule one level down
        j = start
        while True:
            sub = length * V_YEARS[j] / 120
            if t < sub:
                break
            t -= sub
            j = (j + 1) % 9
        out[level] = {'lord': V_LORDS[j], 'elapsed': t, 'length': sub}
        length, start = sub, j
    return out


# ── Kalachakra (vol. 2 pp. 44-80) ────────────────────────────────────────────
KC_YEARS = [7, 16, 9, 21, 5, 9, 16, 7, 10, 4, 4, 10]          # Table-14/15, v. 84 (p. 52)
_AR, _TA, _GE, _CN, _LE, _VI, _LI, _SC, _SG, _CP, _AQ, _PI = range(12)
_ROW = {                                                        # Table-14A (p. 46), checked against ch. 51 verses
    _AR: [_AR, _TA, _GE, _CN, _LE, _VI, _LI, _SC, _SG],
    _TA: [_CP, _AQ, _PI, _SC, _LI, _VI, _CN, _LE, _GE],
    _GE: [_TA, _AR, _PI, _AQ, _CP, _SG, _AR, _TA, _GE],
    _CN: [_CN, _LE, _VI, _LI, _SC, _SG, _CP, _AQ, _PI],
    _LE: [_SC, _LI, _VI, _CN, _LE, _GE, _TA, _AR, _PI],
    _VI: [_AQ, _CP, _SG, _AR, _TA, _GE, _CN, _LE, _VI],
    _LI: [_LI, _SC, _SG, _CP, _AQ, _PI, _SC, _LI, _VI],
    _SC: [_CN, _LE, _GE, _TA, _AR, _PI, _AQ, _CP, _SG],
}
SAVYA_SEQ = {**_ROW, _SG: _ROW[_AR], _CP: _ROW[_TA], _AQ: _ROW[_GE], _PI: _ROW[_CN]}
PARAMAYU = {a: sum(KC_YEARS[s] for s in seq) for a, seq in SAVYA_SEQ.items()}   # v. 89: 100/85/83/86

# v. 96-100 motions, as unordered sign pairs (see specs for why); v. 109-111/118 effects are directional
MOTIONS = {'mandooka': [{_VI, _CN}, {_LE, _GE}], 'markati': [{_CN, _LE}], 'simhavalokana': [{_PI, _SC}, {_SG, _AR}]}


def _pada(moon_lon: float) -> tuple[int, int, float]:
    x = moon_lon % 360
    n = int(x // NAK)
    q = int((x - n * NAK) // PADA)
    frac = (x - n * NAK - q * PADA) / PADA
    return n, min(q, 3), frac


def kalachakra_natal(moon_lon: float) -> dict:
    """v. 56-58: nakshatras in threes alternate Savya / Apasavya from Ashwini. v. 87-88: the pada's navamsa
    = (nakshatras passed mod 3) x 4 + pada. Apasavya rows are the Savya rows of the mirror amsa (7 - n) mod 12,
    run in reverse (Tables 14B, 22)."""
    n, q, frac = _pada(moon_lon)
    savya = (n // 3) % 2 == 0
    nat = (n % 3) * 4 + q
    amsa = nat if savya else (7 - nat) % 12
    seq = SAVYA_SEQ[amsa] if savya else SAVYA_SEQ[amsa][::-1]
    # v. 94-95: Savya first = Deha, last = Jeeva; Apasavya first = Jeeva, last = Deha
    deha, jeeva = (seq[0], seq[-1]) if savya else (seq[-1], seq[0])
    return {'nakshatra': n, 'pada': q, 'frac': frac, 'savya': savya, 'amsa': amsa, 'seq': seq,
            'paramayu': PARAMAYU[amsa], 'deha': deha, 'jeeva': jeeva}


def kalachakra(moon_lon: float, birth_jd: float, jd: float) -> dict | None:
    """v. 90-93: expired years = fraction of the pada traversed x paramayu, consumed through the 9 signs in order.
    The book does not say what follows the 9th dasha (Table-20 ends there): None after that."""
    k = kalachakra_natal(moon_lon)
    t = k['frac'] * k['paramayu'] + (jd - birth_jd) / YEAR
    if t < 0:
        return None
    for i, s in enumerate(k['seq']):
        y = KC_YEARS[s]
        if t < y:
            prev = k['seq'][i - 1] if i else None
            motion = None
            if prev is not None:
                pair = {prev, s}
                motion = next((m for m, pairs in MOTIONS.items() if pair in pairs), None)
            # ch. 66 (pp. 472-482, Tables 33-35): antardashas run through the same 9-sign sequence starting from
            # the dasha sign; each = dasha years x antardasha sign years / paramayu
            u, j = t, 0
            while j < 8:
                ad_len = y * KC_YEARS[k['seq'][(i + j) % 9]] / k['paramayu']
                if u < ad_len:
                    break
                u -= ad_len
                j += 1
            return {**k, 'index': i, 'pos': i + 1 if k['savya'] else 9 - i,    # pos = savya position (ch. 51 key)
                    'sign': s, 'prev': prev, 'motion': motion, 'elapsed': t, 'years': y,
                    'ad_sign': k['seq'][(i + j) % 9], 'ad_index': j}
        t -= y
    return None


# ── Chara (vol. 2 pp. 81-88) ─────────────────────────────────────────────────
# Lords used by the Chara count; v. 157 gives Scorpio and Aquarius two lords each.
RASI_LORDS = {0: ['Mars'], 1: ['Venus'], 2: ['Mercury'], 3: ['Moon'], 4: ['Sun'], 5: ['Mercury'], 6: ['Venus'],
              7: ['Mars', 'Ketu'], 8: ['Jupiter'], 9: ['Saturn'], 10: ['Saturn', 'Rahu'], 11: ['Jupiter']}
ODD_QUARTER = {0, 1, 2, 6, 7, 8}                                 # Table-23: Ar Ta Ge, Li Sc Sg count forward
MOVABLE, FIXED, DUAL = {0, 3, 6, 9}, {1, 4, 7, 10}, {2, 5, 8, 11}


def _count(frm: int, to: int, forward: bool) -> int:
    """Inclusive count from sign frm to sign to; v. 155-156 with the example p. 85 (count - 1 = years)."""
    return ((to - frm) % 12 if forward else (frm - to) % 12) + 1


def chara_years(signs: dict[str, int], exalt: dict[str, int] | None = None) -> dict[int, int]:
    """Years of each sign's Chara dasha. signs: planet -> sign (Rahu and Ketu needed for Sc/Aq).
    exalt: planet -> exaltation sign for the +1/-1 of v. 164-165 (pass None to skip until vol. 1 ch. 3 is read)."""
    def years_to(s, p):
        c = _count(s, signs[p], s in ODD_QUARTER)
        return 12 if c == 1 else c - 1                          # own sign -> 12 (notes p. 86)

    out = {}
    for s in range(12):
        lords = [p for p in RASI_LORDS[s] if p in signs]
        if len(lords) == 2 and all(signs[p] == s for p in lords):
            out[s] = 12                                         # v. 158
            continue
        lord = _chara_lord(signs, s, exalt)
        y = years_to(s, lord)
        if exalt and lord in exalt:                             # v. 164-165
            if signs[lord] == exalt[lord]:
                y += 1
            elif signs[lord] == (exalt[lord] + 6) % 12:
                y -= 1
        out[s] = y
    return out


def chara_order(lagna: int) -> list[int]:
    """v. 167: from the Lagna, forward if the 9th house sign is in an odd quarter, else backward."""
    forward = (lagna + 8) % 12 in ODD_QUARTER
    return [(lagna + i) % 12 if forward else (lagna - i) % 12 for i in range(12)]


def chara(signs: dict[str, int], lagna: int, birth_jd: float, jd: float, exalt=None) -> dict | None:
    """Running Chara mahadasha and antardasha. The first cycle only: ch. 48 does not say what follows the 12th
    dasha. Antardashas (specs): from the sign holding the dasha sign's lord, 12 signs forward (ch. 52 v. 90),
    each 1/12 of the dasha (ch. 53 v. 5); for Scorpio/Aquarius the lord used is the one the year count used."""
    yrs = chara_years(signs, exalt)
    t = (jd - birth_jd) / YEAR
    if t < 0:
        return None
    for i, s in enumerate(chara_order(lagna)):
        y = max(yrs[s], 0)
        if t < y:
            lord = _chara_lord(signs, s, exalt)
            j = min(11, int(t / (y / 12)))
            ad = (signs[lord] + j) % 12
            return {'index': i, 'sign': s, 'lord': lord, 'years': y, 'elapsed': t, 'ad_index': j, 'ad_sign': ad}
        t -= y
    return None


def _chara_lord(signs, s, exalt=None) -> str:
    """The lord the year count of sign s uses (v. 157-165): v. 159 the lord placed elsewhere when one sits in the
    sign; v. 164 an exalted lord first; v. 161-163 more planets with it, then dual > fixed > movable, then more years."""
    lords = [p for p in RASI_LORDS[s] if p in signs]
    if len(lords) == 1:
        return lords[0]
    a, b = lords
    in_a, in_b = signs[a] == s, signs[b] == s
    if in_a != in_b:
        return b if in_a else a
    if in_a and in_b:
        return a
    ex = [p for p in lords if exalt and exalt.get(p) == signs[p]]
    if len(ex) == 1:
        return ex[0]
    n_with = lambda p: sum(1 for q, x in signs.items() if q != p and x == signs[p])
    st = lambda x: 2 if x in DUAL else 1 if x in FIXED else 0
    c = lambda p: _count(s, signs[p], s in ODD_QUARTER)
    return max(lords, key=lambda p: (n_with(p), st(signs[p]), c(p)))
