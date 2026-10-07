"""tests/test_bphs_dasha.py — the BPHS ch. 48 dasha code against the book's own tables and worked examples."""
from src.rules import bphs_dasha as D

NAK, PADA = 360 / 27, 360 / 108


def test_vimshottari_matches_book_examples_and_table_28():
    from src import features as F
    # p. 12: Moon Scorpio 14d29m -> Anuradha (Saturn), balance 3y1m10d (= 1120 days of 360 -> 3.111 y)
    v = D.vimshottari(7 * 30 + 14 + 29 / 60, 0.0, 0.0)
    assert v['MD']['lord'] == 'Saturn'
    assert abs((v['MD']['length'] - v['MD']['elapsed']) - 19 * 131 / 800) < 1e-9
    # Table-28 p. 181: Sun MD -> Sun AD 0.3 y, Moon AD 0.5 y
    v = D.vimshottari(26.67 + 0.0001, 0.0, 0.0)                    # start of Krittika = start of Sun MD
    assert v['MD']['lord'] == 'Sun' and v['AD']['lord'] == 'Sun' and abs(v['AD']['length'] - 0.3) < 1e-9
    v = D.vimshottari(26.67 + 0.0001, 0.0, 0.31 * D.YEAR)
    assert v['AD']['lord'] == 'Moon' and abs(v['AD']['length'] - 0.5) < 1e-9
    # same lords as the study's original implementation
    for moon, days in ((12.3, 5000), (200.1, 20000), (333.3, 9000)):
        i, j, k = F.vimshottari_at(moon, 0.0, days)
        v = D.vimshottari(moon, 0.0, days)
        assert (v['MD']['lord'], v['AD']['lord'], v['PD']['lord']) == (F.DASHA_LORDS[i], F.DASHA_LORDS[j], F.DASHA_LORDS[k])


def test_kalachakra_tables_match_paramayu_and_table_14b():
    assert [D.PARAMAYU[a] for a in range(12)] == [100, 85, 83, 86] * 3            # v. 89
    # Table-14B (p. 47), Rohini pada 1..4 and Mrigashira pada 1..4
    rohini = [D.kalachakra_natal(3 * NAK + q * PADA + 0.1)['seq'] for q in range(4)]
    assert rohini[0] == [8, 9, 10, 11, 0, 1, 2, 4, 3]                             # Sg Cp Aq Pi Ar Ta Ge Le Cn
    assert rohini[1] == [5, 6, 7, 11, 10, 9, 8, 7, 6]
    assert rohini[2] == [5, 4, 3, 2, 1, 0, 8, 9, 10]
    assert rohini[3] == [11, 0, 1, 2, 4, 3, 5, 6, 7]
    mrig = [D.kalachakra_natal(4 * NAK + q * PADA + 0.1)['seq'] for q in range(4)]
    assert mrig[0] == [11, 10, 9, 8, 7, 6, 5, 4, 3]
    assert mrig[1] == [2, 1, 0, 8, 9, 10, 11, 0, 1]
    assert mrig[3] == [8, 7, 6, 5, 4, 3, 2, 1, 0]
    # Table-22 labels: Rohini Sc Li Vi Le; Mrigashira Cn Ge Ta Ar; Ardra Pi Aq Cp Sg
    assert [D.kalachakra_natal(3 * NAK + q * PADA + 0.1)['amsa'] for q in range(4)] == [7, 6, 5, 4]
    assert [D.kalachakra_natal(4 * NAK + q * PADA + 0.1)['amsa'] for q in range(4)] == [3, 2, 1, 0]
    assert [D.kalachakra_natal(5 * NAK + q * PADA + 0.1)['amsa'] for q in range(4)] == [11, 10, 9, 8]
    # v. 77: Ardra follows Mrigashira
    assert D.kalachakra_natal(5 * NAK + 0.1)['seq'] == mrig[0]


def test_kalachakra_deha_jeeva():
    k = D.kalachakra_natal(0.1)                       # Ashwini 1: Deha Aries, Jeeva Sagittarius (v. 60)
    assert (k['deha'], k['jeeva'], k['savya']) == (0, 8, True)
    k = D.kalachakra_natal(3 * NAK + 0.1)             # Rohini 1: Deha Cancer, Jeeva Sagittarius (v. 73)
    assert (k['deha'], k['jeeva'], k['savya']) == (3, 8, False)


