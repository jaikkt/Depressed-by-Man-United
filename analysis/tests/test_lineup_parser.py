from analysis.ingest.transfermarkt_lineups import parse_fixtures, parse_report

REPORT = """
<div class="box"><h2>Line-Ups</h2>
<div class="large-6 columns aufstellung-box">
  <a class="sb-vereinslink" href="/manchester-united/startseite/verein/985/saison_id/1998">Manchester United</a>
  <div class="formation-subtitle">Starting Line-up: 4-4-2</div>
  <div class="formation-player-container" style="top: 80%; left: 40%;">
    <div class="tm-shirt-number">1</div><a href="/peter-schmeichel/profil/spieler/3465">Schmeichel</a></div>
  <div class="formation-player-container" style="top: 2%; left: 30%;">
    <div class="tm-shirt-number">9</div><a href="/andy-cole/profil/spieler/3333">Cole</a></div>
  <a href="/alex-ferguson/profil/trainer/4">Alex Ferguson</a>
</div>
<div class="large-6 columns aufstellung-box">
  <a class="sb-vereinslink" href="/leicester-city/startseite/verein/1003/saison_id/1998">Leicester</a>
  <div class="formation-player-container" style="top: 80%; left: 40%;"><a href="/kasey-keller/profil/spieler/1">Keller</a></div>
</div></div>
"""

FIXTURES = """
<div class="box"><h2>Premier League</h2><table><tbody>
<tr><td>1</td><td>Sat 15/08/1998</td><td>2:00 PM</td><td>H</td><td>(1.)</td><td></td><td>Leicester (10.)</td><td>4-5-1</td><td>55.052</td>
<td><a href="/spielbericht/index/spielbericht/1149602">2:2</a></td></tr>
<tr><td>2</td><td>Sat 22/08/2026</td><td>3:00 PM</td><td>A</td><td></td><td></td><td>Fulham</td><td>?</td><td></td>
<td><a href="/spielbericht/index/spielbericht/999">-:-</a></td></tr>
</tbody></table></div>
<div class="box"><h2>FA Cup</h2><table><tbody>
<tr><td>1</td><td>Sat 01/01/1999</td><td>3:00 PM</td><td>H</td><td></td><td></td><td>Spurs</td><td>?</td><td></td>
<td><a href="/spielbericht/index/spielbericht/5">1:0</a></td></tr>
</tbody></table></div>
"""


def test_parse_report_reads_only_united() -> None:
    rows = parse_report(REPORT, "1149602", 1998)
    assert [r.short_name for r in rows] == ["Schmeichel", "Cole"]
    assert rows[0].formation == "4-4-2" and rows[0].manager == "Alex Ferguson"
    assert rows[0].top == 80.0 and rows[1].left == 30.0
    assert rows[1].player_slug == "andy-cole"


def test_parse_fixtures_league_only_and_played_only() -> None:
    fx = parse_fixtures(FIXTURES, 1998)
    assert len(fx) == 1
    assert fx[0].report_id == "1149602" and fx[0].opponent == "Leicester" and fx[0].date == "15/08/1998"

AWAY_AND_LIST = """
<div class="box"><h2>Line-Ups</h2>
<div class="large-6 columns aufstellung-box"><a class="sb-vereinslink" href="/crystal-palace/startseite/verein/873/saison_id/1992">Palace</a></div>
<div class="large-6 columns">
  <a class="sb-vereinslink" href="/manchester-united/startseite/verein/985/saison_id/1992">Manchester United</a>
  <table>
    <tr><td><b>Goalkeeper</b></td><td><a href="/peter-schmeichel/profil/spieler/3465">Peter Schmeichel</a></td></tr>
    <tr><td><b>Defenders</b></td><td><a href="/a/profil/spieler/1">A</a>, <a href="/b/profil/spieler/2">B</a>, <a href="/c/profil/spieler/3">C</a>, <a href="/d/profil/spieler/4">D</a></td></tr>
    <tr><td><b>Midfield</b></td><td><a href="/e/profil/spieler/5">E</a>, <a href="/f/profil/spieler/6">F</a>, <a href="/g/profil/spieler/7">G</a>, <a href="/h/profil/spieler/8">H</a></td></tr>
    <tr><td><b>Forwards</b></td><td><a href="/i/profil/spieler/9">I</a>, <a href="/j/profil/spieler/10">J</a></td></tr>
  </table>
</div></div>
"""


def test_list_style_away_report_infers_formation() -> None:
    rows = parse_report(AWAY_AND_LIST, "1", 1992)
    assert len(rows) == 11
    assert all(r.inferred for r in rows)
    assert rows[0].formation == "4-4-2" and rows[0].top == 80.0
    assert rows[1].left < rows[4].left  # spread left to right across the line
