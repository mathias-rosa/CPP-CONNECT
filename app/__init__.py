import os
from flask import Flask, render_template, redirect, url_for, send_from_directory, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./db.db'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), unique=True)
    surname = db.Column(db.String(25), unique=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)
    darkmode = db.Column(db.Boolean)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('', validators=[InputRequired()])
    password = PasswordField('', validators=[InputRequired(), Length(min=6, max=80)])
    remember = BooleanField('Se rappeller de moi')

class RegisterForm(FlaskForm):
    name = StringField('', validators=[InputRequired()])
    surname = StringField('', validators=[InputRequired()])
    email = StringField('', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('', validators=[InputRequired(), Length(min=6, max=80)])
    password_confirm = PasswordField('', validators=[InputRequired(), Length(min=6, max=80)])

@app.route('/favicon.ico')
def fav():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico')

@app.route('/')
def index():
    darkmode_status = "lightmode"
    try:
        if current_user.darkmode == True:
            darkmode_status = 'darkmode'
    except:
        print("current_user n'existe pas")
    return render_template('index.html', 
                            year=datetime.date.today().year,
                            darkmode_status=darkmode_status,
                            )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    darkmode_status = "lightmode"
    try:
        if current_user.darkmode == True:
            darkmode_status = 'darkmode'
    except:
        print("current_user n'existe pas")
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data == form.password_confirm.data:
            hashed_password = generate_password_hash(form.password.data, method='sha256')
            username = form.surname.data.lower() + "." + form.name.data.lower()
            new_user = User(name=form.name.data.upper(),
                            surname=form.surname.data,
                            username=username,
                            email=form.email.data,
                            password=hashed_password,
                            admin=False)
            db.session.add(new_user)
            db.session.commit()
            user = User.query.filter_by(username=username).first()
            login_user(user)
            return redirect(url_for('dashboard'))

        return "<h1>Les mots de passe ne correspondent pas</h1>"

    return render_template('signup.html', 
                            form=form,
                            darkmode_status=darkmode_status,
                            )


@app.route('/login', methods=['GET', 'POST'])
def login():
    darkmode_status = "lightmode"
    try:
        if current_user.darkmode == True:
            darkmode_status = 'darkmode'
    except:
        print("current_user n'existe pas")
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        if "@" in username:
            user = User.query.filter_by(email=username).first()
        else:
            user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))

        return '<h1>Invalid username or password</h1>'

    return render_template('login.html', 
                            form=form,
                            darkmode_status=darkmode_status,
                            )


@app.route('/dashboard/')
@login_required
def dashboard():
    darkmode_status = "lightmode"
    if current_user.admin == 1:
        return redirect(url_for("admin"))
    else:
        if current_user.darkmode == True:
            darkmode_status = 'darkmode'
        return render_template('dashboard.html', 
                                current_user=current_user,
                                darkmode_status=darkmode_status,
                                )


@app.route('/admin-dashboard/')
@login_required
def admin():
    darkmode_status = "lightmode"
    if current_user.admin == 0:
        return redirect(url_for("dashboard"))
    else:
        if current_user.darkmode == True:
            darkmode_status = 'darkmode'
        userlist = [user for user in db.session.query(User)]
        return render_template('admin.html', 
                                current_user=current_user,
                                userlist=userlist,
                                darkmode_status=darkmode_status,
                                )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    darkmode_status = "lightmode"
    try:
        if current_user.darkmode == True:
            darkmode_status = 'darkmode'
    except:
        print("current_user n'existe pas")

    return render_template('404.html',
                            darkmode_status=darkmode_status,
                            ), 404


if __name__ == '__main__':
    app.run(debug=True)