def test_kalachakra_example_8():
    """p. 64-65: Moon 0s 26d 47m -> 7' into Kritika pada 1 -> 3.5 years expired, Mars (Aries) dasha, 3.5 left."""
    moon = 26 + 47 / 60
    k = D.kalachakra(moon, 0.0, 0.0)
    assert k['amsa'] == 8 and k['sign'] == 0 and k['pos'] == 1
    assert abs(k['elapsed'] - 3.5) < 0.01
    later = D.kalachakra(moon, 0.0, 4 * D.YEAR)       # 7.5 y in: Taurus (16 y)
    assert later['sign'] == 1 and later['motion'] is None
    # Aries row: Ge -> Cn -> Le; Cn-Le is a Markati pair (v. 99)
    t = (7 + 16 + 9 + 21 + 1 - 3.5) * D.YEAR
    assert D.kalachakra(moon, 0.0, t)['sign'] == 4 and D.kalachakra(moon, 0.0, t)['motion'] == 'markati'
    assert D.kalachakra(moon, 0.0, 200 * D.YEAR) is None   # past the 9 dashas: not stated in the book


def test_kalachakra_apasavya_position_maps_to_savya_order():
    k = D.kalachakra(3 * NAK + 0.001, 0.0, 0.0)       # Rohini 1 at its start: first sign Sg = savya position 9
    assert k['sign'] == 8 and k['pos'] == 9 and k['amsa'] == 7


def test_kalachakra_antardasha_table_33_and_ch66_examples():
    # Table-33 (p. 474): Aries amsa, Aries dasha (7 y): antardashas Ar 0.49 y, Ta 1.12 y, Ge 0.63 y ...
    k = D.kalachakra(0.001, 0.0, 0.0)                         # Ashwini 1 at its very start: Aries dasha, Aries AD
    assert k['sign'] == 0 and k['ad_sign'] == 0
    assert D.kalachakra(0.001, 0.0, 0.50 * D.YEAR)['ad_sign'] == 1        # past 0.49 y -> Taurus AD
    assert D.kalachakra(0.001, 0.0, (0.49 + 1.12 + 0.01) * D.YEAR)['ad_sign'] == 2
    # Example 90 (p. 494): Swati pada 3 -> Savya, 83 years, Deha Taurus, Jeeva Gemini, 'Aquarius navamsa'
    k = D.kalachakra_natal(14 * NAK + 2 * PADA + 0.1)
    assert (k['savya'], k['paramayu'], k['deha'], k['jeeva'], k['amsa']) == (True, 83, 1, 2, 10)
    # Example 91 (p. 495): Ardra pada 4 -> Apasavya, 100 years, Deha Aries, Jeeva Sagittarius
    k = D.kalachakra_natal(5 * NAK + 3 * PADA + 0.1)
    assert (k['savya'], k['paramayu'], k['deha'], k['jeeva']) == (False, 100, 0, 8)
    # Example 92 (p. 497): Mrigashira pada 3 -> Apasavya, 85 years, Deha Capricorn, Jeeva Gemini
    k = D.kalachakra_natal(4 * NAK + 2 * PADA + 0.1)
    assert (k['savya'], k['paramayu'], k['deha'], k['jeeva']) == (False, 85, 9, 2)
    # Example 89 (p. 492): P.Bhadrapada pada 4 -> Savya, 86 years, Deha Cancer, Jeeva Pisces
    k = D.kalachakra_natal(24 * NAK + 3 * PADA + 0.1)
    assert (k['savya'], k['paramayu'], k['deha'], k['jeeva']) == (True, 86, 3, 11)


def test_chara_example_10_table_24():
    """p. 86-87, Capricorn Lagna. Verse rules reproduce 10 of the 12 printed years; Aq and Pi conflict (logged)."""
    signs = {'Jupiter': 11, 'Moon': 0, 'Sun': 1, 'Mars': 1, 'Mercury': 1, 'Venus': 3, 'Ketu': 4, 'Saturn': 5,
             'Rahu': 10}
    y = D.chara_years(signs)
    table = {9: 4, 8: 3, 7: 6, 6: 9, 5: 4, 4: 3, 3: 3, 2: 11, 1: 2, 0: 1}
    assert {s: y[s] for s in table} == table
    assert y[10] == 5 and y[11] == 12                 # verse 159 / notes p. 86 (table prints 12 and 1)
    assert D.chara_order(9)[:3] == [9, 8, 7]          # 9th = Virgo (even quarter) -> backward


