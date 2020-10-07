from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json, time, sqlite3, datetime
from os.path import exists, join

def get_game_results(week: int=0):
    opt = Options()
    opt.headless = True
    driver = webdriver.Chrome(options=opt)
    if week:
        driver.get(f"https://foxsports.com/nfl/scores?seasonType=1&week={week}")
    else:
        driver.get(f"https://foxsports.com/nfl/scores")
    games = []
    while not games:
        html = driver.execute_script("return document.documentElement.outerHTML")
        soup = BeautifulSoup(html, 'html.parser')
        try:
            week_from_page = soup.find('div', {'class': 'scores-scorechips-container layout-content-container'}).find('h2', {'class': 'section-title'}).decode_contents()
        except:
            week_from_page = "no such element yet..."
        print(week_from_page)

        final_scores = []
        games = soup.findAll("div", {"class": "teams"})
        time.sleep(1)
        print("page loading...")
    print(len(games), "games")
    week_num = int(week_from_page.split()[1])
    for g in games:
        teams = g.findAll("div", {"class": "score-team-row"})
        print(len(teams), "teams")  # should always be 2
        game = {}
        i = 0
        for t in teams:
            i += 1
            name = t.find("div", {"class": "score-team-name team"}).find("span", {"class": "scores-text uc"}).decode_contents()
            try:
                score = t.find("div", {"class": "score-team-score"}).find("span", {"class": "scores-text uc"}).decode_contents()
            except:
                print(name, 'no score')
                score = 'noscore'
            n = None
            for s in score.split():
                try:
                    n = int(s)
                except:
                    pass
            score = n 
            game[name] = score
            if i == 1:
                game['AWAY'] = name
            elif i == 2:
                game['HOME'] = name
        final_scores.append(game)
    """
    with open("scoretest.json", "w") as f:
        json.dump(final_scores, f)
    """
    driver.close()
    return week_num, final_scores

def get_betting_info(week: int=0):
    opt = Options()
    opt.headless = True
    driver = webdriver.Chrome(options=opt)
    if week:
        driver.get(f"https://foxsports.com/nfl/scores?seasonType=1&week={week}")
    else:
        driver.get(f"https://foxsports.com/nfl/scores")
    games = []
    while not games:
        html = driver.execute_script("return document.documentElement.outerHTML")
        soup = BeautifulSoup(html, 'html.parser')
        try:
            week_from_page = soup.find('div', {'class': 'scores-scorechips-container layout-content-container'}).find('h2', {'class': 'section-title'}).decode_contents()
        except:
            week_from_page = "no such element yet..."
        print(week_from_page)

        games = soup.findAll("div", {"class": "score-chip-content"})
        time.sleep(1)
        print("page loading...")
    output = []
    for g in games:
        odds = g.find("div", {"class": "score-game-info odds-game-info"})
        try:
            over_under = float(odds.findAll("span")[1].decode_contents().split()[1])
        except:
            over_under = None
        out = f"{over_under} "
        teams = g.findAll("div", {"class": "score-team-row"})
        names = []
        for t in teams:
            name = t.find("div", {"class": "score-team-name team"}).find("span", {"class": "scores-text uc"}).decode_contents()
            names.append(name)
        """
        proj, off, dst = matchup_score_prediction(names[0], names[1])
        out += f"| {proj} | {names[0]} | {names[1]} | offense: {off} | defense: {dst}"
        print(out)
        """
        output.append({"HOME": names[1], "AWAY": names[0], "TOTAL": over_under})
    return int(week_from_page.split()[1]), output
    

def create_db():
    if not exists('nfl.db'):
        conn = sqlite3.connect('nfl.db')
        curr = conn.cursor()
        with open(join('queries', 'schema.sql'), 'r') as q:
            curr.executescript(q.read())
        wn = pregame()  # get current week's data
        for w in range(1, wn):
            pregame(w)
            postgame(w)  # insert previous weeks data
        conn.commit()
        conn.close()
        return True
    return False

def maxweek():
    """
    gets the highest week number
    TODO: only get highest week number from current year
    """
    conn = sqlite3.connect('nfl.db')
    curr = conn.cursor()
    curr.execute('SELECT MAX(week) FROM Games;')
    week = curr.fetchall()[0][0]
    conn.close()
    return week


def insert_games(week_number, game_json):
    """
    peforms insertion of new games to the database
    """
    conn = sqlite3.connect('nfl.db')
    curr = conn.cursor()
    curr.execute('SELECT MAX (gameid) FROM Games;')
    last_gid = curr.fetchall()[0][0]
    gid = 1 + (last_gid if last_gid else 0)
    y = datetime.datetime.today().year
    for game in game_json:
        print(game)
        if type(game['TOTAL']) != float:
            game['TOTAL'] = None
        curr.execute('INSERT INTO Games (gameid, week, season, booktotal) VALUES (?, ?, ?, ?);', (gid, week_number, y, game['TOTAL']))
        curr.execute('INSERT INTO Scores (gameid, hometeam, awayteam) VALUES (?, ?, ?);', (gid, game['HOME'], game['AWAY']))
        gid += 1
    conn.commit()
    conn.close()

def update_lines(game_json):
    """
    updates sportsbook totals
    """
    conn = sqlite3.connect('nfl.db')
    curr = conn.cursor()
    for game in game_json:
        ht = game['HOME']
        at = game['AWAY']
        curr.execute('SELECT MAX(gameid) FROM Scores WHERE hometeam = ? AND awayteam = ?;', (ht, at))
        gid = curr.fetchall()[0][0]
        curr.execute('UPDATE Games SET booktotal = ? WHERE gameid = ?', (game['TOTAL'], gid))
    conn.commit()
    conn.close()


