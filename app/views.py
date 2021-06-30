import os
from flask import Flask, render_template, send_from_directory, redirect, url_for

app = Flask(__name__)


@app.route('/favicon.ico')
def fav():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico')

@app.route('/')
def calculatrice():
    return render_template('calculatrice.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#global-------------------------------------------------------------------

#if __name__ == "__main__":
#    app.run()