def test_chara_example_9_order():
    assert D.chara_order(0)[:3] == [0, 1, 2]          # Aries Lagna, 9th Sagittarius odd -> forward (p. 85)


def test_ashtakavarga_tables_match_book_totals():
    from src.rules import bphs_av as AV
    for p, table in AV.REKHA.items():
        assert sum(len(h) for h in table.values()) == AV.TOTALS[p]
    b = AV.bav({'Sun': 0, 'Moon': 3, 'Mars': 5, 'Mercury': 1, 'Jupiter': 8, 'Venus': 11, 'Saturn': 6}, 2)
    assert all(sum(b[p]) == AV.TOTALS[p] for p in b)
    assert sum(AV.sav(b)) == 337                                  # 48+49+39+54+56+52+39


def test_shodhana_and_pinda_example_93():
    """Ch. 69-71, example 93 (Sun's AV): Trikona p. 544, Ekadhipatya p. 548, pindas 65 + 58 = 123 (pp. 552-553)."""
    from src.rules import bphs_av as AV
    rekhas = [6, 3, 5, 4, 3, 3, 3, 3, 3, 5, 5, 5]               # Aries..Pisces (p. 544)
    tri = AV.trikona_shodhana(rekhas)
    assert tri == [3, 0, 2, 1, 0, 0, 0, 0, 0, 2, 2, 2]
    signs = {'Sun': 4, 'Mercury': 4, 'Moon': 2, 'Mars': 2, 'Jupiter': 2, 'Venus': 3, 'Saturn': 3}
    eka = AV.ekadhipatya_shodhana(tri, set(signs.values()))
    assert eka == [3, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 2]
    assert AV.shodhya_pinda(eka, signs) == (65, 58)


def test_ashtakavarga_example_93_worked_through_ch72():
    """Model horoscope (Aries Lagna; Sun, Mercury Leo; Moon, Mars, Jupiter Gemini; Venus, Saturn Cancer).
    Book rows and pindas (pp. 544, 562-570). Moon and Venus differ because the worked example uses the common
    tables against the book's own chakras and verses; Saturn's pinda differs because the example does not apply
    its own Ekadhipatya rule III to Aries/Scorpio (both 3, both unoccupied) - logged."""
    from src.rules import bphs_av as A
    signs = {'Sun': 4, 'Mercury': 4, 'Moon': 2, 'Mars': 2, 'Jupiter': 2, 'Venus': 3, 'Saturn': 3}
    av = A.AV(signs, 0)
    assert av.rekhas['Sun'] == [6, 3, 5, 4, 3, 3, 3, 3, 3, 5, 5, 5] and av.pinda['Sun'] == 123
    assert av.rekhas['Mars'] == [5, 4, 5, 2, 1, 2, 3, 2, 4, 5, 3, 3] and av.pinda['Mars'] == 146
    assert av.rekhas['Mercury'] == [7, 5, 3, 7, 3, 4, 3, 4, 3, 7, 4, 4] and av.pinda['Mercury'] == 102
    assert av.rekhas['Jupiter'] == [7, 4, 5, 4, 5, 6, 3, 4, 7, 4, 3, 4] and av.pinda['Jupiter'] == 94
    assert av.rekhas['Saturn'] == [5, 6, 4, 2, 3, 3, 2, 5, 2, 2, 2, 3]
    assert av.saturn_years() == {'lagna_to_saturn': 17, 'saturn_to_lagna': 29, 'total': 46}
    # p. 564: Mercury, 4th = Scorpio (4 rekhas) x 102 = 408 -> Krittika (+U.Phalguni, U.Ashadha); Pisces (+Cn, Sc)
    assert av.point('Mercury', 4) == ({2, 11, 20}, {11, 3, 7})
    # p. 566: Jupiter, 5th = Libra (3) x 94 = 282 -> U.Phalguni (+U.Ashadha, Krittika); Virgo (+Cp, Ta)
    assert av.point('Jupiter', 5) == ({11, 20, 2}, {5, 9, 1})
    # p. 563: Mars, 3rd = Leo (1) x 146 -> remainder 11 = P.Phalguni (book misnames it Uttara; its trines match 11)
    assert av.point('Mars', 3) == ({10, 19, 1}, {1, 5, 9})


