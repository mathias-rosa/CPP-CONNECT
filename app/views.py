import os
from flask import Flask, render_template, send_from_directory, redirect, url_for
import datetime

app = Flask(__name__)

@app.route('/favicon.ico')
def fav():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico')

@app.route('/')
def index():
    return render_template('index.html', year=datetime.date.today().year)

@app.route('/login/')
def login():
    return render_template('login.html')

@app.route('/signup/')
def signup():
    return render_template('signup.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# global-------------------------------------------------------------------

#if __name__ == "__main__":
#    app.run()