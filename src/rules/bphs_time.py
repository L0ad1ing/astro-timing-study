"""
src/rules/bphs_time.py — sunrise-based quantities of BPHS vol. 1 ch. 3 v. 66-74 and ch. 6.

day_info(bjd, lat, lon)  -> sunrise/sunset around the birth, day or night birth, the vedic weekday (from sunrise)
gulika(bjd, lat, lon)    -> longitude of Gulika: the Lagna rising at the start of Saturn's portion when the day (or
                            night) is divided into 8 portions ruled in weekday order from the day lord (by night from
                            the 5th lord from the day lord); the 8th portion has no lord (ch. 3 v. 66-70)
pranapada(bjd, lat, lon, sun_lon) -> ch. 3 v. 71-74: time since sunrise in palas / 15 = signs (2 deg per pala) added to
                            the Sun; for the Sun in a fixed sign add a further 8 signs, in a dual sign 4 signs
Positions are sidereal (Lahiri), whole-sign Lagna from Swiss Ephemeris. Persons need 'lat' and 'lon'; without them
these return None and rules using them do not fire.
"""
from __future__ import annotations

from src import features as F

ORDER = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']


def _rise_set(swe, jd, lat, lon, rise=True):
    flag = swe.CALC_RISE if rise else swe.CALC_SET
    res = swe.rise_trans(jd, swe.SUN, flag | swe.BIT_DISC_CENTER, (lon, lat, 0.0))
    return res[1][0]


def day_info(bjd: float, lat: float, lon: float) -> dict | None:
    if lat is None or lon is None:
        return None
    swe, _ = F._swe()
    try:
        rise_before = _rise_set(swe, bjd - 1.0, lat, lon)
        if rise_before > bjd:                       # search window landed after birth; step back a day
            rise_before = _rise_set(swe, bjd - 2.0, lat, lon)
        nxt = _rise_set(swe, rise_before + 0.5, lat, lon)
        while nxt <= bjd:                            # last sunrise at or before birth
            rise_before, nxt = nxt, _rise_set(swe, nxt + 0.5, lat, lon)
        sunset = _rise_set(swe, rise_before, lat, lon, rise=False)
    except Exception:
        return None
    day = bjd < sunset
    weekday = int((rise_before + 1.5) % 7)          # 0 = Sunday for the civil day containing that sunrise
    return {'sunrise': rise_before, 'sunset': sunset, 'next_sunrise': nxt, 'day_birth': day,
            'weekday_lord': ORDER[weekday]}


def _lagna(swe, jd, lat, lon) -> float:
    return swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)[1][0]


def gulika(bjd: float, lat: float, lon: float) -> float | None:
    d = day_info(bjd, lat, lon)
    if d is None:
        return None
    swe, _ = F._swe()
    start, end = (d['sunrise'], d['sunset']) if d['day_birth'] else (d['sunset'], d['next_sunrise'])
    first = ORDER.index(d['weekday_lord']) if d['day_birth'] else (ORDER.index(d['weekday_lord']) + 4) % 7
    k = (ORDER.index('Saturn') - first) % 7         # Saturn's portion number (0-6)
    t = start + k * (end - start) / 8
    return _lagna(swe, t, lat, lon)


def pranapada(bjd: float, lat: float, lon: float, sun_lon: float) -> float | None:
    d = day_info(bjd, lat, lon)
    if d is None:
        return None
    palas = (bjd - d['sunrise']) * 24 * 60 * 60 / 24          # 1 pala = 24 seconds
    s = int((sun_lon % 360) // 30)
    extra = 0 if s in (0, 3, 6, 9) else 240 if s in (1, 4, 7, 10) else 120
    return (sun_lon + palas * 2 + extra) % 360


PD_MANDI_DAY = [26, 22, 18, 14, 10, 6, 2]          # Phaladeepika XXV v. 2: ghatikas (of a 30-ghatika day), Sun..Sat
PD_MANDI_NIGHT = [10, 6, 2, 26, 22, 18, 14]


def pd_mandi(bjd: float, lat: float, lon: float) -> float | None:
    """Phaladeepika XXV v. 2 (1961 p. 335): Mandi rises at the end of the given ghatika of the day (by night of the
    night), scaled to the actual length of the day or night; weekday from sunrise (Sunday first)."""
    d = day_info(bjd, lat, lon)
    if d is None:
        return None
    swe, _ = F._swe()
    wk = ORDER.index(d['weekday_lord'])
    if d['day_birth']:
        start, end, g = d['sunrise'], d['sunset'], PD_MANDI_DAY[wk]
    else:
        start, end, g = d['sunset'], d['next_sunrise'], PD_MANDI_NIGHT[wk]
    return _lagna(swe, start + g / 30 * (end - start), lat, lon)
