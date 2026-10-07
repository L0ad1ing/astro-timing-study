"""Explain why a rule fired on a chart: walk its condition tree and describe the true atoms in plain words, with chart
references resolved to planets (e.g. 'the 7th lord (Mars) in house 12')."""
from src.rules import engine as E
from src.rules import kp_core as K

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
ORD = lambda n: f'{n}{"th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")}'


def ref_name(c, ref):
    if isinstance(ref, list):
        if len(ref) > 3:
            return 'one of ' + ', '.join(sorted({p for r in ref for p in E.refs(c, r)}))
        return ' or '.join(ref_name(c, r) for r in ref)
    try:
        ps = sorted(E.refs(c, ref))
    except Exception:
        return str(ref)
    s = str(ref)
    if s.startswith('lord:'):
        return f'the {ORD(int(s[5:]))} lord ({", ".join(ps)})'
    if s.startswith('mlord:'):
        return f'the {ORD(int(s[6:]))} lord from the Moon ({", ".join(ps)})'
    if s.startswith('dispositor:'):
        return f'the dispositor of {ref_name(c, s[11:])} ({", ".join(ps)})'
    if s.startswith(('occupants:', 'aspecting:')):
        return f'{s.split(":")[0]} of house {s.split(":")[1]} ({", ".join(ps) or "none"})'
    return ', '.join(ps) if ps else s


def where(c, ps):
    return '; '.join(f'{p} in {SIGNS[c.signs[p]]}, house {c.house_of(p)}' for p in ps)


def describe(c, atom, a, jd):
    try:
        if atom == 'in_house':
            ps = [p for p in E.refs(c, a[0]) if E.evaluate(c, {'in_house': [p, a[1]] + list(a[2:])}, jd)]
            base = '' if len(a) < 3 or a[2] == 'lagna' else f' from {a[2] if a[2] != "moon" else "the Moon"}'
            return f'{ref_name(c, a[0])}: {where(c, ps)}{base}' if base == '' else f'{", ".join(ps)} in house(s) {a[1]}{base}'
        if atom == 'in_sign':
            ps = [p for p in E.refs(c, a[0]) if c.signs[p] in a[1]]
            return '; '.join(f'{p} in {SIGNS[c.signs[p]]}' for p in ps)
        if atom == 'dignity':
            ps = [p for p in E.refs(c, a[0]) if c.dig[p] in a[1]]
            return '; '.join(f'{p} {c.dig[p].replace("_", " ")} in {SIGNS[c.signs[p]]}' for p in ps)
        if atom == 'conjunct':
            return f'{ref_name(c, a[0])} together with {ref_name(c, a[1])}'
        if atom == 'aspects':
            return f'{ref_name(c, a[0])} aspects {a[1] if str(a[1]).startswith("house") else ref_name(c, a[1])}'
        if atom in ('strong', 'weak'):
            ps = sorted(E.refs(c, a))
            return '; '.join(f'{p} {atom} (Shadbala {c.shadbala[p]["ratio"]:.2f})' for p in ps if p in c.shadbala)
        if atom == 'combust':
            return f'{ref_name(c, a)} combust'
        if atom == 'lagna_sign':
            return f'{SIGNS[c.lagna]} rising'
        if atom == 'nakshatra':
            return 'the Moon\'s nakshatra'
        if atom == 'is':
            return f'{ref_name(c, a[0])} is {ref_name(c, a[1])}'
        if atom == 'parivartana':
            return f'exchange of the {ORD(a[0])} and {ORD(a[1])} lords'
        if atom == 'nabhasa':
            return f'{a} yoga'
        if atom.startswith('kp_') and c.kp is not None:
            k = c.kp
            if atom == 'kp_csl':
                sl = k.csl[a[0]]
                return f'KP: the {ORD(a[0])} cusp sub lord {sl} signifies houses {sorted(k.signified(sl))}'
            if atom == 'kp_csl_star':
                sl = k.csl[a[0]]
                return f'KP: the {ORD(a[0])} cusp sub lord {sl} sits in the star of {k.star[sl]} (signifying {sorted(k.signified(k.star[sl]))})'
            if atom == 'kp_csl_of':
                return f'KP: the {ORD(a[0])} cusp sub lord is {k.csl[a[0]]}'
            if atom == 'kp_sig':
                return f'KP: {a[0]} signifies houses {sorted(k.signified(a[0] if a[0] != "lagna_csl" else k.csl[1]))}'
            if atom == 'kp_planet_house':
                return f'KP: {a[0]} in Placidus house {k.house[a[0]]}'
            return f'KP condition {atom}'
        if atom == 'kc_natal':
            return f'Kalachakra birth amsa: {SIGNS[c.kc["amsa"]] if isinstance(c.kc.get("amsa"), int) else c.kc.get("amsa")}'
        if atom == 'argala':
            return f'unobstructed argala on house {a[0]}'
        if atom == 'special_in_house':
            x = c.special.get(a[0])
            return f'{a[0]} in house {(int(x // 30) - c.lagna) % 12 + 1}' if x is not None else a[0]
        if atom == 'upagraha_with':
            return f'upagraha {a[0]} with {a[1]}' if isinstance(a, list) else 'an upagraha conjunction'
        if atom == 'from_pada':
            return f'{ref_name(c, a[1])} in house(s) {a[2]} from the pada of house {a[0]}'
        if atom == 'pada_in_sign':
            return f'the pada of house {a[0]} in {SIGNS[c.pada(a[0])]}'
        if atom == 'n_in_house':
            return f'{a[2]}+ planets in houses {a[1]}'
        if atom == 'moon_phase':
            return f'Moon {a}'
        if atom == 'tithi':
            return 'birth tithi'
        if atom == 'vargottama':
            return f'{ref_name(c, a)} vargottama'
        if atom == 'pd_vaiseshika':
            return f'{ref_name(c, a[0])} good in {a[1]}-{a[2]} vargas'
        if atom == 'pd_santana':
            return 'santana tithi'
        if atom == 'pd_ayu_class':
            return f'three-pair longevity: {a}'
        if atom == 'special_with':
            return f'{a[0]} with {ref_name(c, a[1])}'
        if atom == 'ayu_class':
            return f'longevity class {a}'
        if atom in ('dasha', 'kp_dasha', 'transit', 'gochara'):
            return f'{atom} condition on the date'
    except Exception:
        pass
    return atom.replace('_', ' ')


def explain(c, cond, jd=None, yogas=None, out=None):
    """True atoms of the condition (only the branches that actually hold)."""
    out = [] if out is None else out
    (k, a), = cond.items()
    if k == 'all':
        for x in a:
            explain(c, x, jd, yogas, out)
    elif k == 'any':
        for x in a:
            try:
                if E.evaluate(c, x, jd, yogas):
                    explain(c, x, jd, yogas, out)
                    break
            except Exception:
                continue
    elif k == 'not':
        pass
    else:
        d = describe(c, k, a, jd)
        if d and d not in out:
            out.append(d)
    return out
