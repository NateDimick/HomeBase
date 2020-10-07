from flask import Flask, render_template, request, redirect, jsonify
from flask_cors import CORS
import json, psutil, socket, gpiozero, requests, sqlite3
from os.path import join, expanduser, exists, dirname
import sys
from datetime import datetime
import nfl

app = Flask(__name__)
CORS(app)
hostname = socket.gethostname()

users = ["ubuntu", "nate"]

# this list is like a brainstorm/ roadmap of what I'd like to implement in the future
features = [
    ("chupbot", "@chupeverything management"),
    ("raspi", "Hardware Monitor"),
    ("dice", "DnD dice roller"),
    ("nfl", "NFL Over/Under Data"),
    ("betting", "Sports Betting Calculators"),
    ("deisbot", "u/BrandeisBot management"),
    ("lights", "Smart Home Light management"),
    ("fun", "Random Shenanigans"),
    ("todo", "my to-do list")
]
@app.route("/")
def index():
    return render_template("index.html", links=features)

@app.route("/chupbot", methods=["GET", "POST"])
def chupbot():
    server_uname = ""
    for u in users:
        if exists(join("/home", u, "Projects/chupeverything/json/settings.json")):
            server_uname = u
            break

    if request.method == "GET":
        # open current settings and render them into the settings form
        with open(join("/home", server_uname, "Projects/chupeverything/json/settings.json"), 'r') as s:
            settings = json.load(s)
            settings = [(name, value, str(type(value))) for name, value in settings.items()]
            print(settings)
            return render_template("chupbot.html", settings=settings)
    else:
        # new data is posted to settings
        inputs = request.form
        with open(join("/home", server_uname, "Projects/chupeverything/json/settings.json"), 'r') as s:
            outputs = json.load(s)  # tomaintain consistancy, load the old settings as the outputs, and change values
        for i in inputs:
            typ, name = i.split("~")
            if typ == "n":
                # numbers - first convert to float, then convert to int if it is clearly and int
                value = float(inputs[i])
                if value == int(value):
                    value = int(value)
                outputs[name] = value
            elif typ == "b":
                # if a true boolean value is passed in. only true value will be passed in - unchecked boxes aren't included in the form
                value = 'on' == inputs[i]
                outputs[name] = value
            else:
                # form values default to being a string
                outputs[name] = inputs[i]
        present = [i.split('~')[1] for i in inputs]
        # make sure unchecked boxes result in false boolean values in the output
        for o in outputs:
            if o not in present and bool == type(outputs[o]):
                outputs[o] = False
        print(inputs, outputs)
        with open(join(expanduser("~"), "Projects/chupeverything/json/settings.json"), 'w') as s:
            json.dump(outputs, s)
        return redirect("/")

@app.route("/raspi")
def monitor():
    return render_template("raspi.html")

@app.route("/raspi/update")
def monitor_update():
    """
    returns json pertaining to current system status
    """
    cpu_load = psutil.cpu_percent()
    if hostname == "raspberryduck":
        cpu_temp = gpiozero.CPUTemperature().temperature
        print(f"temp: {cpu_temp}")
    else:
        cpu_temp = "not on raspi"
    return jsonify({"response": "Hello", "cpu_load": cpu_load, "host": hostname, "cpu_temp": f"{cpu_temp} C"})

@app.route("/dice")
def dice():
    return render_template("dice.html")

@app.route("/nfl")
def nflpage():
    # a little but of backend
    # * create db if db does not exist
    # * get teams
    new_db = nfl.create_db()
    if new_db:
        # get all info from the season so far...
        pass
    w = nfl.maxweek()
    y = datetime.today().year
    games = nfl.getweek(w, y)
    tabledata = []
    total_swing = 0
    for g in games:
        d = {}  # home, away, total, apt, pop, ppa, avg, ou
        d['home'] = g['hometeam'].lower().capitalize()
        d['away'] = g['awayteam'].lower().capitalize()
        d['total'] = g['booktotal']
        d['apt'], d['pop'], d['ppa'] = nfl.matchup_score_prediction(d['home'], d['away'])
        if d['total']:
            swing = sum([d[x] - d['total'] for x in ('apt', 'pop', 'ppa') if type(d['total'] == float)])
            d['ou'] = 'Over' if swing > 0 else 'Under'
            #d['ou'] += f" ({swing})"
            d['confidence'] = swing
            total_swing += abs(swing)
            print('swing', swing)
        else:
            d['ou'] = 'N/A'
            d['confidence'] = 0
        tabledata.append(d)
    for g in tabledata:
        pct = round(abs(g['confidence']) / total_swing * 100, 2)
        #g['ou'] += f" ({pct}%)"
        g['pct'] = pct


    return render_template('nfl.html', games=tabledata)

@app.route('/nfl/newweek')
def nflupdate():
    try:
        nfl.tuesday_update()
        return jsonify({"success": True})
    except:
        return jsonify({"success": False})

@app.route('/nfl/updateodds')
def odds_update():
    wn, js = nfl.get_betting_info(nfl.maxweek())
    nfl.update_lines(js)
    return redirect("/nfl")
