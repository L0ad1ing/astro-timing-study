"""
src/context_builder.py — a readable astrological state report for one person at one moment.

Replaces the 706 binary columns with the structured facts a practitioner reads: running dashas with their
dates, the Bhrigu Chakra year, the Hellenistic profection and Lord of the Year, the Tajika year, Sade Sati,
Ashtakavarga support of the slow transits, and exact slow transits to natal points and angles.
Every value is computed (src/features.py, src/rao.py conventions: sidereal, Lahiri, Swiss Ephemeris);
nothing is interpreted here — interpretation belongs to the consultation agent.

BCP active house follows the Alif Astrology site (src/lib/bhriguChakra.ts): house = ((age - 1) mod 12) + 1,
age in completed years (minimum 1).
"""
from __future__ import annotations

import math

import numpy as np

from src import features as F
from src import rao as R
from src.preprocessing import NATAL

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius",
         "Capricorn", "Aquarius", "Pisces"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
              "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
              "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
              "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
ASPECT_ANGLES = {"conjunction": 0, "sextile": 60, "square": 90, "trine": 120, "opposition": 180}
SLOW = {"Mars": 1.0, "Jupiter": 1.5, "Saturn": 1.5, "Rahu": 1.5, "Ketu": 1.5}
DAYS_PER_DEGREE = 365.25 / 30


def _date(jd: float) -> str:
    swe, _ = F._swe()
    y, m, d, _h = swe.revjul(jd)
    return f"{y:04d}-{m:02d}-{d:02d}"


