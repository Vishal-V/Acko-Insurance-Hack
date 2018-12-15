from flask import Flask, redirect, url_for, request
from fire import firepred
from landslide import landpred
from flask import Flask, render_template, jsonify, request, redirect, url_for
app=Flask(__name__, static_url_path="", static_folder="static")

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/fire')
def firepre():
    return render_template("fire.html")

@app.route('/land')
def landpre():
    return render_template("landslide.html")
