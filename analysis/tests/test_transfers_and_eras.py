import pandas as pd

from analysis.models.manager_eras import common_xi, label_position, rating, record, seasons_in_charge
from analysis.models.transfer_roi import best_and_worst, evaluate, signings, value_score


def transfers() -> pd.DataFrame:
    return pd.DataFrame([
        {"season": 2010, "team": "u", "direction": "in", "player_id": "1", "player": "Good Buy", "age": 22, "position": "CF", "other_club": "X", "fee_text": "€20m", "fee_eur": 2e7, "is_loan": False, "fee_gbp_real": 20e6},
        {"season": 2010, "team": "u", "direction": "in", "player_id": "2", "player": "Flop", "age": 27, "position": "AM", "other_club": "Y", "fee_text": "€60m", "fee_eur": 6e7, "is_loan": False, "fee_gbp_real": 60e6},
        {"season": 2010, "team": "u", "direction": "in", "player_id": "3", "player": "Cheap", "age": 20, "position": "CB", "other_club": "Z", "fee_text": "€2m", "fee_eur": 2e6, "is_loan": False, "fee_gbp_real": 2e6},
        {"season": 2012, "team": "u", "direction": "out", "player_id": "2", "player": "Flop", "age": 29, "position": "AM", "other_club": "W", "fee_text": "€5m", "fee_eur": 5e6, "is_loan": False, "fee_gbp_real": 5e6},
    ])


def squad() -> pd.DataFrame:
    rows = []
    for s in (2010, 2011, 2012):
        rows.append({"season": s, "team": "u", "player_id": "1", "player": "Good Buy", "age": 22, "apps": 36, "goals": 15, "assists": 5, "subs_on": 2, "minutes": 3000})
    rows.append({"season": 2010, "team": "u", "player_id": "2", "player": "Flop", "age": 27, "apps": 8, "goals": 0, "assists": 1, "subs_on": 6, "minutes": 300})
    return pd.DataFrame(rows)


def test_roi_metrics() -> None:
    sig = signings(transfers(), ["u"])
    assert set(sig["player"]) == {"Good Buy", "Flop"}  # under-£10m signing excluded
    roi = evaluate(sig, transfers(), squad(), {2010: 38, 2011: 38, 2012: 38}, current_season=2012).set_index("player")
    assert roi.loc["Good Buy", "league_minutes"] == 9000
    assert roi.loc["Good Buy", "still_at_club"]
    assert roi.loc["Flop", "sale_fee_gbp_real"] == 5e6
    assert roi.loc["Flop", "net_cost_gbp_real"] == 55e6
    assert roi.loc["Flop", "cost_per_1000_min"] > roi.loc["Good Buy", "cost_per_1000_min"]
    assert pd.isna(roi.loc["Flop", "ga_per90"])  # under 450 minutes: not computed
    roi = roi.reset_index()
    scores = value_score(roi)
    assert scores[roi["player"] == "Good Buy"].iloc[0] > scores[roi["player"] == "Flop"].iloc[0]
    bw = best_and_worst(roi, n=1, min_seasons_done=0)
    assert bw["u"]["best"][0]["player"] == "Good Buy"


def test_label_position() -> None:
    assert label_position(80, 40) == "GK"
    assert label_position(63, 28) == "CB"
    assert label_position(61, 7.5) == "LB"
    assert label_position(2, 40) == "ST"
    assert label_position(61, 7.5, back_three=True) == "CB"


def test_name_from_slug() -> None:
    from analysis.export import name_from_slug

    assert name_from_slug("edwin-van-der-sar") == "Edwin van der Sar"
    assert name_from_slug("nemanja-vidic-lrm") == "Nemanja Vidic"


def test_common_xi_unique_players() -> None:
    rows = []
    for m in range(5):
        for k in range(11):
            pid = f"p{k}" if not (m == 4 and k == 1) else "p0b"
            rows.append({"report_id": str(m), "formation": "4-4-2", "player_id": pid, "name": pid, "top": float(k * 7), "left": float(k * 5)})
    xi = common_xi(pd.DataFrame(rows))
    assert xi is not None and xi["formation"] == "4-4-2"
    assert len(xi["xi"]) == 11 and len({p["player_id"] for p in xi["xi"]}) == 11
    assert xi["exact_xi"]["times"] == 4


def test_record_and_rating() -> None:
    games = pd.DataFrame({"result": ["W", "D", "L", "W"], "pts": [3, 1, 0, 3], "gf": [2, 1, 0, 3], "ga": [0, 1, 2, 1], "season": [2000] * 4})
    r = record(games)
    assert r["w"] == 2 and r["l"] == 1 and abs(r["ppg"] - 1.75) < 1e-12
    assert rating(None, 0, 1) is None and rating(2.0, 0, 1) == 99
    assert seasons_in_charge(games, {2000: 6}) == [2000]
    assert seasons_in_charge(games, {2000: 38}) == []