def test_ashtakavarga_longevity_ch73():
    """Table-37 and example 93 (p. 574): the Sun's AV contributes 12 y 0 m 10 d 12 h."""
    from src.rules import bphs_av as A
    sun = [6, 3, 5, 4, 3, 3, 3, 3, 3, 5, 5, 5]
    assert abs(A.ayu_years(sun) - (12 + 10.5 / 365.25)) < 1e-9


def test_samudaya_example_93():
    """Ch. 74 p. 579 table, rows not affected by the book's Moon/Venus table slip: Sun, Mars, Mercury, Jupiter,
    Saturn, Ascendant columns sum as printed once Moon and Venus rows are swapped for the book's."""
    from src.rules import bphs_av as A
    av = A.AV({'Sun': 4, 'Mercury': 4, 'Moon': 2, 'Mars': 2, 'Jupiter': 2, 'Venus': 3, 'Saturn': 3}, 0)
    assert av.rekhas['Lagna'] == [4, 4, 5, 4, 4, 5, 4, 6, 2, 3, 3, 5]          # p. 579 Ascendant row
    book_moon = [4, 5, 5, 1, 3, 4, 4, 5, 4, 4, 4, 6]
    book_venus = [7, 5, 4, 4, 4, 3, 6, 4, 2, 3, 6, 4]
    s = [av.samudaya[i] - av.rekhas['Moon'][i] - av.rekhas['Venus'][i] + book_moon[i] + book_venus[i] for i in range(12)]
    assert s == [45, 36, 36, 28, 26, 30, 28, 33, 27, 33, 30, 34]


def test_rays_example_94():
    """Ch. 75 example 94 (pp. 593-597): raw rays before moderation, written as rays and thirtieths."""
    from src.rules import bphs_rays as R
    lon = {'Sun': 4 * 30 + 20 + 23 / 60, 'Moon': 2 * 30 + 1 + 57 / 60, 'Mars': 2 * 30 + 9 + 55 / 60,
           'Mercury': 4 * 30 + 17 + 43 / 60, 'Venus': 3 * 30 + 17 + 12 / 60, 'Saturn': 3 * 30 + 29 + 59 / 60}
    # Moon excluded: the example subtracts 8s 3 deg (Sagittarius) though its own table gives Scorpio 3 deg (logged)
    book = {'Sun': 2 + 23 / 30, 'Mars': 1 + 10 / 30, 'Mercury': 4 + 7 / 30,  # units-thirtieths (sign-degree arithmetic)
            'Venus': 3 + 3 / 30, 'Saturn': 2 + 23 / 30}
    for p, v in book.items():
        assert abs(R.raw_rays(p, lon[p]) - v) < 1 / 30, p


def test_bphs_core_dignity_friendship_and_natures():
    """Vol. 1 ch. 3 v. 11, 49-58 (pp. 16-41)."""
    from src.rules import bphs_core as C
    assert C.dignity('Moon', 30 + 2) == 'exalted' and C.dignity('Moon', 30 + 10) == 'moolatrikona'
    assert C.dignity('Mercury', 150 + 10) == 'exalted' and C.dignity('Mercury', 150 + 17) == 'moolatrikona'
    assert C.dignity('Mercury', 150 + 25) == 'own'
    assert C.dignity('Sun', 120 + 25) == 'own' and C.dignity('Sun', 120 + 5) == 'moolatrikona'
    assert C.natural('Rahu', 'Jupiter') == 'friend' and C.natural('Rahu', 'Mercury') == 'neutral'
    assert C.natural('Ketu', 'Mars') == 'friend' and C.natural('Ketu', 'Jupiter') == 'neutral'
    # example p. 41: Sun's compound relations (Lagna chart p. 40): Mars, Jupiter extreme friends; Venus, Saturn extreme enemies
    signs = {'Sun': 3, 'Mercury': 3, 'Venus': 3, 'Ketu': 3, 'Jupiter': 4, 'Mars': 4, 'Saturn': 7, 'Moon': 11, 'Rahu': 9}
    assert C.compound('Sun', 'Mars', signs['Sun'], signs['Mars']) == 'great_friend'
    assert C.compound('Sun', 'Venus', signs['Sun'], signs['Venus']) == 'great_enemy'
    assert C.compound('Sun', 'Moon', signs['Sun'], signs['Moon']) == 'neutral'
    # v. 11: waning Moon malefic; Mercury with a malefic malefic
    lon = {'Sun': 100, 'Moon': 100 + 300, 'Mercury': 105}
    ben, mal = C.benefics_malefics(lon, {'Sun': 3, 'Moon': 1, 'Mercury': 3, 'Mars': 5, 'Saturn': 6, 'Rahu': 8, 'Ketu': 2})
    assert 'Moon' in mal and 'Mercury' in mal and 'Jupiter' in ben