def _sign(lon: float) -> int:
    return int((lon % 360) // 30)


def _planet_lons(jd: float) -> dict[str, tuple[float, float]]:
    """{planet: (sidereal longitude, speed deg/day)} incl. Ketu."""
    swe, flags = F._swe()
    ids = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
           "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
    out = {}
    for p, i in ids.items():
        c = swe.calc_ut(jd, i, flags | swe.FLG_SPEED)[0]
        out[p] = (c[0], c[3])
    out["Ketu"] = ((out["Rahu"][0] + 180) % 360, out["Rahu"][1])
    return out


def vimshottari_periods(moon: float, birth_jd: float, jd: float) -> dict:
    """Running maha/antar/pratyantar dasha with start and end dates (365.25-day years)."""
    Y = F.DASHA_YEARS
    nak = (moon % 360) / (360 / 27)
    i = int(nak) % 9
    start = birth_jd - (nak - int(nak)) * Y[i] * 365.25       # the first mahadasha began before birth
    while start + Y[i] * 365.25 <= jd:
        start += Y[i] * 365.25
        i = (i + 1) % 9
    md = (i, start, start + Y[i] * 365.25)
    j, s = i, start
    while s + Y[i] * Y[j] / 120 * 365.25 <= jd:
        s += Y[i] * Y[j] / 120 * 365.25
        j = (j + 1) % 9
    ad_len = Y[i] * Y[j] / 120
    ad = (j, s, s + ad_len * 365.25)
    k, ps = j, s
    while ps + ad_len * Y[k] / 120 * 365.25 <= jd:
        ps += ad_len * Y[k] / 120 * 365.25
        k = (k + 1) % 9
    pd = (k, ps, ps + ad_len * Y[k] / 120 * 365.25)
    return {lvl: {"lord": F.DASHA_LORDS[x[0]], "from": _date(x[1]), "to": _date(x[2])}
            for lvl, x in (("maha", md), ("antar", ad), ("pratyantar", pd))}


def state_report(person: dict, jd: float) -> dict:
    """person: {"natal": NATAL-order longitudes (Ascendant NaN if unknown), "birth_jd", "lat", "lon",
    optional "gender" ('M'/'F') and "name"}."""
    nat = person["natal"]
    bjd = person["birth_jd"]
    asc = nat[NATAL.index("Ascendant")]
    has_lagna = not math.isnan(asc)
    natal = {p: float(nat[NATAL.index(p)]) for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")}
    natal["Ketu"] = (natal["Rahu"] + 180) % 360
    age = (jd - bjd) / 365.2425
    years = int(age)
    lagna = _sign(asc) if has_lagna else None
    moon = natal["Moon"]
    report = {"name": person.get("name"), "date": _date(jd), "age": round(age, 2),
              "natal": {"lagna": SIGNS[lagna] if has_lagna else None,
                        "moon_sign": SIGNS[_sign(moon)], "moon_nakshatra": NAKSHATRAS[int(moon // (360 / 27))],
                        "planets": {p: {"sign": SIGNS[_sign(v)], "degree": round(v % 30, 2),
                                        "house": ((_sign(v) - lagna) % 12 + 1) if has_lagna else None}
                                    for p, v in natal.items()}},
              "vimshottari": vimshottari_periods(moon, bjd, jd)}
    ymd, yad = F.yogini_at(moon, bjd, jd)
    report["yogini"] = {"maha": F.YOGINI_LORDS[ymd], "antar": F.YOGINI_LORDS[yad]}

    sky = _planet_lons(jd)
    moon_sign = _sign(moon)
    sat_from_moon = (_sign(sky["Saturn"][0]) - moon_sign) % 12 + 1
    report["sade_sati"] = {"active": sat_from_moon in (12, 1, 2),
                           "phase": {12: "rising", 1: "peak", 2: "setting"}.get(sat_from_moon),
                           "saturn_house_from_moon": sat_from_moon}

    if has_lagna:
        ctx = F.person_context({"natal": nat, "birth_jd": bjd, "lat": person.get("lat"), "lon": person.get("lon")})
        bcp_house = ((max(1, years) - 1) % 12) + 1
        bcp_sign = (lagna + bcp_house - 1) % 12
        lord = F.SIGN_LORD[bcp_sign]
        occupants = [p for p, v in natal.items() if _sign(v) == bcp_sign]
        aspecting = [p for p, v in natal.items() if R.aspects(p, _sign(v), bcp_sign) and p not in occupants]
        last_bday = bjd + years * 365.2425
        report["bhrigu_chakra"] = {
            "active_house": bcp_house, "sign": SIGNS[bcp_sign], "lord": lord,
            "occupants": occupants, "aspected_by": aspecting,
            "trigger_dates": {p: _date(last_bday + (natal[p] % 30) * DAYS_PER_DEGREE)
                              for p in dict.fromkeys([lord] + occupants + aspecting)}}
        prof = (lagna + years) % 12
        yl = F.SIGN_LORD[prof]
        report["profection"] = {"sign": SIGNS[prof], "house": years % 12 + 1, "lord_of_the_year": yl,
                                "lord_natal_house": (_sign(natal[yl]) - lagna) % 12 + 1,
                                "lord_transit_sign": SIGNS[_sign(sky[yl][0])]}
        cur = R.chara_rao(ctx["chara"], jd)
        if cur:
            report["chara"] = {"maha_sign": SIGNS[cur[0]], "antar_sign": SIGNS[cur[1]],
                               "darakaraka": F.chara_karakas(ctx["pos"])["DK"],
                               "atmakaraka": F.chara_karakas(ctx["pos"])["AK"]}
        if person.get("lat") is not None and person.get("lon") is not None:
            ch = F.annual_chart(natal["Sun"], bjd, jd, person["lat"], person["lon"], {})
            muntha = (lagna + ch["years"]) % 12
            report["tajika"] = {"annual_lagna": SIGNS[_sign(ch["lagna"])], "muntha_sign": SIGNS[muntha],
                                "muntha_house": (muntha - lagna) % 12 + 1}
        bav = ctx["bav"]
        report["ashtakavarga"] = {p: {"transit_sign": SIGNS[_sign(sky[p][0])], "own_bindus": bav[p][_sign(sky[p][0])],
                                      "sav": bav["SAV"][_sign(sky[p][0])]} for p in ("Jupiter", "Saturn")}

    # exact slow transits to natal points and angles
    targets = dict(natal)
    if has_lagna:
        targets["Ascendant"] = float(asc)
        if person.get("lat") is not None and person.get("lon") is not None:
            swe, _ = F._swe()
            targets["Midheaven"] = swe.houses_ex(bjd, person["lat"], person["lon"], b"W", swe.FLG_SIDEREAL)[1][1]
    exact = []
    for tp, orb in SLOW.items():
        lon, speed = sky[tp]
        for target, tlon in targets.items():
            for name, ang in ASPECT_ANGLES.items():
                sep = abs(((lon - tlon) + 180) % 360 - 180)
                off = abs(sep - ang)
                if off <= orb:
                    nxt = abs(abs(((lon + speed - tlon) + 180) % 360 - 180) - ang)
                    exact.append({"planet": tp, "aspect": name, "target": f"natal {target}",
                                  "orb_deg": round(off, 2), "applying": bool(nxt < off)})
    report["exact_transits"] = sorted(exact, key=lambda x: x["orb_deg"])
    return report
