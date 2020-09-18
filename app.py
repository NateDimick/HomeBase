from flask import Flask, render_template, request, redirect, jsonify
from flask_cors import CORS
import json, psutil, socket, gpiozero
from os.path import join, expanduser

app = Flask(__name__)
CORS(app)
hostname = socket.gethostname()

features = [
    ("chupbot", "@chupeverything management"),
    ("raspi", "Hardware Monitor"),
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
    if request.method == "GET":
        # open current settings and render them into the settings form
        with open(join(expanduser("~"), "Projects/chupeverything/json/settings.json"), 'r') as s:
            settings = json.load(s)
            settings = [(name, value, str(type(value))) for name, value in settings.items()]
            print(settings)
            return render_template("chupbot.html", settings=settings)
    else:
        # new data is posted to settings
        inputs = request.form
        with open(join(expanduser("~"), "Projects/chupeverything/json/settings.json"), 'r') as s:
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
