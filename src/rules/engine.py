"""
src/rules/engine.py — evaluate classical rules (JSON condition trees) on a chart and a date.

Chart(s)                 natal facts for one person (sidereal Lahiri, whole-sign houses), computed once
evaluate(chart, cond, jd)  True/False; jd=None for natal-only conditions
validate_rule(rule)      schema and condition check (used on every rule before it is stored or tested)
load_rules(path)         read a rules/*.jsonl file (validated)
RuleFeaturizer(rules)    one feature per timing rule (1 = fires on the date) for the study's model harness

Condition language: see docs/rule_engine_design.md.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from src import features as F
from src import models as Mo
from src import rao as R
from src import strength as S
from src.rules import bphs_dasha as BD
from src.rules import bphs_av as BAV
from src.rules import bphs_core as BC
from src.rules import bphs_rays as BR
from src.rules import bphs_time as BT
from src.rules import bphs_strength as BS
from src.rules import bphs_functional as BF
from src.rules import bphs_nabhasa as BN
from src.rules import bphs_ayu as BA
from src.rules import bphs_avastha as BV
from src.rules import pd_varga as PV
from src.rules import pd_av as PAV
from src.rules import kp_core as KP

GRAHAS = S.GRAHAS
ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'rules'
EVENTS = {'Marriage', 'Divorce', 'Birth_Child', 'Career_Peak', 'Prize', 'Job_Start', 'Job_End', 'Arrest', 'Trial',
          'Illness', 'Accident', 'Death', 'Death_of_relative', 'Death of father', 'Death of mother', 'Death of mate',
          'Relationship_Begin', 'Relationship_End',
          # grouped targets for rules that only say a period is auspicious / inauspicious
          'Positive', 'Negative'}
POSITIVE_EVENTS = ['Marriage', 'Birth_Child', 'Career_Peak', 'Prize', 'Job_Start', 'Relationship_Begin']
NEGATIVE_EVENTS = ['Divorce', 'Illness', 'Accident', 'Arrest', 'Trial', 'Job_End', 'Death', 'Death_of_relative', 'Death of father',
                   'Death of mother', 'Death of mate', 'Relationship_End']
DIGNITY_CLASSES = set(S.DIGNITY_SCORE)
ATOMS = {'in_house', 'in_sign', 'dignity', 'strong', 'weak', 'conjunct', 'aspects', 'associated', 'varga_in_house',
         'varga_dignity', 'is', 'combust', 'moon_phase', 'dasha', 'transit', 'yoga', 'kc', 'kc_natal', 'chara',
         'dasha_frac', 'dasha_elapsed', 'lagna_sign', 'varga_in_sign', 'av_point', 'av_transit', 'av_year', 'av_ayu', 'sav_transit', 'rays_total', 'sud', 'age', 'gender', 'tithi', 'tithi_part', 'nakshatra', 'gandanta', 'upagraha_with', 'special_in_house', 'day_birth', 'shadbala', 'ishta_gt_kashta', 'from_pada', 'pada_from_pada', 'argala', 'pada_in_sign', 'ul_lord_dignity', 'from_kk', 'kk_in_sign', 'yogakaraka_natal', 'functional', 'nabhasa', 'vargottama', 'n_dignity', 'n_aspecting', 'pindayu_near', 'ayu_class', 'in_ayu_span', 'n_in_house', 'avastha', 'n_in_house_from', 'pd_vaiseshika', 'pd_weak_vargas', 'pd_lagna_krura60', 'moon_avastha12', 'lagna_hora', 'deeptadi', 'parivartana', 'retro', 'planet_nakshatra', 'conj_orb', 'santana_tithi_kerala', 'lagna_vargottama', 'n_aspecting_house', 'pd_trimsamsa_lord', 'pd_sphuta', 'pd_santana', 'dasha_sphuta_nak', 'pd_ayu_class', 'moon_mrityubhaga', 'transit_sphuta', 'transit_conj', 'transit_point', 'dasha_lord_transit', 'moon_from_dasha_lord', 'sun_on_dasha_sign', 'md_index', 'pd_av_star', 'pd_av_sign', 'pd_av_transit', 'pd_sav', 'pd_sav_transit', 'pd_av_year', 'pd_sav_cmp', 'gochara', 'tnak', 'latta', 'special_with', 'n_in_one_sign', 'gochara_set', 'pd_drek_lord', 'kp_csl', 'kp_dasha', 'kp_sig', 'kp_csl_star', 'kp_badhaka_dasha', 'kp_transit_star', 'kp_csl_lordship', 'kp_cusp_chain_dasha', 'kp_cusp_star_lordship', 'kp_majority_8_12', 'kp_lord_dasha', 'kp_jup_on_dasha_sign', 'kp_no_cure', 'kp_planet_house', 'kp_planet_sig_both', 'kp_sig_link', 'kp_csl_of', 'kp_cssl', 'kp_dba_cover', 'kp_csl_starlord_house', 'kp_period_star_is', 'kp_fortuna', 'kp_csl_star_combust', 'kp_csl_dasha', 'kp_star_sub', 'kp_sub_sig', 'kp_lord_in_star_of_lord', 'kp_csl_retro', 'kp_cusp_lords', 'kp_csl_pos', 'kp_cusplord_sub', 'kp_csl_starlord_sign', 'kp_occ_in_star_of_lord', 'kp_dasha_planet', 'kp_csl_node', 'kp_csl_in_star_of_planet', 'kp_dasha_sig_pair', 'kp_lagna_csl_starlord_sign', 'kp_period_sub_sig', 'kp_punarphoo', 'kp_csl_dual', 'kp_csl_chain_nodes_sat', 'kp_transit_sl', 'kp_transit_dba_point', 'retro_transit', 'kp_node_in_badhaka_star', 'kp_csl_star_badhaka_maraka', 'deg_in_sign', 'navamsa_lagna', 'sar_rays_total', 'moola', 'moola_start_transit', 'av_own_natal', 'sar_av_transit'}
AV_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
# natural benefics / malefics used for "benefic sign" etc. — PENDING replacement by vol. 1 ch. 3's definitions
NAT_BEN, NAT_MAL = {'Jupiter', 'Venus', 'Mercury', 'Moon'}, {'Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'}
KC_FIELDS = {'amsa', 'pos', 'sign', 'prev', 'motion', 'cycle', 'house', 'lord_nature', 'holds', 'holds_n',
             'holds_dignity', 'role', 'dj_holds_n', 'dj_both', 'ad_sign', 'ad_lord'}
KC_NATAL_FIELDS = {'amsa', 'cycle', 'dj_holds_n', 'dj_both', 'deha_holds', 'jeeva_holds'}
SIGN_CTX_FIELDS = {'sign', 'house', 'index', 'lord_nature', 'holds', 'holds_n', 'holds_dignity', 'empty', 'from_holds',
                   'from_dignity', 'from_combust', 'lord_in', 'lord_dignity', 'lord_aspected_by', 'lord_with',
                   'holds_own_lord', 'lord_sign_nature', 'lord_aspects'}
CHARA_FIELDS = SIGN_CTX_FIELDS | {'ad_' + f for f in SIGN_CTX_FIELDS}
VARGAS = {'D9', 'D7', 'D10', 'D12'}


def _sign(lon: float) -> int:
    return int((lon % 360) // 30)


def d7_sign(lon: float) -> int:
    s, part = _sign(lon), int(((lon % 360) % 30) // (30 / 7))
    return ((s if s % 2 == 0 else (s + 6) % 12) + part) % 12


def d12_sign(lon: float) -> int:
    s, part = _sign(lon), int(((lon % 360) % 30) // 2.5)
    return (s + part) % 12


VARGA_FN = {'D9': F.d9_sign, 'D7': d7_sign, 'D10': F.d10_sign, 'D12': d12_sign}


class Chart:
    def __init__(self, s: dict):
        st = S.natal_strength(s)
        self.s, self.st = s, st
        self.lon, self.signs, self.lagna = st['lon'], st['signs'], st['lagna']
        self.moon_sign = self.signs['Moon']
        self.bjd = s['birth_jd']
        self.dig = {p: BC.dignity(p, self.lon[p], self.signs) for p in GRAHAS}       # BPHS vol. 1 ch. 3
        self.benefics, self.malefics = BC.benefics_malefics(self.lon, self.signs)    # v. 11, per chart
        ri = S.PLANET_FEATURES.index('retro')
        self.combust = {p: BC.combust(p, self.lon, bool(st['vec'][p][ri])) for p in GRAHAS}   # vol. 1 ch. 8 notes
        asc = st['asc']
        self.varga = {v: ({p: fn(self.lon[p]) for p in GRAHAS}, fn(asc)) for v, fn in VARGA_FN.items()}
        self._date: dict[float, dict] = {}

    # facts
    def lord(self, house: int, lagna: int | None = None) -> str:
        return F.SIGN_LORD[((self.lagna if lagna is None else lagna) + house - 1) % 12]

    def house_of(self, p: str, base: str = 'lagna') -> int:
        ref = self.lagna if base == 'lagna' else self.moon_sign
        return (self.signs[p] - ref) % 12 + 1

    def date(self, jd: float) -> dict:
        if jd not in self._date:
            v = BD.vimshottari(self.lon['Moon'], self.bjd, jd)
            self._date[jd] = {'MD': v['MD']['lord'], 'AD': v['AD']['lord'], 'PD': v['PD']['lord'], 'SD': v['SD']['lord'], 'PR': v['PR']['lord'], 'V': v,
                              'transit': R.transit_signs(jd),
                              'KC': BD.kalachakra(self.lon['Moon'], self.bjd, jd),
                              # exaltation +/-1 of ch. 48 v. 164-165 waits for vol. 1 ch. 3's exaltation signs
                              'CH': BD.chara(self.signs, self.lagna, self.bjd, jd, exalt=None)}
        return self._date[jd]

    @property
    def kc(self) -> dict:
        if not hasattr(self, '_kc'):
            self._kc = BD.kalachakra_natal(self.lon['Moon'])
        return self._kc

    @property
    def av(self) -> 'BAV.AV':
        if not hasattr(self, '_av'):
            self._av = BAV.AV({p: self.signs[p] for p in AV_PLANETS}, self.lagna)
        return self._av

    @property
    def kp(self) -> 'KP.KPChart | None':
        """KP chart (Krishnamurti ayanamsa, Placidus) from the birth moment and place; 'kp_birth' overrides them (the
        mismatched-chart null passes a donor's birth data)."""
        if not hasattr(self, '_kp'):
            b = self.s.get('kp_birth') or (self.bjd, self.s.get('lat'), self.s.get('lon'))
            try:
                self._kp = KP.KPChart(*b) if b[1] is not None and b[2] is not None else None
            except Exception:                    # Placidus is undefined near the poles (|lat| > ~66 deg): no KP chart
                self._kp = None
        return self._kp

    def kp_date(self, jd: float) -> dict:
        key = ('kp', jd)
        if key not in self._date:
            self._date[key] = KP.kp_dasha(self.kp.lon['Moon'], self.bjd, jd)
        return self._date[key]

    @property
    def pd_av(self) -> 'PAV.PDAV':
        if not hasattr(self, '_pd_av'):
            self._pd_av = PAV.PDAV({p: self.signs[p] for p in AV_PLANETS}, self.lagna)
        return self._pd_av

    @property
    def special(self) -> dict[str, float | None]:
        """Longitudes of the non-luminous bodies (vol. 1 ch. 3 v. 61-74)."""
        if not hasattr(self, '_special'):
            sun = self.lon['Sun']
            dhuma = (sun + 133 + 20 / 60) % 360
            vyati = (360 - dhuma) % 360
            pari = (vyati + 180) % 360
            indra = (360 - pari) % 360
            lat, lon = self.s.get('lat'), self.s.get('lon')
            self._special = {'Dhuma': dhuma, 'Vyatipata': vyati, 'Parivesha': pari, 'Indrachapa': indra,
                             'Upaketu': (indra + 16 + 40 / 60) % 360,
                             'Gulika': BT.gulika(self.bjd, lat, lon) if lat is not None else None,
                             'Pranapada': BT.pranapada(self.bjd, lat, lon, sun) if lat is not None else None,
                             'Mandi': BT.pd_mandi(self.bjd, lat, lon) if lat is not None else None}
        return self._special

    @property
    def karakas(self) -> dict[str, str]:
        """Seven chara karakas (vol. 1 ch. 34 v. 3-17): AK, AmK, BK, MK, PiK, PK, GK(jaati), DK - with seven planets
        the 'stree karaka' (DK) is the last; Matri and Putra karaka are one in the seven-karaka scheme (notes p. 447)."""
        if not hasattr(self, '_karakas'):
            order = sorted(('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'), key=lambda p: -(self.lon[p] % 30))
            names = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
            self._karakas = dict(zip(names, order))
            self._karakas['PiK'] = self._karakas['PK']
        return self._karakas

    @property
    def karakamsa(self) -> int:
        """Navamsa sign of the Atmakaraka (vol. 1 ch. 35)."""
        return self.varga['D9'][0][self.karakas['AK']]

    def pada(self, house: int) -> int:
        """Arudha of a house (vol. 1 ch. 31): sign index."""
        hs = (self.lagna + house - 1) % 12
        return BC.arudha(hs, self.signs[F.SIGN_LORD[hs]])

    @property
    def shadbala(self) -> dict:
        if not hasattr(self, '_sb'):
            self._sb = BS.shadbala(self)
        return self._sb

    @property
    def day(self) -> dict | None:
        if not hasattr(self, '_day'):
            lat, lon = self.s.get('lat'), self.s.get('lon')
            self._day = BT.day_info(self.bjd, lat, lon) if lat is not None else None
        return self._day

    def in_sign(self, s: int) -> set[str]:
        return {p for p in GRAHAS if self.signs[p] == s}


# ── references ───────────────────────────────────────────────────────────────

def refs(c: Chart, ref) -> set[str]:
    if isinstance(ref, list):
        if set(ref) == NAT_MAL or ref == ['malefics']:
            return set(c.malefics)
        if set(ref) == NAT_BEN or ref == ['benefics']:
            return set(c.benefics)
        return set().union(*(refs(c, r) for r in ref)) if ref else set()
    if ref == 'malefics':
        return set(c.malefics)
    if ref == 'marakas':                      # vol. 1 ch. 46 v. 3-5
        lords = {c.lord(2), c.lord(7)}
        mal_in = {p for p in c.malefics if c.house_of(p) in (2, 7)}
        mal_with = {p for p in c.malefics if any(c.signs[p] == c.signs[q] for q in lords if q != p)}
        return lords | mal_in | mal_with
    if ref == 'benefics':
        return set(c.benefics)
    if ref in GRAHAS:
        return {ref}
    kind, _, arg = str(ref).partition(':')
    if kind == 'lord':
        return {c.lord(int(arg))}
    if kind == 'occupants':
        return {p for p in GRAHAS if c.house_of(p) == int(arg)}
    if kind == 'aspecting':
        t = (c.lagna + int(arg) - 1) % 12
        return {p for p in GRAHAS if _aspects_sign(p, c.signs[p], t)}
    if kind == 'dispositor':
        return {F.SIGN_LORD[c.signs[p]] for p in refs(c, arg)}
    if kind == 'with':                       # planets in the same sign as the referenced planet(s)
        base = refs(c, arg)
        return {p for p in GRAHAS if p not in base and any(c.signs[p] == c.signs[q] for q in base)}
    if kind == 'assoc':                      # conjunct, aspecting either way, or in sign exchange with it
        base = refs(c, arg)
        return {p for p in GRAHAS if p not in base and any(_associated(c, p, q) for q in base)}
    if kind == 'karaka':                     # vol. 1 ch. 34 v. 3-17: chara karakas by degrees within the sign
        return {c.karakas[arg]}
    if kind == 'd9lord':
        return {F.SIGN_LORD[(c.varga['D9'][1] + int(arg) - 1) % 12]}
    if kind == 'exaltlord':                  # lord of the referenced planet's exaltation sign
        return {F.SIGN_LORD[F.EXALT[p]] for p in refs(c, arg)}
    if kind == 'lordfrom':                   # 'lordfrom:<ref>:N' lord of the Nth sign from a planet
        ref_, n = arg.rsplit(':', 1)
        return {F.SIGN_LORD[(c.signs[p] + int(n) - 1) % 12] for p in refs(c, ref_)}
    if kind == 'strongest':                  # 'strongest:a|b|c' the planet with the highest Shadbala ratio
        cand = set().union(*(refs(c, x) for x in arg.split('|')))
        return {max(sorted(cand), key=lambda q: c.shadbala[q]['ratio'] if q in c.shadbala else 0)}
    if kind in ('drek22', 'drek22m', 'drek1'):  # lord of the 22nd drekkana from the Lagna / Moon, of the rising one
        base = c.lon['Moon'] if kind == 'drek22m' else c.st['asc']
        return {F.SIGN_LORD[PV.varga_sign('D3', base + (0 if kind == 'drek1' else 210))]}
    if kind == 'weakest':                    # 'weakest:a|b|c' lowest Shadbala ratio
        cand = set().union(*(refs(c, x) for x in arg.split('|')))
        return {min(sorted(cand), key=lambda q: c.shadbala[q]['ratio'] if q in c.shadbala else 9)}
    if kind == 'naklord':                    # Vimshottari lord of the Nth nakshatra counted from the natal Moon's
        k = int((c.lon['Moon'] % 360) // (360 / 27))
        return {F.DASHA_LORDS[(k + int(arg) - 1) % 9]}
    if kind in ('gulikalord', 'mandilord'):  # lord of the sign Gulika (BPHS) / Mandi (Phaladeepika) occupies
        g = c.special.get('Gulika' if kind == 'gulikalord' else 'Mandi')
        return {F.SIGN_LORD[int((g % 360) // 30)]} if g is not None else set()
    if kind == 'mlord':                      # lord of the Nth house from the Moon
        return {F.SIGN_LORD[(c.moon_sign + int(arg) - 1) % 12]}
    if kind == 'navlord':                    # lord of the navamsa sign the referenced planet(s) occupy
        return {F.SIGN_LORD[c.varga['D9'][0][p]] for p in refs(c, arg)}
    if kind == 'pd_profession':              # Phaladeepika ch. V v. 1: navamsa lord of the 10th lord from the
        return {_pd_profession(c)}           # strongest of Lagna, Moon, Sun
    raise ValueError(f'unknown planet reference {ref!r}')


def _sign_dignity(p: str, s: int) -> str:
    """Sign-level dignity of a planet placed in sign s (transits): exalted, own, debilitated, friend, enemy, neutral
    (natural friendship; nodes: exaltation/debilitation only)."""
    if s == F.EXALT.get(p):
        return 'exalted'
    if s == F.DEBIL.get(p):
        return 'debilitated'
    if F.SIGN_LORD[s] == p:
        return 'own'
    if p not in BC.NAT:
        return 'neutral'
    return BC.natural(p, F.SIGN_LORD[s])


# Phaladeepika XXVI v. 2-8 (1961 pp. 345-348): good houses from the natal Moon and their vedha (obstruction) houses;
# the exempt pair never obstructs. Rahu and Ketu like the Sun (v. 2).
GOCHARA_VEDHA = {
    'Sun': ({3: 9, 6: 12, 10: 4, 11: 5}, 'Saturn'), 'Rahu': ({3: 9, 6: 12, 10: 4, 11: 5}, None),
    'Ketu': ({3: 9, 6: 12, 10: 4, 11: 5}, None),
    'Moon': ({7: 2, 1: 5, 6: 12, 11: 8, 10: 4, 3: 9}, 'Mercury'),
    'Mars': ({3: 12, 11: 5, 6: 9}, None), 'Saturn': ({3: 12, 11: 5, 6: 9}, 'Sun'),
    'Mercury': ({2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12}, 'Moon'),
    'Jupiter': ({2: 12, 11: 8, 9: 10, 5: 4, 7: 3}, None),
    'Venus': ({1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 6, 12: 3}, None)}
LATTA = {'Sun': 12, 'Mars': 3, 'Jupiter': 6, 'Saturn': 8, 'Venus': -5, 'Mercury': -7, 'Rahu': -9, 'Moon': -22}


def _pd_profession(c: Chart) -> str:
    # strength of the Lagna = its lord's Shadbala ratio (engine convention; the book says 'whichever is strongest')
    cand = [(c.shadbala[c.lord(1)]['ratio'] if c.lord(1) in c.shadbala else 0, c.lagna),
            (c.shadbala['Moon']['ratio'], c.moon_sign), (c.shadbala['Sun']['ratio'], c.signs['Sun'])]
    base = max(cand, key=lambda x: x[0])[1]
    lord10 = F.SIGN_LORD[(base + 9) % 12]
    return F.SIGN_LORD[c.varga['D9'][0][lord10]]


def _target_signs(c: Chart, target) -> set[int]:
    if isinstance(target, str) and target.startswith('house:'):
        return {(c.lagna + int(target[6:]) - 1) % 12}
    if isinstance(target, str) and target.startswith('moon_house:'):
        return {(c.moon_sign + int(target[11:]) - 1) % 12}
    if isinstance(target, str) and target.startswith('sign:'):
        return {int(target[5:])}
    if isinstance(target, str) and target.startswith('from:'):      # 'from:<planet ref>:N' = Nth sign from a planet
        ref_, n = target[5:].rsplit(':', 1)
        return {(c.signs[p] + int(n) - 1) % 12 for p in refs(c, ref_)}
    if isinstance(target, str) and target.startswith('owned:'):     # the signs a planet owns
        return {s for p in refs(c, target[6:]) for s in range(12) if F.SIGN_LORD[s] == p}
    if isinstance(target, str) and target.startswith('navfrom:'):   # Nth sign from a planet's navamsa sign
        ref_, n = target[8:].rsplit(':', 1)
        return {(c.varga['D9'][0][p] + int(n) - 1) % 12 for p in refs(c, ref_)}
    return {c.signs[p] for p in refs(c, target)}


def _aspects_sign(planet: str, frm: int, to: int) -> bool:
    """Full planetary aspect as BPHS vol. 1 ch. 28 v. 2-5 gives it (no special aspects for Rahu/Ketu)."""
    return frm != to and BC.full_aspect(planet, frm, to)


def _associated(c: 'Chart', p: str, q: str) -> bool:
    if p == q:
        return False
    sp, sq = c.signs[p], c.signs[q]
    return (sp == sq or _aspects_sign(p, sp, sq) or _aspects_sign(q, sq, sp)
            or (F.SIGN_LORD[sp] == q and F.SIGN_LORD[sq] == p))


def _kc_natal_match(c: 'Chart', a: dict) -> bool:
    k = c.kc
    if 'amsa' in a and k['amsa'] not in a['amsa']:
        return False
    if 'cycle' in a and k['savya'] != (a['cycle'] == 'savya'):
        return False
    if 'dj_holds_n' in a:                      # at least n planets of the ref in the Deha or Jeeva sign
        ref, n = a['dj_holds_n']
        if len(refs(c, ref) & (c.in_sign(k['deha']) | c.in_sign(k['jeeva']))) < n:
            return False
    if 'dj_both' in a:                         # both the Deha and the Jeeva sign hold a planet of the ref
        ps = refs(c, a['dj_both'])
        if not (ps & c.in_sign(k['deha']) and ps & c.in_sign(k['jeeva'])):
            return False
    for f, sign in (('deha_holds', k['deha']), ('jeeva_holds', k['jeeva'])):
        if f in a and not refs(c, a[f]) & c.in_sign(sign):
            return False
    return True


def _kc_match(c: 'Chart', k: dict, a: dict) -> bool:
    s = k['sign']
    if 'pos' in a and k['pos'] not in a['pos']:
        return False
    if 'sign' in a and s not in a['sign']:
        return False
    if 'prev' in a and k['prev'] not in a['prev']:
        return False
    if 'motion' in a and k['motion'] not in a['motion']:
        return False
    if 'ad_sign' in a and k['ad_sign'] not in a['ad_sign']:
        return False
    if 'ad_lord' in a and F.SIGN_LORD[k['ad_sign']] not in refs(c, a['ad_lord']):
        return False
    if 'house' in a and (s - c.lagna) % 12 + 1 not in a['house']:
        return False
    if 'lord_nature' in a and (F.SIGN_LORD[s] in c.benefics) != (a['lord_nature'] == 'benefic'):
        return False
    if 'holds' in a and not refs(c, a['holds']) & c.in_sign(s):
        return False
    if 'holds_n' in a and len(refs(c, a['holds_n'][0]) & c.in_sign(s)) < a['holds_n'][1]:
        return False
    if 'holds_dignity' in a and not any(c.dig[p] in a['holds_dignity'] for p in c.in_sign(s)):
        return False
    if 'role' in a:
        roles = {'deha': {c.kc['deha']}, 'jeeva': {c.kc['jeeva']}, 'either': {c.kc['deha'], c.kc['jeeva']}}
        if s not in roles[a['role']]:
            return False
    return True


GHATI_DEG_TITHI = 12 / 60          # a tithi is 12 deg of elongation, taken as about 60 ghatis
GHATI_DEG_NAK = (360 / 27) / 60    # a nakshatra traversed in about 60 ghatis
LAGNA_GHATI = 0.25                 # ch. 94 v. 4: half a ghati astride a sign junction ~ 0.25 deg of Lagna per side


def _tithi(c: 'Chart') -> tuple[int, float]:
    e = (c.lon['Moon'] - c.lon['Sun']) % 360
    return int(e // 12) + 1, (e % 12) / 12


def _gandanta(c: 'Chart', kind: str) -> bool:
    """Ch. 94 v. 2-4 (book p. 764-765), with ghatis converted at the mean rate of each quantity (logged):
    tithi - last 2 ghatis of tithis 5, 10, 15 (Purna) and first 2 of 6, 11, 1 (Nanda) of either fortnight;
    nakshatra - last 2 ghatis of Revati, Ashlesha, Jyeshtha and first 2 of Ashwini, Magha, Moola;
    lagna - half a ghati either side of Pisces/Aries, Cancer/Leo, Scorpio/Sagittarius."""
    if kind == 'tithi':
        e = (c.lon['Moon'] - c.lon['Sun']) % 360
        for end in (5, 10, 15, 20, 25, 30):                    # ends of tithis 5,10,15 in both pakshas
            d = (e - end * 12) % 360
            if d < 2 * GHATI_DEG_TITHI or d > 360 - 2 * GHATI_DEG_TITHI:
                return True
        return False
    if kind == 'nakshatra':
        x = c.lon['Moon'] % 360
        for k in (0, 9, 18):                                   # Ashwini, Magha, Moola start = Revati, Ashlesha, Jyeshtha end
            d = (x - k * 360 / 27) % 360
            if d < 2 * GHATI_DEG_NAK or d > 360 - 2 * GHATI_DEG_NAK:
                return True
        return False
    asc = c.st['asc'] % 360
    return any(min((asc - b) % 360, (b - asc) % 360) < LAGNA_GHATI for b in (0, 120, 240))


def _yogakarakas(c: 'Chart') -> set[str]:
    good = {p for p in ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn')
            if c.dig[p] in ('exalted', 'moolatrikona', 'own', 'friend', 'great_friend')}
    out = {p for p in good if c.house_of(p) in (1, 4, 7, 10)}
    for p in good:
        for q in good:
            if p != q and ((c.signs[q] - c.signs[p]) % 12 + 1) in (1, 4, 7, 10):
                out |= {p, q}
    return out if len(out) >= 2 else set()


def _argala(c: 'Chart', base: int, kind: str = 'any') -> bool:
    """Vol. 1 ch. 33 v. 2-9: planets in the 4th, 2nd, 11th (and 5th) from a sign form argala, obstructed by those in
    the 10th, 12th, 3rd (and 9th) unless the obstructors are fewer; three or more malefics in the 3rd form vipreeta
    argala, unobstructed; Rahu and Ketu are counted in reverse. kind: 'any' | 'benefic' | 'malefic'."""
    def house_of(p):
        s = c.signs[p]
        return (base - s) % 12 + 1 if p in ('Rahu', 'Ketu') else (s - base) % 12 + 1
    pos = {p: house_of(p) for p in GRAHAS}
    pick = (lambda p: True) if kind == 'any' else (lambda p: p in c.benefics) if kind == 'benefic' else (lambda p: p in c.malefics)
    for a_h, o_h in ((4, 10), (2, 12), (11, 3), (5, 9)):
        causing = [p for p in GRAHAS if pos[p] == a_h]
        if causing and any(pick(p) for p in causing) and len(causing) > len([p for p in GRAHAS if pos[p] == o_h]):
            return True
    mal3 = [p for p in GRAHAS if pos[p] == 3 and p in c.malefics]
    return len(mal3) >= 3 and kind in ('any', 'malefic')


def _strong(c: 'Chart', p: str) -> bool:
    """Seven planets: Shadbala ratio >= 1 and not combust; Rahu/Ketu (no Shadbala in the book): dignity friend or
    better."""
    sb = c.shadbala
    if p in sb:
        return sb[p]['ratio'] >= 1 and not c.combust[p]
    return S.DIGNITY_SCORE[c.dig[p]] >= 2


def _sign_ctx_match(c: 'Chart', s: int, index: int, a: dict) -> bool:
    """A running sign dasha (or antardasha) sign s against the fields of a chara condition."""
    def nth(n):                                    # the sign n houses from s
        return (s + n - 1) % 12
    lord = F.SIGN_LORD[s]
    checks = {
        'sign': lambda v: s in v,
        'house': lambda v: (s - c.lagna) % 12 + 1 in v,
        'index': lambda v: index in v,
        'lord_nature': lambda v: (lord in c.benefics) == (v == 'benefic'),
        'holds': lambda v: bool(refs(c, v) & c.in_sign(s)),
        'holds_n': lambda v: len(refs(c, v[0]) & c.in_sign(s)) >= v[1],
        'holds_dignity': lambda v: any(c.dig[p] in v for p in c.in_sign(s)),
        'empty': lambda v: (not c.in_sign(s)) == v,
        'from_holds': lambda v: any(refs(c, v[1]) & c.in_sign(nth(n)) for n in v[0]),
        'from_dignity': lambda v: any(c.dig[p] in v[1] for n in v[0] for p in c.in_sign(nth(n))),
        'from_combust': lambda v: any(c.combust[p] for n in v for p in c.in_sign(nth(n))),
        'lord_in': lambda v: (c.signs[lord] - s) % 12 + 1 in v,
        'lord_dignity': lambda v: c.dig[lord] in v,
        'lord_aspected_by': lambda v: any(_aspects_sign(p, c.signs[p], c.signs[lord]) for p in refs(c, v)),
        'lord_with': lambda v: any(p != lord and c.signs[p] == c.signs[lord] for p in refs(c, v)),
        'holds_own_lord': lambda v: (c.signs[lord] == s) == v,
        'lord_sign_nature': lambda v: (F.SIGN_LORD[c.signs[lord]] in c.benefics) == (v == 'benefic'),
        'lord_aspects': lambda v: _aspects_sign(lord, c.signs[lord], s) == v,
    }
    return all(checks[f](v) for f, v in a.items())


# ── evaluation ───────────────────────────────────────────────────────────────

def evaluate(c: Chart, cond: dict, jd: float | None = None, yogas: dict | None = None) -> bool:
    if 'all' in cond:
        return all(evaluate(c, x, jd, yogas) for x in cond['all'])
    if 'any' in cond:
        return any(evaluate(c, x, jd, yogas) for x in cond['any'])
    if 'not' in cond:
        return not evaluate(c, cond['not'], jd, yogas)
    (atom, a), = cond.items()
    if atom.startswith('w_'):                    # Western (Valens / Lilly) conditions: src/rules/west.py
        from src.rules import west as W
        return W.evaluate(c, atom, a, jd)
    if atom == 'in_house':
        base = a[2] if len(a) > 2 else 'lagna'
        if base in ('lagna', 'moon'):
            return any(c.house_of(p, base) in a[1] for p in refs(c, a[0]))
        # counted from another planet's sign (e.g. from the mahadasha lord); a planet is not 'from' itself
        bases = refs(c, base)
        return any((c.signs[p] - c.signs[b]) % 12 + 1 in a[1] for p in refs(c, a[0]) for b in bases if p != b)
    if atom == 'in_sign':
        return any(c.signs[p] in a[1] for p in refs(c, a[0]))
    if atom == 'dignity':
        return any(c.dig[p] in a[1] for p in refs(c, a[0]))
    if atom == 'strong':                         # vol. 1 ch. 29 v. 32-33: Shadbala at or above the requirement
        return any(_strong(c, p) for p in refs(c, a))
    if atom == 'weak':
        return any(not _strong(c, p) for p in refs(c, a))
    if atom == 'from_pada':                      # [N, ref, [houses]]: planets in houses counted from the pada of house N
        pada = c.pada(a[0])
        return any((c.signs[p] - pada) % 12 + 1 in a[2] for p in refs(c, a[1]))
    if atom == 'pada_from_pada':                 # [M, N, [houses]]: pada of house M in given houses from the pada of N
        return (c.pada(a[0]) - c.pada(a[1])) % 12 + 1 in a[2]
    if atom == 'argala':                         # vol. 1 ch. 33: [house N or 'pada:N', kinds] unobstructed argala
        base = c.pada(int(a[0][5:])) if str(a[0]).startswith('pada:') else (c.lagna + int(a[0]) - 1) % 12
        return _argala(c, base, a[1] if len(a) > 1 else 'any')
    if atom == 'ul_lord_dignity':                # dignity of the lord of the Upapada (pada of the 12th)
        return c.dig[F.SIGN_LORD[c.pada(12)]] in a
    if atom == 'from_kk':                        # [ref, [houses]]: navamsa positions counted from the Karakamsa
        vs = c.varga['D9'][0]
        return any((vs[p] - c.karakamsa) % 12 + 1 in a[1] for p in refs(c, a[0]))
    if atom == 'avastha':                        # [ref, [states]] Lajjitadi states (vol. 1 ch. 47 v. 11-18)
        return any(BV.lajjitadi(c, p) & set(a[1]) for p in refs(c, a[0]))
    if atom == 'pindayu_near':                   # death within a years of the Pindayu (vol. 1 ch. 45)
        if not hasattr(c, '_pinda'):
            c._pinda = BA.pindayu(c)['total']
        return abs((jd - c.bjd) / 365.25 - c._pinda) < a
    if atom == 'ayu_class':
        if not hasattr(c, '_ayucls'):
            c._ayucls = BA.ayu_class(c)
        return c._ayucls in a
    if atom == 'in_ayu_span':                    # age inside the span of the chart's longevity class (ch. 46 v. 10-14)
        if not hasattr(c, '_ayucls'):
            c._ayucls = BA.ayu_class(c)
        if c._ayucls is None:
            return False
        lo, hi = BA.SPAN[c._ayucls]
        return (lo <= (jd - c.bjd) / 365.25 < hi) == a
    if atom == 'n_in_house_from':                # [refs, houses, n, base 'lagna'|'moon'|planet]
        if a[3] in ('lagna', 'moon'):
            return sum(c.house_of(p, a[3]) in a[1] for p in refs(c, a[0])) >= a[2]
        b = next(iter(refs(c, a[3])))
        return sum((c.signs[p] - c.signs[b]) % 12 + 1 in a[1] for p in refs(c, a[0]) if p != b) >= a[2]
    if atom == 'pd_vaiseshika':                  # Phaladeepika III v. 7: [ref, lo, hi] good vargas of ten
        return any(a[1] <= PV.counts(p, c.lon[p])[0] <= a[2] for p in refs(c, a[0]) if p in PV.SEVEN)
    if atom == 'pd_weak_vargas':                 # Phaladeepika III v. 10: [ref, lo, hi] weak vargas of ten
        return any(a[1] <= PV.counts(p, c.lon[p])[1] <= a[2] for p in refs(c, a[0]) if p in PV.SEVEN)
    if atom == 'pd_lagna_krura60':               # Phaladeepika III v. 5, 11: Lagna in a Krura shashtyamsa
        return PV.krura_shashtyamsa(c.st['asc']) == bool(a)
    if atom == 'moon_avastha12':                 # Phaladeepika IV v. 12-16: [indices 1..12]
        return PV.moon_avastha12(c.lon['Moon']) in a
    if atom == 'lagna_hora':                     # Phaladeepika III v. 12: the hora rising is the Sun's / Moon's
        return PV.varga_sign('D2', c.st['asc']) == (4 if a == 'Sun' else 3)
    if atom == 'deeptadi':                       # Phaladeepika III v. 18-19: [ref, [states]]
        return any(PV.deeptadi(c, p) in a[1] for p in refs(c, a[0]))
    if atom == 'retro':                          # retrograde at birth (nodes always)
        ri = S.PLANET_FEATURES.index('retro')
        return any(p in ('Rahu', 'Ketu') or bool(c.st['vec'][p][ri]) for p in refs(c, a))
    if atom == 'santana_tithi_kerala':           # [lo, hi]: (5 x Moon - 5 x Lagna) mod 360 in [lo, hi) - KP R4 p. 224 (Kerala method)
        x = (5 * c.lon['Moon'] - 5 * c.st['asc']) % 360
        return a[0] <= x < a[1]
    if atom == 'conj_orb':                       # [ref, ref, degrees]: KP R3 p. 303 'close conjunction'
        return any(p != q and abs((c.lon[p] - c.lon[q] + 180) % 360 - 180) <= a[2] for p in refs(c, a[0]) for q in refs(c, a[1]))
    if atom == 'planet_nakshatra':               # [ref, [1..27]]
        return any(int((c.lon[p] % 360) // (360 / 27)) + 1 in a[1] for p in refs(c, a[0]))
    if atom == 'deg_in_sign':                    # [ref, sign 0-11, lo, hi]: the planet (or 'Lagna') in that sign between lo and hi degrees
        lons = [c.st['asc']] if a[0] == 'Lagna' else [c.lon[p] for p in refs(c, a[0])]
        return any(int(x % 360 // 30) == a[1] and a[2] <= x % 30 < a[3] for x in lons)
    if atom == 'navamsa_lagna':                  # [signs 0-11]: the sign rising in the navamsa chart
        return c.varga['D9'][1] in a
    if atom == 'lagna_vargottama':
        return (c.varga['D9'][1] == c.lagna) == bool(a)
    if atom == 'n_aspecting_house':              # [house, n]: at least n planets aspect the house (full aspects)
        tgt = (c.lagna + a[0] - 1) % 12
        return sum(_aspects_sign(q, c.signs[q], tgt) for q in GRAHAS) >= a[1]
    if atom == 'pd_trimsamsa_lord':              # [ref, [lords]] Phaladeepika III v. 4 / XI v. 6
        return any(PV.trimsamsa_lord(c.lon[p]) in a[1] for p in refs(c, a[0]))
    if atom == 'pd_sphuta':                      # [[refs], 'odd'|'even'|'mixed'] Phaladeepika XII v. 14
        return PV.sphuta_parity([c.lon[next(iter(refs(c, r)))] for r in a[0]]) == a[1]
    if atom == 'pd_santana':                     # [keys] any of bright/dark/amavasya/chidra/vishti/sthira (XII v. 15)
        st = PV.santana(c.lon['Moon'], c.lon['Sun'])
        return any((not st['bright']) if k == 'dark' else st[k] for k in a)
    if atom == 'dasha_sphuta_nak':               # [[refs], [levels]]: the dasha lord is the nakshatra lord of the sum
        if jd is None:                           # of the refs' longitudes (Phaladeepika XII v. 27)
            raise ValueError('dasha condition needs a date')
        x = sum(c.lon[next(iter(refs(c, r)))] for r in a[0]) % 360
        lord = F.DASHA_LORDS[int(x // (360 / 27)) % 9]
        d = c.date(jd)
        return any(d[level] == lord for level in a[1])
    if atom == 'pd_ayu_class':                   # Phaladeepika XIII v. 14 three pairs
        return PV.ayu_class(c) in (a if isinstance(a, list) else [a])
    if atom == 'moon_mrityubhaga':               # Phaladeepika XIII v. 10
        return PV.moon_mrityubhaga(c.lon['Moon']) == bool(a)
    if atom == 'transit_sphuta':                 # [planet, [refs]]: transiting planet in the sign of the sum of the refs'
        if jd is None:                           # natal longitudes (Phaladeepika XIII v. 18)
            raise ValueError('transit condition needs a date')
        x = sum(c.lon[next(iter(refs(c, r)))] for r in a[1]) % 360
        return c.date(jd)['transit'][a[0]] == int(x // 30)
    if atom == 'transit_conj':                   # [ref a, ref b]: the two (chart-referenced) planets transit one sign
        if jd is None:
            raise ValueError('transit condition needs a date')
        t = c.date(jd)['transit']
        return any(t[p] == t[q] for p in refs(c, a[0]) for q in refs(c, a[1]) if p != q)
    if atom == 'transit_point':                  # Phaladeepika XVII: [movers, [[coef, body], ..], kinds, trines, via_lord]
        if jd is None:
            raise ValueError('transit condition needs a date')
        movers, terms, kinds = a[0], a[1], a[2]
        trines, via = (a[3] if len(a) > 3 else True), (a[4] if len(a) > 4 else False)
        x = 0.0
        for coef, body in terms:
            if body == 'Lagna':
                v = c.st['asc']
            elif body == 'deg':                  # a constant offset in degrees
                v = 1.0
            elif body in ('Gulika', 'Mandi'):
                v = c.special.get(body)
            else:
                v = c.lon[next(iter(refs(c, body)))]
            if v is None:
                return False
            x += coef * v
        x %= 360
        signs = set()
        for k in kinds:
            s = PV.varga_sign({'rasi': 'D1', 'navamsa': 'D9', 'd12': 'D12', 'd3': 'D3'}[k], x)
            if s is not None:
                signs.add(s)
        if via:                                  # the sign occupied by the lord of that sign
            signs = {c.signs[F.SIGN_LORD[s]] for s in signs}
        if trines:
            signs |= {(s + 4) % 12 for s in signs} | {(s + 8) % 12 for s in signs}
        tr = c.date(jd)['transit']
        return any(tr[m] in signs for m in movers)
    if atom in ('dasha_lord_transit', 'moon_from_dasha_lord', 'sun_on_dasha_sign', 'md_index') and jd is None:
        raise ValueError('dasha condition needs a date')
    if atom == 'dasha_lord_transit':             # [level, 'lagna'|'natal'|'dignity', [houses or classes]]
        d = c.date(jd)
        p = d[a[0]]
        s = d['transit'][p]
        if a[1] == 'lagna':
            return (s - c.lagna) % 12 + 1 in a[2]
        if a[1] == 'natal':
            return (s - c.signs[p]) % 12 + 1 in a[2]
        return _sign_dignity(p, s) in a[2]
    if atom == 'moon_from_dasha_lord':           # [level, [houses from the dasha lord's transit sign], also_good_signs]
        d = c.date(jd)
        p = d[a[0]]
        tr = d['transit']
        ok = (tr['Moon'] - tr[p]) % 12 + 1 in a[1]
        if len(a) > 2 and a[2]:
            ok = ok or _sign_dignity(p, tr['Moon']) in ('exalted', 'own', 'friend')
        return ok
    if atom == 'sun_on_dasha_sign':              # [level, [classes]]: transiting Sun in that lord's exaltation/... sign
        d = c.date(jd)
        return _sign_dignity(d[a[0]], d['transit']['Sun']) in a[1]
    if atom == 'md_index':                       # the k-th Vimshottari mahadasha of life (1 = the one running at birth)
        v = c.date(jd)['V']
        k0 = F.DASHA_LORDS.index(BD.vimshottari(c.lon['Moon'], c.bjd, c.bjd + 1)['MD']['lord'])
        k = F.DASHA_LORDS.index(v['MD']['lord'])
        return (k - k0) % 9 + 1 in a
    if atom in ('pd_av_star', 'pd_av_sign', 'pd_av_transit', 'pd_sav_transit', 'pd_av_year') and jd is None:
        raise ValueError('transit condition needs a date')
    if atom == 'pd_av_star':                     # [planet, house, base, [movers]] Phaladeepika XXIV v. 1-3, 7, 13
        naks = c.pd_av.star(a[0], a[1], a[2])
        tr = c.date(jd)['transit']
        return any(tr['_nak'][m] in naks for m in a[3])
    if atom == 'pd_av_sign':                     # [planet, multiplier, [movers]] XXIV v. 5-6
        sg = c.pd_av.sign_mult(a[0], a[1])
        tr = c.date(jd)['transit']
        return any(tr[m] in sg for m in a[2])
    if atom == 'pd_av_transit':                  # [planet, lo, hi]: the planet transits a sign with lo..hi bindus in
        s = c.date(jd)['transit'][a[0]]          # its own (unreduced) AV - XXIII v. 11, 14
        return a[1] <= c.pd_av.bindus[a[0]][s] <= a[2]
    if atom == 'pd_sav_transit':                 # [planet, lo, hi]: transit over a sign whose Samudaya is lo..hi
        s = c.date(jd)['transit'][a[0]]
        return a[1] <= c.pd_av.sav[s] <= a[2]
    if atom == 'pd_av_year':                     # ['calamity', planet] / ['benefic']: the age-year of XXIV v. 41-43
        age = (jd - c.bjd) / 365.25
        ys = c.pd_av.calamity_years(a[1]) if a[0] == 'calamity' else [c.pd_av.benefic_year(sorted(c.benefics & set(AV_PLANETS)))]
        return any(y <= age < y + 1 for y in ys)
    if atom == 'pd_sav_cmp':                     # XXIV v. 38: Samudaya 11th > 10th, 12th < 11th, Lagna > 12th
        sv = c.pd_av.sav
        h = lambda n: sv[(c.lagna + n - 1) % 12]
        return h(11) > h(10) and h(12) < h(11) and h(1) > h(12)
    if atom in ('gochara', 'tnak', 'latta', 'gochara_set') and jd is None:
        raise ValueError('transit condition needs a date')
    if atom == 'gochara':                        # [planet, 'good'|'bad'|[houses], vedha_matters]
        tr = c.date(jd)['transit']
        pl, sel = a[0], a[1]
        h = (tr[pl] - c.moon_sign) % 12 + 1
        good, exempt = GOCHARA_VEDHA[pl]
        if sel == 'good':
            if h not in good:
                return False
            if len(a) > 2 and a[2]:
                vh = good[h]
                blockers = [q for q in GRAHAS if q not in (pl, exempt) and not (pl in ('Rahu', 'Ketu') and q in ('Rahu', 'Ketu'))]
                if any((tr[q] - c.moon_sign) % 12 + 1 == vh for q in blockers):
                    return False
            return True
        if sel == 'bad':
            return h not in good
        return h in sel
    if atom == 'gochara_set':                    # [[planet, [houses from the Moon]], ...] all at once (XXVI v. 33-34)
        tr = c.date(jd)['transit']
        return all((tr[pl] - c.moon_sign) % 12 + 1 in hs for pl, hs in a)
    if atom == 'tnak':                           # [planet, [k]]: transiting planet in the k-th star from the natal star
        tr = c.date(jd)['transit']
        n0 = int((c.lon['Moon'] % 360) // (360 / 27))
        return (tr['_nak'][a[0]] - n0) % 27 + 1 in a[1]
    if atom == 'latta':                          # planet: the natal star is the planet's Latta star (XXVI v. 42-44)
        tr = c.date(jd)['transit']
        n0 = int((c.lon['Moon'] % 360) // (360 / 27))
        k = LATTA[a]
        star = (tr['_nak'][a] + (k - 1 if k > 0 else k + 1)) % 27
        return star == n0
    if atom == 'special_with':                   # [body, ref]: the special point in the same sign as the planet(s)
        x = c.special.get(a[0])
        return x is not None and any(c.signs[p] == int(x // 30) for p in refs(c, a[1]))
    if atom == 'pd_drek_lord':                   # [ref, lord]: the planet's decanate (Phaladeepika III v. 4) owned by lord
        return any(F.SIGN_LORD[PV.varga_sign('D3', c.lon[p])] == a[1] for p in refs(c, a[0]))
    if atom == 'n_in_one_sign':                  # at least n of the nine in a single sign
        from collections import Counter
        return max(Counter(c.signs[p] for p in GRAHAS).values()) >= a
    if atom.startswith('kp_'):
        k = c.kp
        if k is None:
            return False
        if atom == 'kp_csl':                     # [cusp, [houses], 'any'|'none']: the cusp sub lord signifies them
            sig = k.signified(k.csl[a[0]])
            hit = bool(sig & set(a[1]))
            return hit if (len(a) < 3 or a[2] == 'any') else not hit
        if atom == 'kp_csl_star':                # [cusp, [houses]]: the star lord of the cusp sub lord signifies them
            return bool(k.signified(k.star[k.csl[a[0]]]) & set(a[1]))
        if atom == 'kp_csl_lordship':            # [cusp, [houses]]: the cusp sub lord owns one of these houses
            p = k.csl[a[0]]
            return any(k.lord[h] == p for h in a[1])
        if atom == 'kp_cusp_star_lordship':      # [cusp, [houses]]: the star lord of the cusp owns one of these houses
            return any(k.lord[h] == k.cusp_star[a[0]] for h in a[1])
        if atom == 'kp_majority_8_12':           # R3 p. 182: most planets in the star or sub of the lords of 8 or 12
            ls = {k.lord[8], k.lord[12]}
            return sum(k.star[q] in ls or k.sub[q] in ls for q in KP.NINE) >= 5
        if atom == 'kp_no_cure':                 # R3 p. 175: no planet in 11, none in the star of the 11th owner or
            occ = k.occupants(11)                # occupants, and the 11th cusp sub lord a significator of 6/8/12 only
            in_star = [q for q in KP.NINE if k.star[q] in occ or k.star[q] == k.lord[11]]
            s = k.signified(k.csl[11])
            return not occ and not in_star and bool(s & {6, 8, 12}) and not s & {1, 11}
        if atom == 'kp_planet_house':            # [planet or 'kplord:N' (lord of the sign on cusp N), [houses]] Placidus (KP) house
            pl = k.lord[int(a[0][7:])] if str(a[0]).startswith('kplord:') else a[0]
            return k.house[pl] in a[1]
        if atom == 'kp_planet_sig_both':         # [planet or 'lordN', [houses A], [houses B]]: signifies one of A and one of B
            q = k.lord[int(a[0][4:])] if str(a[0]).startswith('lord') else a[0]
            s = k.signified(q)
            return bool(s & set(a[1])) and bool(s & set(a[2]))
        if atom == 'kp_sig_link':                # [[houses A], [houses B], n]: at least n planets signify both groups
            return sum(bool(k.signified(q) & set(a[0])) and bool(k.signified(q) & set(a[1])) for q in KP.NINE) >= a[2]
        if atom == 'kp_occ_in_star_of_lord':     # [house, [houses]]: an occupant is in the star of a lord of those cusps (R3 p. 345)
            lords = {k.lord[h] for h in a[1]}
            return any(k.star[p] in lords for p in k.occupants(a[0]))
        if atom == 'kp_csl_pos':                 # [cusp, [houses], [signs 0-11] or None]: where the cusp sub lord sits (R3 p. 361)
            s = k.csl[a[0]]
            return k.house[s] in a[1] and (a[2] is None or int(k.lon[s] % 360 // 30) in a[2])
        if atom == 'kp_cusplord_sub':            # [cusp, [planets]]: the lord of the cusp's sign is in the sub of these (R3 p. 361)
            return k.sub[k.lord[a[0]]] in a[1]
        if atom == 'kp_sub_sig':                 # [ref, [houses], 'any'|'none']: the planet's sub lord signifies them (R4 p. 81)
            hit = any(bool(k.signified(k.sub[p]) & set(a[1])) for p in refs(c, a[0]))
            return hit if (len(a) < 3 or a[2] == 'any') else not hit
        if atom == 'kp_star_sub':                # [ref, {star:[lords], sub:[lords]}]: KP star / sub lord of a planet (R3 pp. 409-410)
            res = lambda xs: set().union(*(refs(c, x) for x in xs))   # entries may be planet names or refs like 'lord:2'
            return any(('star' not in a[1] or k.star[p] in res(a[1]['star'])) and ('sub' not in a[1] or k.sub[p] in res(a[1]['sub']))
                       for p in refs(c, a[0]))
        if atom == 'kp_lord_in_star_of_lord':    # [cusp, [cusps]]: the lord of the cusp's sign is in the star of a lord of those cusps (R3 pp. 399-401)
            return k.star[k.lord[a[0]]] in {k.lord[h] for h in a[1]}
        if atom == 'kp_csl_retro':               # [cusp]: the cusp sub lord is retrograde at birth (R3 p. 397); nodes excluded
            s = k.csl[a[0]]
            return s not in ('Rahu', 'Ketu') and bool(c.st['vec'][s][S.PLANET_FEATURES.index('retro')])
        if atom == 'kp_cusp_lords':              # [cusp, {sign_of:[0-11], sign:[lords], star:[lords], sub:[lords]}] R3 pp. 327-329
            h, q = a
            return (('sign_of' not in q or int(k.cusp[h] % 360 // 30) in q['sign_of']) and ('sign' not in q or k.lord[h] in q['sign'])
                    and ('star' not in q or k.cusp_star[h] in q['star']) and ('sub' not in q or k.csl[h] in q['sub']))
        if atom == 'kp_csl_of':                  # [cusp, [planets]]: the cusp sub lord is one of these planets
            return k.csl[a[0]] in a[1]
        if atom == 'kp_csl_node':                # [cusp]: the cusp sub lord is a node
            return k.csl[a[0]] in ('Rahu', 'Ketu')
        if atom == 'kp_csl_in_star_of_planet':   # [cusp, [planets]]: the cusp sub lord sits in the star of these planets
            return k.star[k.csl[a[0]]] in a[1]
        if atom == 'kp_cssl':                    # [cusp, [houses], 'any'|'none']: the cusp SUB-SUB lord signifies them (modern KP)
            hit = bool(k.signified(KP.sub_sub_lord(k.cusp[a[0]])) & set(a[1]))
            return hit if (len(a) < 3 or a[2] == 'any') else not hit
        if atom == 'kp_csl_starlord_house':      # [cusp, [houses]]: the star lord of the cusp sub lord occupies these (KP) houses
            return k.house[k.star[k.csl[a[0]]]] in a[1]
        if atom == 'kp_csl_starlord_sign':       # [cusp, [signs 0-11]]: R3 p. 350, the sign of the star lord of the cusp sub lord
            return int(k.lon[k.star[k.csl[a[0]]]] % 360 // 30) in a[1]
        if atom == 'kp_lagna_csl_starlord_sign':  # R3 p. 433: the sign occupied by the star lord of the lagna sub lord
            return int(k.lon[k.star[k.csl[1]]] // 30) in a
        if atom == 'kp_punarphoo':               # R4 p. 79
            return (k.star['Saturn'] == 'Moon' and k.sub['Saturn'] == 'Saturn') or (k.star['Moon'] == 'Saturn' and k.sub['Moon'] == 'Moon')
        if atom == 'kp_csl_dual':                # R4 p. 182: the cusp sub lord or its star lord in a dual sign
            q = k.csl[a[0]]
            return int(k.lon[q] // 30) % 3 == 2 or int(k.lon[k.star[q]] // 30) % 3 == 2
        if atom == 'kp_csl_chain_nodes_sat':     # R4 p. 222: star and sub lords of the cusp sub lord all Saturn/Rahu/Ketu
            q = k.csl[a[0]]                      # and all signifying the given houses
            chain = [k.star[q], k.sub[q]]
            return all(x in ('Saturn', 'Rahu', 'Ketu') for x in chain) and all(k.signified(x) & set(a[1]) for x in chain + [q])
        if atom == 'kp_node_in_badhaka_star':    # R2 p. 461: the node in the star or sub of the badhaka occupant (or lord)
            bh = KP.badhaka_house(int(k.cusp[1] // 30))
            evil = set(k.occupants(bh)) or {k.lord[bh]}
            return k.star[a[0]] in evil or k.sub[a[0]] in evil
        if atom == 'kp_csl_star_badhaka_maraka':  # R6 p. 156: the cusp sub lord's star lord signifies the badhaka house
            bh = KP.badhaka_house(int(k.cusp[1] // 30))   # and a maraka (2 or 7)
            s = k.signified(k.star[k.csl[a[0]]])
            return bh in s and bool(s & {2, 7})
        if atom == 'kp_fortuna':                 # [{'sub_sig': [houses]} | {'house': [houses]}]: Pars Fortuna = Asc + Moon - Sun
            fl = (k.cusp[1] + k.lon['Moon'] - k.lon['Sun']) % 360   # (KP Astrology for Beginners, Fortuna chapter)
            if 'sub_sig' in a[0]:
                return bool(k.signified(KP.sub_lord(fl)) & set(a[0]['sub_sig']))
            return KP.house_of(fl, k.cusp) in a[0]['house']
        if atom == 'kp_csl_star_combust':        # [cusp]: the cusp sub lord is in the star of a combust planet (R6 p. 151)
            s = k.star[k.csl[a[0]]]
            return s not in ('Rahu', 'Ketu') and bool(c.combust.get(s))
        if atom == 'kp_sig':                     # [ref-like planet name or 'lagna_csl', [houses]]
            p = k.csl[1] if a[0] == 'lagna_csl' else a[0]
            return bool(k.signified(p) & set(a[1]))
        if jd is None:
            raise ValueError('dasha condition needs a date')
        d = c.kp_date(jd)
        if atom == 'kp_dasha':                   # {'levels': [...], 'houses': [...], 'need': n, 'sub_filter': bool,
            lv = a['levels']                     #  'deny': [...]}
            ok = 0
            for level in lv:
                p = d[level]
                s = k.signified(p)
                good = bool(s & set(a['houses']))
                if good and a.get('sub_filter'):
                    good = bool(k.signified(k.sub[p]) & set(a['houses']))
                if good and a.get('deny'):
                    good = not (k.signified(k.sub[p]) & set(a['deny']) and not k.signified(k.sub[p]) & set(a['houses']))
                ok += good
            return ok >= a.get('need', len(lv))
        if atom == 'kp_cusp_chain_dasha':        # [cusp, levels, need]: sign, star, sub lords of the cusp and the star
            cu = a[0]                            # lord of the sub lord (R3 p. 168) run at >= need levels
            chain = {k.lord[cu], k.cusp_star[cu], k.csl[cu], k.star[k.csl[cu]]}
            return sum(d[level] in chain for level in a[1]) >= a[2]
        if atom == 'kp_lord_dasha':              # [cusp, [levels]]: the lord of the cusp's sign runs at one of the levels
            return any(d[level] == k.lord[a[0]] for level in a[1])
        if atom == 'kp_period_star_is':          # [[levels], [planets]]: each period lord sits in the star of one of these planets
            return all(k.star[d[level]] in a[1] for level in a[0])
        if atom == 'kp_dba_cover':               # [[levels], [houses]]: the period lords jointly signify every house, each a different one
            from itertools import permutations          # (KP e-zine: 'DBA lords jointly the primary significators of all the houses')
            sig = [k.signified(d[level]) for level in a[0]]
            return any(all(h in sig[i] for i, h in enumerate(perm)) for perm in permutations(a[1], min(len(a[1]), len(sig)))
                       ) if len(sig) >= len(a[1]) else False
        if atom == 'kp_csl_dasha':               # [cusp, [levels]]: the cusp sub lord rules one of these periods
            return any(d[level] == k.csl[a[0]] for level in a[1])
        if atom == 'kp_dasha_planet':            # [[planets], [levels]]
            return any(d[level] in a[0] for level in a[1])
        if atom == 'kp_jup_on_dasha_sign':       # R3 pp. 200-201: Jupiter transits a sign ruled by the dasa (or bhukti) lord
            s = c.date(jd)['transit']['Jupiter']
            return any(KP.F.SIGN_LORD[s] == d[level] for level in a)
        if atom == 'kp_dasha_sig_pair':          # [[levels], [houses A], [houses B]]: each lord signifies one of A and one of B
            return all(bool(k.signified(d[level]) & set(a[1])) and bool(k.signified(d[level]) & set(a[2])) for level in a[0])
        if atom == 'kp_period_sub_sig':          # [[levels], [houses yes], [houses no]]: each period lord's sub lord
            for level in a[0]:                   # signifies a 'yes' house and none of the 'no' houses
                s = k.signified(k.sub[d[level]])
                if not (s & set(a[1])) or s & set(a[2]):
                    return False
            return True
        if atom == 'kp_transit_sl':              # [mover, 'star'|'sub', [houses]]: the lord of the star / sub the mover
            lon = KP.kp_transit(jd)[a[0]]       # transits signifies these houses (R5 pp. 150-162)
            lord = KP.star_lord(lon) if a[1] == 'star' else KP.sub_lord(lon)
            return bool(k.signified(lord) & set(a[2]))
        if atom == 'kp_transit_dba_point':       # [[movers], need]: a mover transits a point whose sign, star and sub lords
            lords = {d['MD'], d['AD'], d['PD']}  # are the dasa, bhukti and anthra lords (R5 p. 162)
            for m in a[0]:
                lon = KP.kp_transit(jd)[m]
                pt = {KP.sign_lord(lon), KP.star_lord(lon), KP.sub_lord(lon)}
                if len(pt & lords) >= min(a[1], len(lords)):
                    return True
            return False
        if atom == 'kp_badhaka_dasha':           # [levels, need]: dasha lords signify the badhaka house or 2/7 (marakas)
            bh = KP.badhaka_house(int(k.cusp[1] // 30))
            hs = {bh, 2, 7}
            return sum(bool(k.signified(d[level]) & hs) for level in a[0]) >= a[1]
        if atom == 'kp_transit_star':            # [mover, [houses]]: transiting mover in the star of a significator
            tr = c.date(jd)['transit']['_nak'][a[0]]
            lord = KP.LORDS[tr % 9]
            return bool(k.signified(lord) & set(a[1]))
    if atom == 'retro_transit':                  # the transiting planet is retrograde on the date (Jupiter / Saturn)
        if jd is None:
            raise ValueError('transit condition needs a date')
        return a in c.date(jd)['transit']['_retro']
    if atom == 'parivartana':                    # [house i, house j]: lords of i and j in each other's houses
        li, lj = c.lord(a[0]), c.lord(a[1])
        return li != lj and c.house_of(li) == a[1] and c.house_of(lj) == a[0]
    if atom == 'n_in_house':                     # [refs, houses, n]
        return sum(c.house_of(p) in a[1] for p in refs(c, a[0])) >= a[2]
    if atom == 'n_dignity':                      # [refs, classes, n]: at least n planets in those dignities
        return sum(c.dig[p] in a[1] for p in refs(c, a[0])) >= a[2]
    if atom == 'n_aspecting':                    # [ref, n]: at least n planets aspect the planet
        tgt = refs(c, a[0])
        return any(sum(_aspects_sign(q, c.signs[q], c.signs[p]) for q in GRAHAS if q != p) >= a[1] for p in tgt)
    if atom == 'vargottama':                     # same sign in the rashi and the navamsa
        return any(c.varga['D9'][0][p] == c.signs[p] for p in refs(c, a))
    if atom == 'nabhasa':                        # vol. 1 ch. 37
        if not hasattr(c, '_nabhasa'):
            c._nabhasa = BN.active(c.signs, c.lagna, c.benefics)
        return a in c._nabhasa
    if atom == 'functional':                     # [ref, [natures]]: vol. 1 ch. 36 functional nature for this Lagna
        f = BF.FUNCTIONAL[c.lagna]
        return any(BF.nature(c.lagna, p) in a[1] or ('killer' in a[1] and p in f['killer']) for p in refs(c, a[0]))
    if atom == 'kk_in_sign':
        return c.karakamsa in a
    if atom == 'yogakaraka_natal':               # ch. 34 v. 25-30: planets in own/exalted/friend's sign mutually in
        return bool(_yogakarakas(c))             # kendras or in kendras from the Lagna (two or more)
    if atom == 'pada_in_sign':                   # [N, [signs]]
        return c.pada(a[0]) in a[1]
    if atom == 'ishta_gt_kashta':                # vol. 1 ch. 30 v. 11-12
        sb = c.shadbala
        return any(p in sb and sb[p]['ishta'] > sb[p]['kashta'] for p in refs(c, a))
    if atom == 'shadbala':                       # [ref, lo, hi] on total / requirement
        sb = c.shadbala
        return any(p in sb and a[1] <= sb[p]['ratio'] < a[2] for p in refs(c, a[0]))
    if atom == 'conjunct':
        return any(c.signs[p] == c.signs[q] and p != q for p in refs(c, a[0]) for q in refs(c, a[1]))
    if atom == 'aspects':
        tgt = _target_signs(c, a[1])
        return any(_aspects_sign(p, c.signs[p], t) for p in refs(c, a[0]) for t in tgt)
    if atom == 'associated':
        ps = refs(c, a[0])
        if str(a[1]).startswith(('house:', 'moon_house:', 'sign:')):  # occupies or aspects the house / sign
            t = _target_signs(c, a[1])
            return any(c.signs[p] in t or any(_aspects_sign(p, c.signs[p], x) for x in t) for p in ps)
        qs = refs(c, a[1])
        return any(_associated(c, p, q) for p in ps for q in qs)
    if atom == 'varga_in_house':
        vsigns, vlagna = c.varga[a[0]]
        return any((vsigns[p] - vlagna) % 12 + 1 in a[2] for p in refs(c, a[1]))
    if atom == 'varga_dignity':          # sign-level dignity in the divisional chart (natural friendship)
        vsigns, _ = c.varga[a[0]]
        return any(BC.dignity(p, vsigns[p] * 30 + 15) in a[2] for p in refs(c, a[1]))
    if atom == 'is':                     # the two references share a planet (e.g. the Sun is the 6th lord)
        return bool(refs(c, a[0]) & refs(c, a[1]))
    if atom == 'combust':
        return any(c.combust[p] for p in refs(c, a))
    if atom == 'dasha_frac':                     # Vimshottari level has run between lo and hi of its length
        d = c.date(jd)['V'][a[0]]
        return a[1] <= d['elapsed'] / d['length'] < a[2]
    if atom == 'dasha_elapsed':                  # ... between lo and hi years since it began
        d = c.date(jd)['V'][a[0]]
        return a[1] <= d['elapsed'] < a[2]
    if atom == 'lagna_sign':
        return c.lagna in a
    if atom == 'av_own_natal':                   # [planet, lo, hi]: bindus in the planet's own Saravali Ashtakavarga in its natal sign (ch. 54)
        if not hasattr(c, '_sar_av'):
            from src.rules import sar_av as SAV
            c._sar_av = SAV.bindus(c)
        return a[1] <= c._sar_av[a[0]][c.signs[a[0]]] <= a[2]
    if atom == 'sar_av_transit':                 # [planet, lo, hi]: it transits a sign with lo..hi bindus in its own Saravali AV (ch. 53 v. 9-10)
        if not hasattr(c, '_sar_av'):
            from src.rules import sar_av as SAV
            c._sar_av = SAV.bindus(c)
        return a[1] <= c._sar_av[a[0]][c.date(jd)['transit'][a[0]]] <= a[2]
    if atom == 'av_point':                       # ch. 72: transit over the pinda-derived nakshatra/sign or its trines
        planet, house, mover, mode = a
        naks, signs = c.av.point(planet, house)
        t = c.date(jd)['transit']
        hit_n, hit_s = t['_nak'][mover] in naks, t[mover] in signs
        return hit_n if mode == 'nak' else hit_s if mode == 'sign' else (hit_n or hit_s)
    if atom == 'av_transit':                     # ch. 72: transit over signs by rekha count in a planet's AV
        planet, mover, cls = a
        s = c.date(jd)['transit'][mover]
        r, tri = c.av.rekhas[planet][s], c.av.trikona[planet][s]
        # each sign carries 8 marks (p. 537): 'more rekhas' = rekhas outnumber dots (>= 5), 'more dots' = <= 3
        return {'more_rekhas': r >= 5, 'more_dots': r <= 3, 'zero': r == 0,
                'tri_zero': tri == 0, 'tri_more': tri > 0}[cls]
    if atom == 'tithi':                          # natal tithi 1-30 (1-15 Shukla, 16-30 Krishna; 30 = Amavasya)
        return _tithi(c)[0] in a
    if atom == 'tithi_part':                     # [tithi, n_parts, [parts 1..n]]: which part of the tithi at birth
        n, frac = _tithi(c)
        return n == a[0] and int(frac * a[1]) + 1 in a[2]
    if atom == 'nakshatra':                      # natal Moon nakshatra 1-27 (1 = Ashwini), optional padas [1-4]
        x = c.lon['Moon'] % 360
        k = int(x // (360 / 27))
        pada = int((x - k * 360 / 27) // (360 / 108)) + 1
        return k + 1 in a[0] and (len(a) < 2 or pada in a[1])
    if atom == 'special_in_house':               # vol. 1 ch. 27: a non-luminous body in given houses
        x = c.special.get(a[0])
        return x is not None and (int(x // 30) - c.lagna) % 12 + 1 in a[1]
    if atom == 'day_birth':
        return c.day is not None and c.day['day_birth'] == a
    if atom == 'upagraha_with':                  # vol. 1 ch. 3 v. 61-65: Dhooma .. Upaketu in the sign of Sun/Moon/Lagna
        dhooma = (c.lon['Sun'] + 133 + 20 / 60) % 360
        vyati = (360 - dhooma) % 360
        pari = (vyati + 180) % 360
        indra = (360 - pari) % 360
        upaketu = (indra + 16 + 40 / 60) % 360
        target = c.lagna if a == 'Lagna' else c.signs[a]
        return any(int(x // 30) == target for x in (dhooma, vyati, pari, indra, upaketu))
    if atom == 'gandanta':                       # ch. 94: tithi / nakshatra / lagna gandanta at birth
        return _gandanta(c, a)
    if atom == 'gender':                         # 'M' / 'F' from the person record (absent -> never true)
        return c.s.get('gender') == a
    if atom == 'age':                            # native's age in years in [lo, hi)
        return a[0] <= (jd - c.bjd) / 365.25 < a[1]
    if atom == 'sud':                            # ch. 76 Sudarshana: planets of ref in houses from the running sign
        level, base, ref_, houses = a
        age = (jd - c.bjd) / 365.25
        k = int(age) if level == 'year' else int(age) + int((age - int(age)) * 12)   # v. 21-23: 1 house a year,
        start = {'lagna': c.lagna, 'moon': c.signs['Moon'], 'sun': c.signs['Sun']}[base]  # then a month each
        s = (start + k) % 12
        return any((c.signs[p] - s) % 12 + 1 in houses for p in refs(c, ref_))
    if atom == 'sar_rays_total':                 # Saravali ch. 36: total rays of the seven planets in [lo, hi]
        if not hasattr(c, '_sar_rays'):
            from src.rules import sar_rays as SR
            ri = S.PLANET_FEATURES.index('retro')
            c._sar_rays = sum(SR.rays(p, c.lon[p], c.dig[p], c.combust[p], bool(c.st['vec'][p][ri])) for p in AV_PLANETS)
        return a[0] <= c._sar_rays <= a[1]
    if atom == 'rays_total':                     # ch. 75: total rays of the seven planets in [lo, hi]
        if not hasattr(c, '_rays'):
            c._rays = sum(BR.rays(p, c.lon[p], c.dig[p], c.combust[p]) for p in AV_PLANETS)
        return a[0] <= c._rays <= a[1]
    if atom == 'sav_transit':                    # ch. 74: transit over a sign whose Samudaya count is in [lo, hi]
        mover, lo, hi = a
        n = c.av.samudaya[c.date(jd)['transit'][mover]]
        return lo <= n <= hi
    if atom == 'av_ayu':                         # ch. 73: age within a years of the Ashtakavarga longevity
        return abs((jd - c.bjd) / 365.25 - c.av.ayu()) < a
    if atom == 'av_year':                        # ch. 72 v. 37-40: 'in the Nth year' = age between N-1 and N
        n = c.av.saturn_years()[a]
        age = (jd - c.bjd) / 365.25
        return n - 1 <= age < n
    if atom == 'varga_in_sign':
        vsigns, _ = c.varga[a[0]]
        return any(vsigns[p] in a[2] for p in refs(c, a[1]))
    if atom == 'kc_natal':
        return _kc_natal_match(c, a)
    if atom == 'chara':
        ch = c.date(jd)['CH']
        if ch is None:
            return False
        md = {f: v for f, v in a.items() if not f.startswith('ad_')}
        ad = {f[3:]: v for f, v in a.items() if f.startswith('ad_')}
        return _sign_ctx_match(c, ch['sign'], ch['index'], md) and _sign_ctx_match(c, ch['ad_sign'], ch['ad_index'], ad)
    if atom == 'kc':
        k = c.date(jd)['KC']
        return k is not None and _kc_natal_match(c, {f: v for f, v in a.items() if f in KC_NATAL_FIELDS}) \
            and _kc_match(c, k, a)
    if atom == 'moon_phase':             # waxing (shukla) = Moon 0-180 deg ahead of the Sun
        waxing = (c.lon['Moon'] - c.lon['Sun']) % 360 < 180
        return waxing if a == 'waxing' else not waxing
    if atom == 'dasha':
        if jd is None:
            raise ValueError('dasha condition needs a date')
        d = c.date(jd)
        ps = refs(c, a[1])
        return any(d[level] in ps for level in a[0])
    if atom == 'moola':                          # Saravali Moola dasa (src/rules/sar_moola): [levels MD/AD, refs or 'Lagna']
        from src.rules import sar_moola as SM
        d = SM.at(c, jd)
        ps = {x for x in (a[1] if isinstance(a[1], list) else [a[1]]) if x == 'Lagna'} | refs(c, [x for x in (a[1] if isinstance(a[1], list) else [a[1]]) if x != 'Lagna'])
        return any(d.get(level) in ps for level in a[0])
    if atom == 'moola_start_transit':            # [planet, signs]: its transit sign when the running Moola dasa began
        from src.rules import sar_moola as SM
        d = SM.at(c, jd)
        return d.get('md_start') is not None and R.transit_signs(d['md_start'])[a[0]] in a[1]
    if atom == 'transit':
        if jd is None:
            raise ValueError('transit condition needs a date')
        t = c.date(jd)['transit']
        target, mode = a[1], (a[2] if len(a) > 2 else 'either')
        tgt = _target_signs(c, target)
        for planet in refs(c, a[0]):             # a fixed planet, or a natal reference such as 'lord:7'
            frm = {t[planet]} | ({(t[planet] - 1) % 12} if planet in t['_retro'] else set())
            occ = any(f in tgt for f in frm)
            asp = any(_aspects_sign(planet, f, x) for f in frm for x in tgt)
            if occ if mode == 'occupies' else asp if mode == 'aspects' else (occ or asp):
                return True
        return False
    if atom == 'yoga':
        if not yogas or a not in yogas:
            raise ValueError(f'unknown yoga {a!r}')
        return evaluate(c, yogas[a], None, yogas)
    raise ValueError(f'unknown atom {atom!r}')


# ── validation and loading ───────────────────────────────────────────────────

def _check_ref(ref) -> None:
    if isinstance(ref, list):
        for r in ref:
            _check_ref(r)
        return
    if ref in GRAHAS or ref in ('benefics', 'malefics', 'marakas'):
        return
    kind, _, arg = str(ref).partition(':')
    if kind in ('lord', 'occupants', 'aspecting', 'd9lord', 'mlord') and arg.isdigit() and 1 <= int(arg) <= 12:
        return
    if kind == 'pd_profession' and arg == '':
        return
    if kind in ('navlord', 'exaltlord'):
        return _check_ref(arg)
    if kind == 'lordfrom':
        ref_, n = arg.rsplit(':', 1)
        if not 1 <= int(n) <= 12:
            raise ValueError(f'bad planet reference {ref!r}')
        return _check_ref(ref_)
    if kind in ('strongest', 'weakest'):
        for x in arg.split('|'):
            _check_ref(x)
        return
    if kind in ('drek22', 'drek22m', 'drek1', 'gulikalord', 'mandilord') and arg == '':
        return
    if kind == 'naklord' and arg.isdigit() and 1 <= int(arg) <= 27:
        return
    if kind in ('dispositor', 'with', 'assoc'):
        return _check_ref(arg)
    if kind == 'karaka' and arg in ('AK', 'AmK', 'BK', 'MK', 'PK', 'PiK', 'GK', 'DK'):
        return
    raise ValueError(f'bad planet reference {ref!r}')


def _check_target(t) -> None:
    if isinstance(t, str) and t.startswith(('house:', 'moon_house:')):
        n = int(t.split(':')[1])
        if not 1 <= n <= 12:
            raise ValueError(f'bad house target {t!r}')
        return
    if isinstance(t, str) and t.startswith('sign:'):
        if not 0 <= int(t[5:]) <= 11:
            raise ValueError(f'bad sign target {t!r}')
        return
    if isinstance(t, str) and t.startswith('owned:'):
        return _check_ref(t[6:])
    if isinstance(t, str) and t.startswith(('from:', 'navfrom:')):
        ref_, n = t.split(':', 1)[1].rsplit(':', 1)
        _check_ref(ref_)
        if not 1 <= int(n) <= 12:
            raise ValueError(f'bad from target {t!r}')
        return
    _check_ref(t)


def _check_cond(cond, yogas: set[str], timing: bool) -> None:
    if not isinstance(cond, dict) or len(cond) != 1:
        raise ValueError(f'condition must be a single-key object: {cond!r}')
    (k, a), = cond.items()
    if k in ('all', 'any'):
        if not isinstance(a, list) or not a:
            raise ValueError(f'{k} needs a non-empty list')
        for x in a:
            _check_cond(x, yogas, timing)
        return
    if k == 'not':
        return _check_cond(a, yogas, timing)
    if isinstance(k, str) and k.startswith('w_'):
        from src.rules import west as W
        return W.check(k, a, timing)
    if k not in ATOMS:
        raise ValueError(f'unknown atom {k!r}')
    if k in ('dasha', 'transit', 'moola', 'moola_start_transit', 'sar_av_transit') and not timing:
        raise ValueError(f'{k} is only allowed in timing rules')
    if k in ('in_house', 'in_sign'):
        _check_ref(a[0])
        if not all(isinstance(h, int) and (1 <= h <= 12 if k == 'in_house' else 0 <= h <= 11) for h in a[1]):
            raise ValueError(f'bad numbers in {cond!r}')
        if k == 'in_house' and len(a) > 2 and a[2] not in ('lagna', 'moon'):
            _check_ref(a[2])
    elif k == 'dignity':
        _check_ref(a[0])
        if not set(a[1]) <= DIGNITY_CLASSES:
            raise ValueError(f'bad dignity class in {cond!r}')
    elif k in ('strong', 'weak', 'combust'):
        _check_ref(a)
    elif k in ('conjunct',):
        _check_ref(a[0]); _check_ref(a[1])
    elif k in ('aspects', 'associated'):
        _check_ref(a[0]); _check_target(a[1])
    elif k == 'varga_in_house':
        if a[0] not in VARGAS:
            raise ValueError(f'bad varga {a[0]!r}')
        _check_ref(a[1])
    elif k == 'varga_dignity':
        if a[0] not in VARGAS or not set(a[2]) <= DIGNITY_CLASSES:
            raise ValueError(f'bad varga dignity {cond!r}')
        _check_ref(a[1])
    elif k == 'is':
        _check_ref(a[0]); _check_ref(a[1])
    elif k == 'moon_phase':
        if a not in ('waxing', 'waning'):
            raise ValueError(f'bad moon phase {a!r}')
    elif k == 'dasha':
        if not set(a[0]) <= {'MD', 'AD', 'PD', 'SD', 'PR'}:
            raise ValueError(f'bad dasha level in {cond!r}')
        _check_ref(a[1])
    elif k == 'transit':
        _check_ref(a[0])
        _check_target(a[1])
        if len(a) > 2 and a[2] not in ('occupies', 'aspects', 'either'):
            raise ValueError(f'bad transit mode {a[2]!r}')
    elif k == 'yoga':
        if a not in yogas:
            raise ValueError(f'unknown yoga {a!r}')
    elif k in ('dasha_frac', 'dasha_elapsed'):
        if not timing:
            raise ValueError(f'{k} is only allowed in timing rules')
        if a[0] not in ('MD', 'AD', 'PD', 'SD', 'PR') or not a[1] < a[2]:
            raise ValueError(f'bad {k} in {cond!r}')
    elif k == 'av_point':
        if a[0] not in AV_PLANETS or not 1 <= a[1] <= 12 or a[2] not in GRAHAS or a[3] not in ('nak', 'sign', 'either'):
            raise ValueError(f'bad av_point {cond!r}')
        if not timing:
            raise ValueError('av_point is only allowed in timing rules')
    elif k == 'av_transit':
        if a[0] not in AV_PLANETS or a[1] not in GRAHAS or a[2] not in ('more_rekhas', 'more_dots', 'zero', 'tri_zero', 'tri_more'):
            raise ValueError(f'bad av_transit {cond!r}')
        if not timing:
            raise ValueError('av_transit is only allowed in timing rules')
    elif k == 'tithi':
        if not all(1 <= x <= 30 for x in a):
            raise ValueError(f'bad tithi {cond!r}')
    elif k == 'tithi_part':
        if not (1 <= a[0] <= 30 and a[1] >= 1 and all(1 <= x <= a[1] for x in a[2])):
            raise ValueError(f'bad tithi_part {cond!r}')
    elif k == 'nakshatra':
        if not all(1 <= x <= 27 for x in a[0]) or (len(a) > 1 and not all(1 <= x <= 4 for x in a[1])):
            raise ValueError(f'bad nakshatra {cond!r}')
    elif k == 'special_in_house':
        if a[0] not in ('Dhuma', 'Vyatipata', 'Parivesha', 'Indrachapa', 'Upaketu', 'Gulika', 'Pranapada', 'Mandi')                 or not all(1 <= h <= 12 for h in a[1]):
            raise ValueError(f'bad special_in_house {cond!r}')
    elif k == 'from_pada':
        _check_ref(a[1])
        if not 1 <= a[0] <= 12 or not all(1 <= h <= 12 for h in a[2]):
            raise ValueError(f'bad from_pada {cond!r}')
    elif k == 'pada_from_pada':
        if not (1 <= a[0] <= 12 and 1 <= a[1] <= 12 and all(1 <= h <= 12 for h in a[2])):
            raise ValueError(f'bad pada_from_pada {cond!r}')
    elif k == 'argala':
        if not (str(a[0]).startswith('pada:') or 1 <= int(a[0]) <= 12) or (len(a) > 1 and a[1] not in ('any', 'benefic', 'malefic')):
            raise ValueError(f'bad argala {cond!r}')
    elif k == 'ul_lord_dignity':
        if not set(a) <= DIGNITY_CLASSES:
            raise ValueError(f'bad ul_lord_dignity {cond!r}')
    elif k == 'from_kk':
        _check_ref(a[0])
        if not all(1 <= h <= 12 for h in a[1]):
            raise ValueError(f'bad from_kk {cond!r}')
    elif k == 'avastha':
        _check_ref(a[0])
        if not set(a[1]) <= {'Lajjita', 'Garvita', 'Kshudhita', 'Trashita', 'Mudita', 'Kshobhita'}:
            raise ValueError(f'bad avastha {cond!r}')
    elif k in ('pindayu_near', 'in_ayu_span'):
        if not timing:
            raise ValueError(f'{k} is only allowed in timing rules')
    elif k == 'ayu_class':
        if not set(a) <= {'short', 'medium', 'long'}:
            raise ValueError(f'bad ayu_class {cond!r}')
    elif k == 'n_in_house':
        _check_ref(a[0])
    elif k == 'n_in_house_from':
        _check_ref(a[0])
        if a[3] not in ('lagna', 'moon'):
            _check_ref(a[3])
    elif k in ('pd_vaiseshika', 'pd_weak_vargas'):
        _check_ref(a[0])
        if not 0 <= a[1] <= a[2] <= 10:
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'pd_lagna_krura60':
        if not isinstance(a, bool):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'moon_avastha12':
        if not a or not all(1 <= x <= 12 for x in a):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'lagna_hora':
        if a not in ('Sun', 'Moon'):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'deeptadi':
        _check_ref(a[0])
        if not set(a[1]) <= {'Deepta', 'Sukhita', 'Swastha', 'Mudita', 'Santa', 'Bheeta', 'Dukhita', 'Vikala'}:
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'retro':
        _check_ref(a)
    elif k == 'santana_tithi_kerala':
        if not (0 <= a[0] < a[1] <= 360):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'conj_orb':
        _check_ref(a[0]), _check_ref(a[1])
        if not (0 < a[2] <= 30):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'planet_nakshatra':
        _check_ref(a[0])
        if not all(1 <= x <= 27 for x in a[1]):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'lagna_vargottama':
        if not isinstance(a, bool):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'n_aspecting_house':
        if not (1 <= a[0] <= 12 and a[1] >= 1):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'pd_trimsamsa_lord':
        _check_ref(a[0])
    elif k == 'pd_sphuta':
        for r in a[0]:
            _check_ref(r)
        if a[1] not in ('odd', 'even', 'mixed'):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'pd_santana':
        if not set(a) <= {'bright', 'dark', 'amavasya', 'chidra', 'vishti', 'sthira'}:
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'dasha_sphuta_nak':
        if not timing:
            raise ValueError(f'{k} needs a timing rule')
        for r in a[0]:
            _check_ref(r)
    elif k == 'pd_ayu_class':
        if not set(a if isinstance(a, list) else [a]) <= {'long', 'medium', 'short'}:
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'moon_mrityubhaga':
        if not isinstance(a, bool):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'transit_sphuta':
        if not timing or a[0] not in GRAHAS:
            raise ValueError(f'bad {k} {cond!r}')
        for r in a[1]:
            _check_ref(r)
    elif k == 'transit_conj':
        if not timing:
            raise ValueError(f'{k} needs a timing rule')
        _check_ref(a[0])
        _check_ref(a[1])
    elif k == 'transit_point':
        if not timing or not set(a[0]) <= set(GRAHAS) or not set(a[2]) <= {'rasi', 'navamsa', 'd12', 'd3'}:
            raise ValueError(f'bad {k} {cond!r}')
        for coef, body in a[1]:
            if body not in ('Lagna', 'Gulika', 'Mandi', 'deg'):
                _check_ref(body)
    elif k in ('dasha_lord_transit', 'moon_from_dasha_lord', 'sun_on_dasha_sign', 'md_index'):
        if not timing:
            raise ValueError(f'{k} needs a timing rule')
    elif k in ('pd_av_star', 'pd_av_sign', 'pd_av_transit', 'pd_sav_transit', 'pd_av_year'):
        if not timing:
            raise ValueError(f'{k} needs a timing rule')
    elif k in ('gochara', 'tnak', 'latta', 'gochara_set'):
        if not timing:
            raise ValueError(f'{k} needs a timing rule')
    elif k == 'special_with':
        _check_ref(a[1])
    elif k in ('kp_csl', 'kp_csl_star'):
        if not (1 <= a[0] <= 12 and all(1 <= h <= 12 for h in a[1])):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'kp_dasha':
        if not timing or not set(a['levels']) <= {'MD', 'AD', 'PD', 'SD'}:
            raise ValueError(f'bad {k} {cond!r}')
    elif k in ('kp_badhaka_dasha', 'kp_transit_star', 'kp_cusp_chain_dasha', 'kp_lord_dasha', 'kp_jup_on_dasha_sign',
               'kp_dasha_planet', 'kp_dba_cover', 'kp_period_star_is', 'kp_csl_dasha', 'kp_dasha_sig_pair', 'kp_period_sub_sig', 'kp_transit_sl', 'kp_transit_dba_point'):
        if not timing:
            raise ValueError(f'{k} needs a timing rule')
    elif k == 'retro_transit':
        if not timing or a not in ('Jupiter', 'Saturn'):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'parivartana':
        if not (len(a) == 2 and all(1 <= h <= 12 for h in a) and a[0] != a[1]):
            raise ValueError(f'bad {k} {cond!r}')
    elif k == 'n_dignity':
        _check_ref(a[0])
        if not set(a[1]) <= DIGNITY_CLASSES:
            raise ValueError(f'bad n_dignity {cond!r}')
    elif k == 'n_aspecting':
        _check_ref(a[0])
    elif k == 'vargottama':
        _check_ref(a)
    elif k == 'nabhasa':
        if not isinstance(a, str):
            raise ValueError(f'bad nabhasa {cond!r}')
    elif k == 'functional':
        _check_ref(a[0])
        if not set(a[1]) <= {'yogakaraka', 'benefic', 'malefic', 'neutral', 'killer'}:
            raise ValueError(f'bad functional {cond!r}')
    elif k == 'kk_in_sign':
        if not all(0 <= s <= 11 for s in a):
            raise ValueError(f'bad kk_in_sign {cond!r}')
    elif k == 'yogakaraka_natal':
        pass
    elif k == 'pada_in_sign':
        if not 1 <= a[0] <= 12:
            raise ValueError(f'bad pada_in_sign {cond!r}')
    elif k == 'ishta_gt_kashta':
        _check_ref(a)
    elif k == 'shadbala':
        _check_ref(a[0])
        if not a[1] < a[2]:
            raise ValueError(f'bad shadbala {cond!r}')
    elif k == 'day_birth':
        if a not in (True, False):
            raise ValueError(f'bad day_birth {cond!r}')
    elif k == 'upagraha_with':
        if a not in ('Sun', 'Moon', 'Lagna'):
            raise ValueError(f'bad upagraha_with {cond!r}')
    elif k == 'gandanta':
        if a not in ('tithi', 'nakshatra', 'lagna'):
            raise ValueError(f'bad gandanta {cond!r}')
    elif k == 'gender':
        if a not in ('M', 'F'):
            raise ValueError(f'bad gender {cond!r}')
    elif k == 'age':
        if not timing or not 0 <= a[0] < a[1]:
            raise ValueError(f'bad age {cond!r}')
    elif k == 'sud':
        if a[0] not in ('year', 'month') or a[1] not in ('lagna', 'moon', 'sun') or not timing                 or not all(1 <= h <= 12 for h in a[3]):
            raise ValueError(f'bad sud {cond!r}')
        _check_ref(a[2])
    elif k == 'rays_total':
        if not a[0] <= a[1]:
            raise ValueError(f'bad rays_total {cond!r}')
    elif k == 'sav_transit':
        if a[0] not in GRAHAS or not a[1] <= a[2] or not timing:
            raise ValueError(f'bad sav_transit {cond!r}')
    elif k == 'av_ayu':
        if not isinstance(a, (int, float)) or a <= 0 or not timing:
            raise ValueError(f'bad av_ayu {cond!r}')
    elif k == 'av_year':
        if a not in ('lagna_to_saturn', 'saturn_to_lagna', 'total') or not timing:
            raise ValueError(f'bad av_year {cond!r}')
    elif k == 'lagna_sign':
        if not a or not all(isinstance(s, int) and 0 <= s <= 11 for s in a):
            raise ValueError(f'bad lagna signs in {cond!r}')
    elif k == 'varga_in_sign':
        if a[0] not in VARGAS or not all(0 <= s <= 11 for s in a[2]):
            raise ValueError(f'bad varga sign in {cond!r}')
        _check_ref(a[1])
    elif k == 'chara':
        if not timing:
            raise ValueError('chara is only allowed in timing rules')
        if not isinstance(a, dict) or not a or not set(a) <= CHARA_FIELDS:
            raise ValueError(f'bad chara fields in {cond!r}')
        for f, v in a.items():
            g = f[3:] if f.startswith('ad_') else f
            if g == 'sign' and not all(0 <= x <= 11 for x in v):
                raise ValueError(f'bad signs in {cond!r}')
            if g in ('house', 'lord_in') and not all(1 <= x <= 12 for x in v):
                raise ValueError(f'bad houses in {cond!r}')
            if g in ('lord_nature', 'lord_sign_nature') and v not in ('benefic', 'malefic'):
                raise ValueError(f'bad lord nature in {cond!r}')
            if g in ('holds', 'lord_aspected_by', 'lord_with'):
                _check_ref(v)
            if g in ('holds_n', 'from_holds'):
                _check_ref(v[1] if g == 'from_holds' else v[0])
            if g in ('from_holds', 'from_dignity') and not all(1 <= x <= 12 for x in v[0]):
                raise ValueError(f'bad houses in {cond!r}')
            if g in ('holds_dignity', 'lord_dignity') and not set(v) <= DIGNITY_CLASSES:
                raise ValueError(f'bad dignity in {cond!r}')
            if g == 'from_dignity' and not set(v[1]) <= DIGNITY_CLASSES:
                raise ValueError(f'bad dignity in {cond!r}')
    elif k in ('kc', 'kc_natal'):
        allowed = KC_FIELDS if k == 'kc' else KC_NATAL_FIELDS
        if k == 'kc' and not timing:
            raise ValueError('kc is only allowed in timing rules')
        if not isinstance(a, dict) or not a or not set(a) <= allowed:
            raise ValueError(f'bad {k} fields in {cond!r}')
        for f in ('amsa', 'sign', 'prev', 'ad_sign'):
            if f in a and not all(isinstance(s, int) and 0 <= s <= 11 for s in a[f]):
                raise ValueError(f'bad signs in {cond!r}')
        if 'pos' in a and not all(1 <= x <= 9 for x in a['pos']):
            raise ValueError(f'bad position in {cond!r}')
        if 'house' in a and not all(1 <= x <= 12 for x in a['house']):
            raise ValueError(f'bad house in {cond!r}')
        if 'motion' in a and not set(a['motion']) <= set(BD.MOTIONS):
            raise ValueError(f'bad motion in {cond!r}')
        if a.get('cycle', 'savya') not in ('savya', 'apasavya') or a.get('lord_nature', 'benefic') not in ('benefic', 'malefic'):
            raise ValueError(f'bad value in {cond!r}')
        if a.get('role', 'deha') not in ('deha', 'jeeva', 'either'):
            raise ValueError(f'bad role in {cond!r}')
        if 'holds_dignity' in a and not set(a['holds_dignity']) <= DIGNITY_CLASSES:
            raise ValueError(f'bad dignity in {cond!r}')
        for f in ('holds', 'dj_both', 'deha_holds', 'jeeva_holds', 'ad_lord'):
            if f in a:
                _check_ref(a[f])
        for f in ('holds_n', 'dj_holds_n'):
            if f in a:
                _check_ref(a[f][0])


def validate_rule(rule: dict, yogas: set[str] = frozenset()) -> None:
    for key in ('id', 'source', 'ref', 'kind', 'text', 'when', 'predicts', 'status'):
        if key not in rule:
            raise ValueError(f'{rule.get("id", "?")}: missing {key!r}')
    if rule['kind'] not in ('timing', 'natal'):
        raise ValueError(f'{rule["id"]}: kind must be timing or natal')
    if rule['status'] not in ('draft', 'verified'):
        raise ValueError(f'{rule["id"]}: status must be draft or verified')
    p = rule['predicts']
    # timing rules name a data event (testable) and/or an open outcome domain (wealth, travel, ...)
    if rule['kind'] == 'timing':
        if p.get('event') is None and not p.get('domain'):
            raise ValueError(f'{rule["id"]}: timing rule needs an event or a domain')
        if p.get('event') is not None and p['event'] not in EVENTS:
            raise ValueError(f'{rule["id"]}: unknown event {p.get("event")!r}')
    elif not p.get('domain'):
        raise ValueError(f'{rule["id"]}: natal rule needs a domain')
    if p.get('direction') not in ('+', '-'):
        raise ValueError(f'{rule["id"]}: direction must be + or -')
    _check_cond(rule['when'], set(yogas), rule['kind'] == 'timing')
    if 'effect' in rule:
        _check_effect(rule)
    if 'scale' in rule and not (isinstance(rule['scale'], dict) and set(rule['scale']) <= {'dignity_of', 'strength_of', 'avastha_of', 'bhava_of'}):
        raise ValueError(f'{rule["id"]}: bad scale')


EFFECT_TYPES = {'cancels', 'weakens', 'strengthens', 'reverses'}
SELECTOR_KEYS = {'ids', 'id_prefix', 'domain', 'event', 'direction', 'kind', 'chapter'}


def _check_effect(rule: dict) -> None:
    e = rule['effect']
    if e.get('type') not in EFFECT_TYPES:
        raise ValueError(f'{rule["id"]}: bad effect type {e.get("type")!r}')
    sel = e.get('targets')
    if not isinstance(sel, dict) or not sel or not set(sel) <= SELECTOR_KEYS:
        raise ValueError(f'{rule["id"]}: bad effect targets {sel!r}')
    if e['type'] in ('weakens', 'strengthens') and not isinstance(e.get('factor'), (int, float)):
        raise ValueError(f'{rule["id"]}: {e["type"]} needs a numeric factor')


def load_rules(*paths) -> tuple[list[dict], dict]:
    """(rules, yogas) from rules/*.jsonl files; yogas.jsonl entries are named natal conditions."""
    yogas: dict = {}
    yfile = RULES_DIR / 'yogas.jsonl'
    if yfile.exists():
        for line in yfile.read_text(encoding='utf-8').splitlines():
            if line.strip():
                y = json.loads(line)
                yogas[y['name']] = y['when']
    rules, ids = [], set()
    for path in paths or sorted(p for p in RULES_DIR.glob('*.jsonl') if p.name != 'yogas.jsonl'):
        for line in Path(path).read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            validate_rule(r, set(yogas))
            if r['id'] in ids:
                raise ValueError(f'duplicate rule id {r["id"]}')
            ids.add(r['id'])
            rules.append(r)
    return rules, yogas


class RuleFeaturizer(Mo.Featurizer):
    """One feature per timing rule: 1.0 if the rule fires on the date (NaN if the chart has no Lagna)."""
    dtype = np.float32

    def __init__(self, rules: list[dict], yogas: dict):
        self.rules = [r for r in rules if r['kind'] == 'timing' and r['predicts'].get('event')]
        self.yogas = yogas
        self.n = len(self.rules)
        self.name = f'rules-{self.n}'

    def context(self, s: dict):
        return Chart(s) if not math.isnan(s['natal'][-1]) else None

    def features(self, ctx, jd: float) -> np.ndarray:
        if ctx is None:
            return np.full(self.n, np.nan, np.float32)
        return np.array([float(evaluate(ctx, r['when'], jd, self.yogas)) for r in self.rules], np.float32)
