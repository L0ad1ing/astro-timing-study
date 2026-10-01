"""
src/harmonic_features.py — continuous harmonic features: no signs, houses, rulerships or rules.

For one person on one date, a dense float vector built from raw planetary geometry:

  sky     angle between every pair of transiting bodies, encoded as cos(k*theta), sin(k*theta) for the
          harmonics k in HARMONICS. cos(k*theta) = 1 exactly when theta is a multiple of 360/k, so
          k=1 conjunction, 2 opposition, 3 trine, 4 square, 5 quintile/biquintile, 6 sextile,
          8 octile/sesquiquadrate. The sin terms keep the side of the aspect (waxing/waning).
          Identical for everyone on a date: these can only find "events cluster when the sky looks
          like X", never anything about a particular chart (the mismatched-chart test cannot apply).
  natal   every transiting body to every natal point (planets, node, Ascendant, Midheaven), same encoding.
          This is the chart-specific part.
  kin     per transiting body: speed / mean speed (near 0 = stationary, negative = retrograde),
          declination, and how far beyond the ecliptic's maximum declination it is (out of bounds).
  helio   optional (helio=True): heliocentric angles between Earth and Mercury..Pluto.

Conventions: Swiss Ephemeris (Moshier), sidereal Lahiri to match the natal array in preprocessing.NATAL.
Angles between two bodies do not depend on the zodiac, so this only matters for consistency.
Event dates have no time of day (noon UT), so the Moon is excluded by default: it moves ~13 deg a day.
Unknown birth time: Ascendant and Midheaven features are NaN (LightGBM treats NaN as missing).

AGE CLOCKS. A slow planet's angle to its own natal position (Saturn to natal Saturn ...) is almost the
same function of age for everyone. A flexible model can use it to learn "events happen at certain ages",
which beats same-person control dates without any astrology (the trap Muntha/dasha features fell into,
see models.AGE_CLOCK_COLUMNS). Those columns are listed in AGE_CLOCK_NAMES and dropped by
HarmonicFeaturizer.default_columns(). Cross-pairs of slow planets still carry partial age information,
so any result must also beat AgeBaseline: a model given nothing but age.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from src import features as F
from src.preprocessing import NATAL

HARMONICS = (1, 2, 3, 4, 5, 6, 8)
TRANSIT_BODIES = ["Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Node"]
NATAL_POINTS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
                "Node", "Ascendant", "Midheaven"]
HELIO_BODIES = ["Earth", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
# Mean geocentric speed (deg/day): Mercury and Venus average the Sun's.
MEAN_SPEED = {"Sun": 0.9856, "Moon": 13.1764, "Mercury": 0.9856, "Venus": 0.9856, "Mars": 0.5240,
              "Jupiter": 0.0831, "Saturn": 0.0335, "Uranus": 0.0117, "Neptune": 0.0060, "Pluto": 0.0040,
              "Node": -0.0530}
SLOW = ("Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Node")


def _ids(swe) -> dict[str, int]:
    return {"Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS, "Mars": swe.MARS,
            "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
            "Pluto": swe.PLUTO, "Node": swe.MEAN_NODE, "Earth": swe.EARTH}


def encode(theta_deg: np.ndarray) -> np.ndarray:
    """(..., ) angles in degrees -> (..., 2 * len(HARMONICS)) as [cos k1, sin k1, cos k2, sin k2, ...]."""
    t = np.radians(np.asarray(theta_deg, dtype=np.float64))[..., None] * np.array(HARMONICS)
    return np.stack([np.cos(t), np.sin(t)], axis=-1).reshape(*t.shape[:-1], -1)


# ── The sky on a date (shared by everyone) ───────────────────────────────────

@lru_cache(maxsize=200_000)
def sky_state(jd: float, bodies: tuple[str, ...], helio: bool) -> dict:
    """Longitudes (sidereal), speeds, declinations, out-of-bounds; heliocentric longitudes if asked."""
    swe, flags = F._swe()
    ids = _ids(swe)
    lon, speed, dec = [], [], []
    for b in bodies:
        c = swe.calc_ut(jd, ids[b], flags | swe.FLG_SPEED)[0]
        lon.append(c[0])
        speed.append(c[3])
        dec.append(swe.calc_ut(jd, ids[b], swe.FLG_MOSEPH | swe.FLG_EQUATORIAL)[0][1])
    eps = swe.calc_ut(jd, swe.ECL_NUT)[0][0]
    dec = np.array(dec)
    out = {"lon": np.array(lon), "speed": np.array(speed), "dec": dec, "oob": np.maximum(0.0, np.abs(dec) - eps)}
    if helio:
        out["helio"] = np.array([swe.calc_ut(jd, ids[b], swe.FLG_MOSEPH | swe.FLG_HELCTR)[0][0]
                                 for b in HELIO_BODIES])
    return out


# ── Featurizer (plugs into models.matrix and validation.*) ───────────────────

class HarmonicFeaturizer:
    """Same interface as models.Featurizer, with float32 output."""
    dtype = np.float32

    def __init__(self, include_moon: bool = False, helio: bool = False):
        self.bodies = tuple((["Moon"] if include_moon else []) + TRANSIT_BODIES)
        self.helio = helio
        nb = len(self.bodies)
        self._sky_pairs = [(i, j) for i in range(nb) for j in range(i + 1, nb)]
        self._helio_pairs = [(i, j) for i in range(len(HELIO_BODIES)) for j in range(i + 1, len(HELIO_BODIES))]
        enc = [f"{c}{k}" for k in HARMONICS for c in ("cos", "sin")]
        names = [f"sky {self.bodies[i]}-{self.bodies[j]} {e}" for i, j in self._sky_pairs for e in enc]
        names += [f"transit {b} to natal {n} {e}" for b in self.bodies for n in NATAL_POINTS for e in enc]
        names += [f"{b} {q}" for b in self.bodies for q in ("speed ratio", "declination", "out of bounds")]
        if helio:
            names += [f"helio {HELIO_BODIES[i]}-{HELIO_BODIES[j]} {e}" for i, j in self._helio_pairs for e in enc]
        self.names = names
        self.n = len(names)
        self.name = f"harmonic{'+moon' if include_moon else ''}{'+helio' if helio else ''}"
        self._mean_speed = np.array([MEAN_SPEED[b] for b in self.bodies])

    def context(self, s: dict) -> dict:
        """Natal points. Sun..Node and the Ascendant come from s['natal'] (so mismatched_chart_c swaps them);
        Uranus, Neptune, Pluto and the Midheaven are computed from s['birth_jd'] and the birth place, which
        that test keeps as the person's own."""
        swe, flags = F._swe()
        nat = s["natal"]
        pts = {p: float(nat[NATAL.index(p)]) for p in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")}
        pts["Node"] = float(nat[NATAL.index("Rahu")])
        ids = _ids(swe)
        for p in ("Uranus", "Neptune", "Pluto"):
            pts[p] = swe.calc_ut(s["birth_jd"], ids[p], flags)[0][0]
        asc = float(nat[NATAL.index("Ascendant")])
        pts["Ascendant"] = asc
        pts["Midheaven"] = math.nan
        if not math.isnan(asc) and s.get("lat") is not None and s.get("lon") is not None:
            pts["Midheaven"] = swe.houses_ex(s["birth_jd"], s["lat"], s["lon"], b"W", swe.FLG_SIDEREAL)[1][1]
        return {"natal": np.array([pts[p] for p in NATAL_POINTS]), "birth_jd": s["birth_jd"]}

    def features(self, ctx: dict, jd: float) -> np.ndarray:
        sky = sky_state(float(jd), self.bodies, self.helio)
        lon = sky["lon"]
        i, j = np.array(self._sky_pairs).T
        parts = [encode((lon[i] - lon[j]) % 360).ravel(),
                 encode((lon[:, None] - ctx["natal"][None, :]) % 360).ravel(),   # NaN natal -> NaN features
                 np.stack([sky["speed"] / self._mean_speed, sky["dec"], sky["oob"]], axis=1).ravel()]
        if self.helio:
            h = sky["helio"]
            a, b = np.array(self._helio_pairs).T
            parts.append(encode((h[a] - h[b]) % 360).ravel())
        return np.concatenate(parts).astype(np.float32)

    def age_clock_columns(self) -> np.ndarray:
        clock = {f"transit {b} to natal {b} " for b in SLOW}
        return np.array([k for k, n in enumerate(self.names) if any(n.startswith(c) for c in clock)])

    def default_columns(self) -> np.ndarray:
        return np.setdiff1d(np.arange(self.n), self.age_clock_columns())

    def groups(self) -> dict[str, np.ndarray]:
        """Column indexes per block, for ablations: sky-only, natal-only, kinematics, helio."""
        out: dict[str, list[int]] = {"sky": [], "natal": [], "kin": [], "helio": []}
        for k, n in enumerate(self.names):
            out["sky" if n.startswith("sky ") else "natal" if n.startswith("transit ") else
                "helio" if n.startswith("helio ") else "kin"].append(k)
        return {g: np.array(v) for g, v in out.items() if v}


class AgeBaseline:
    """One feature: age in years. The bar every harmonic result has to clear — with flexible models,
    knowing only the age already beats same-person control dates when events cluster at certain ages."""
    name, n, dtype = "age_baseline", 1, np.float32
    names = ["age in years"]

    def context(self, s: dict) -> dict:
        return {"birth_jd": s["birth_jd"]}

    def features(self, ctx: dict, jd: float) -> np.ndarray:
        return np.array([(jd - ctx["birth_jd"]) / 365.2422], np.float32)

    def default_columns(self) -> np.ndarray:
        return np.arange(1)


def shap_importance(model, X: np.ndarray, M: np.ndarray, columns: np.ndarray, names: list[str],
                    top: int = 30) -> list[tuple[str, float]]:
    """Mean |SHAP| per feature over the valid dates, via LightGBM's built-in TreeSHAP (pred_contrib)."""
    n, k, _ = X.shape
    rows = X[:, :, columns].reshape(n * k, -1)[M.reshape(-1)].astype(np.float32)
    contrib = model.predict(rows, pred_contrib=True)[:, :-1]            # last column is the bias
    imp = np.abs(contrib).mean(0)
    order = np.argsort(-imp)[:top]
    return [(names[columns[i]], round(float(imp[i]), 6)) for i in order]