def update_most_recent_scores(game_json):
    conn = sqlite3.connect('nfl.db')
    curr = conn.cursor()
    for game in game_json:
        ht = game['HOME']
        hs = game[ht]
        at = game['AWAY']
        ws = game[at]
        curr.execute('SELECT MAX(gameid) FROM Scores WHERE hometeam = ? AND awayteam = ?;', (ht, at))
        gid = curr.fetchall()[0][0]
        curr.execute('UPDATE Scores SET homescore = ?, awayscore = ? WHERE gameid = ?;', (hs, ws, gid))
    conn.commit()
    conn.close()


def opp_scoring_avg(team, thru=None):
    conn = sqlite3.connect('nfl.db')
    curr = conn.cursor()
    if not thru:
        curr.execute('SELECT * FROM Scores WHERE hometeam = ? OR awayteam = ?;', [team.upper()] * 2)
    else:
        curr.execute('SELECT * FROM Scores, Games WHERE (hometeam = ? OR awayteam = ?) AND Scores.gameid = Games.gameid AND week < ?;', (team.upper(), team.upper(), thru))
    res = curr.fetchall()
    conn.close()
    pts = 0
    gms = 0
    for row in res:
        t = row.index(team.upper())
        s = 5 - t
        if row[s] != None:
            gms += 1
            pts += row[s]
    return pts/gms

def scoring_avg(team, thru=None):
    conn = sqlite3.connect('nfl.db')
    curr = conn.cursor()
    if not thru:
        curr.execute('SELECT * FROM Scores WHERE hometeam = ? OR awayteam = ?;', [team.upper()] * 2)
    else:
        curr.execute('SELECT * FROM Scores, Games WHERE (hometeam = ? OR awayteam = ?) AND Scores.gameid = Games.gameid AND week < ?;', (team.upper(), team.upper(), thru))
    res = curr.fetchall()
    conn.close()
    pts = 0
    gms = 0
    for row in res:
        t = row.index(team.upper())
        s = t + 2
        if row[s] != None:
            gms += 1
            pts += row[s]
    return pts/gms

def matchup_score_prediction(t1, t2, w=None):
    t1pf = scoring_avg(t1, thru=w)
    t1pa = opp_scoring_avg(t1, thru=w)
    t2pf = scoring_avg(t2, thru=w)
    t2pa = opp_scoring_avg(t2, thru=w)
    print(t1pf, t1pa, t2pf, t2pa)
    t1_proj = (t1pf + t2pa) / 2
    t2_proj = (t2pf + t1pa) / 2
    # return projected average total, pure offense projection, pure defense projection
    return round(t1_proj + t2_proj), round(t1pf + t2pf), round(t1pa + t2pa)

def getweek(week, season):
    conn = sqlite3.connect('nfl.db')
    conn.row_factory = sqlite3.Row
    curr = conn.cursor()
    curr.execute('SELECT * FROM Games, Scores WHERE Games.gameid = Scores.gameid AND week = ? AND season = ?;', (week, season))
    res = curr.fetchall()
    conn.close()
    return res

def over_under_record():
    mw = maxweek()
    y = datetime.datetime.today().year
    p = [0,0,0]
    o = [0,0,0]
    d = [0,0,0]
    b = [0,0,0]
    if mw > 2:
        for week in range(2, mw):
            w = getweek(week, y)
            for game in w:
                try:
                    actual_score = game['homescore'] + game['awayscore']
                except:
                    continue
                book_total = game['booktotal']
                print(game['hometeam'], game['awayteam'], week)
                projection, offense, def_allowed = matchup_score_prediction(game['hometeam'], game['awayteam'], w=week)
                if projection > actual_score:
                    p[1] += 1  # projection was too high
                elif projection < actual_score:
                    p[0] += 1  # projecttion was too low
                else:
                    p[2] += 1

                if offense > actual_score:
                    o[1] += 1  # projection was too high
                elif offense < actual_score:
                    o[0] += 1  # projecttion was too low
                else:
                    o[2] += 1

                if def_allowed > actual_score:
                    d[1] += 1  # projection was too high
                elif def_allowed < actual_score:
                    d[0] += 1  # projecttion was too low
                else:
                    d[2] += 1
                
                if book_total:
                    if book_total < actual_score:
                        b[0] += 1
                    elif book_total > actual_score:
                        b[1] += 1
                    else:
                        b[2] += 1
                print(f"{game['awayteam']} @ {game['hometeam']}: {actual_score} pts, {projection} projected, ({offense}, {def_allowed})")
    print('projections', p)
    print('offense', o)
    print('pts allowed', d)
    print('sportsbook', b)



def pregame(week=0):
    wn, js = get_betting_info(week)
    if wn == maxweek():
        update_lines(js)
    else:
        insert_games(wn, js)
    return wn

def postgame(week=0):
    wn, js = get_game_results(week)
    update_most_recent_scores(js)
    return wn

def tuesday_update():
    week = postgame()
    pregame(week + 1)

if __name__ == '__main__':
    """
    create_db()
    for w in range(1, 5):
        pregame(w)
    for w in [1, 2, 3]:
        postgame(w)
    """
    """
    print(matchup_score_prediction('packers', 'falcons'))
    week4 = getweek(4, 2020)
    print(week4)
    print(week4[0]['hometeam'])
    print(week4[0][3])
    print([x for x in week4[0]])
    """
    #wn = postgame()
    #pregame(5)
    over_under_record()