def test_sphuta_drishti_book_examples():
    """Vol. 1 ch. 28 worked examples (pp. 362-375): the Moon's and Saturn's aspectual values."""
    from src.rules import bphs_core as C
    lon = lambda s, d, m=0, sec=0: s * 30 + d + m / 60 + sec / 3600
    moon = lon(0, 26, 47, 25)
    assert abs(C.drishti('Moon', moon, lon(3, 2, 39, 37)) - (20 + 52 / 60 + 12 / 3600)) < 1e-3     # Venus
    assert abs(C.drishti('Moon', moon, lon(4, 23, 35, 22)) - (31 + 36 / 60 + 1.5 / 3600)) < 1e-2   # Ketu
    assert C.drishti('Moon', moon, lon(1, 18, 8, 22)) == 0                                       # Sun, < 1 sign
    sat = lon(5, 3, 16, 14)
    assert abs(C.drishti('Saturn', sat, lon(10, 23, 35, 22)) - (40 + 38 / 60 + 16 / 3600)) < 1e-3  # Rahu, 5-6 signs
    assert abs(C.drishti('Saturn', sat, lon(11, 16, 19, 53)) - (53 + 28 / 60 + 10.5 / 3600)) < 1e-2  # Jupiter
    assert C.full_aspect('Saturn', 0, 2) and not C.full_aspect('Rahu', 0, 4)


def test_arudha_book_example():
    """Vol. 1 ch. 31 example (p. 421): Leo Lagna, Sun in Gemini -> Lagna pada Aries; 2nd (Virgo) lord Mercury in
    Cancer -> Taurus; notes p. 422: Leo Lagna, Sun in Leo -> Taurus; Sun in Aquarius -> Scorpio."""
    from src.rules import bphs_core as C
    assert C.arudha(4, 2) == 0
    assert C.arudha(5, 3) == 1
    assert C.arudha(4, 4) == 1
    assert C.arudha(4, 10) == 7


def test_pindayu_raw_years_book_example():
    """Vol. 1 ch. 45 example (pp. 580-583): raw pindas before reductions."""
    from src.rules import bphs_ayu as A
    lon = lambda s, d, m, sec: s * 30 + d + m / 60 + sec / 3600
    cases = {'Sun': (lon(1, 18, 8, 22), 16 + 11 / 12), 'Mars': (lon(1, 14, 28, 1), 10 + 6 / 12),
             'Mercury': (lon(1, 1, 5, 7), 7 + 6 / 12), 'Jupiter': (lon(11, 16, 19, 53), 10 + 5 / 12),
             'Venus': (lon(3, 2, 39, 37), 15 + 5 / 12), 'Saturn': (lon(5, 3, 16, 14), 17 + 4 / 12)}
    for p, (x, years) in cases.items():
        assert abs(A.raw_pinda(p, x) - years) < 0.1, p


def test_kp_chart_matches_reader5_example():
    """KP Reader V, 'Systematic procedure' example: Alibag 18N39 72E55, 9 PM IST 23-12-1924. The book's cusps (Raphael
    tables, Krishnamurti ayanamsa): I 18-22 Cancer, II 15-01 Leo, IV 17-01 Libra, VI 19-01 Sagittarius; Sun 8-51,
    Jupiter 8-32 Sagittarius, Venus 9-33 Scorpio, Rahu 23-23 Cancer."""
    import swisseph as swe
    from src.rules import kp_core as K
    k = K.KPChart(swe.julday(1924, 12, 23, 15.5), 18 + 39 / 60, 72 + 55 / 60)
    book_cusps = {1: 90 + 18 + 22 / 60, 2: 120 + 15 + 1 / 60, 4: 180 + 17 + 1 / 60, 6: 240 + 19 + 1 / 60}
    for h, v in book_cusps.items():
        assert abs((k.cusp[h] - v + 180) % 360 - 180) < 0.25
    book = {'Sun': 240 + 8 + 51 / 60, 'Jupiter': 240 + 8 + 32 / 60, 'Venus': 210 + 9 + 33 / 60, 'Rahu': 90 + 23 + 23 / 60}
    for p, v in book.items():
        assert abs((k.lon[p] - v + 180) % 360 - 180) < 0.1
