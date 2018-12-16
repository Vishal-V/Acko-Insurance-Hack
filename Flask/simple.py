from flask import Flask, render_template
from fire import firepred
from landslide import landpred

app = Flask(__name__, static_url_path="", static_folder="static")

@app.route('/')
def index():
    return render_template("index.html", title='Acko Hack')

@app.route('/fire')
def firepre():
    return render_template("fire.html", title='Fire Prediction')

@app.route('/land')
def landpre():
    return render_template("landslide.html", title='Landslide prediction')

@app.route("/analyse")
def analyse():
	return render_template("Insurance.html", title='Insurance')

@app.route("/map")
def map():
	return render_template("map.html", title='Map')

app.run(debug=True)