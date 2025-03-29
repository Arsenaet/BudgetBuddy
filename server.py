from flask import Flask, render_template, request
import requests
from waitress import serve

app = Flask(__name__)

@app.route("/")
@app.route("/index")
def index():
    pass
    # return an html template

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000)