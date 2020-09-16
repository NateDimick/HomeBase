from flask import Flask, render_template, request, redirect
import json
from os.path import join, expanduser

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chupbot", methods=["GET", "POST"])
def chupbot():
    if request.method == "GET":
        with open(join(expanduser("~"), "Projects/chupeverything/json/settings.json"), 'r') as s:
            settings = json.load(s)
            settings = [(name, value, str(type(value))) for name, value in settings.items()]
            print(settings)
            return render_template("chupbot.html", settings=settings)
    else:
        inputs = request.form
        with open(join(expanduser("~"), "Projects/chupeverything/json/settings.json"), 'r') as s:
            outputs = json.load(s)
        for i in inputs:
            typ, name = i.split("~")
            if typ == "n":
                value = float(inputs[i])
                if value == int(value):
                    value = int(value)
                outputs[name] = value
            elif typ == "b":
                value = 'on' == inputs[i]
                outputs[name] = value
            else:
                outputs[name] = inputs[i]
        present = [i.split('~')[1] for i in inputs]
        for o in outputs:
            if o not in present and bool == type(outputs[o]):
                outputs[o] = False
        print(inputs, outputs)
        with open(join(expanduser("~"), "Projects/chupeverything/json/settings.json"), 'w') as s:
            json.dump(outputs, s)
        return redirect("/")