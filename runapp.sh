#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export FLASK_APP=$(pwd)/app.py
export FLASK_DEBUG=1
flask run -h 0.0.0.0
deactivate
