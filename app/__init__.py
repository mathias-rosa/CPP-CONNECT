import os
from flask import Flask, render_template, redirect, url_for, send_from_directory, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField, RadioField
from wtforms.validators import InputRequired, Email, Length, Optional

import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import datetime

app = Flask(__name__)
bootstrap = Bootstrap(app)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
host = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/cpp_connect')
client = pymongo.MongoClient(host=host)
mongodb = client.cpp_connect
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_dict):
        self.id = user_dict.get('_id')
        self.name = user_dict.get('name')
        self.surname = user_dict.get('surname')
        self.username = user_dict.get('username')
        self.email = user_dict.get('email')
        self.password = user_dict.get('password')
        self.theaming = user_dict.get('theaming')
    
    def get_id(self):
        return str(self.id)

class LoginForm(FlaskForm):
    username = StringField("Nom d'utilisateur ou Email", validators=[InputRequired()])
    password = PasswordField('Mot de passe', validators=[InputRequired(), Length(min=6, max=80)])
    remember = BooleanField('Se rappeller de moi')

class RegisterForm(FlaskForm):
    name = StringField('Nom', validators=[InputRequired()])
    surname = StringField('Prénom', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('Mot de passe', validators=[InputRequired(), Length(min=6, max=80)])
    password_confirm = PasswordField('', validators=[InputRequired(), Length(min=6, max=80)])


class ChangeSelfInformationsForm(FlaskForm):
    name = StringField('Nom')
    surname = StringField('Prénom')
    username = StringField("Nom d'utilisateur")
    email = StringField('Email', validators=[Optional(), Email(message='Invalid email'), Length(max=50)])
    current_password = PasswordField('Mot de passe actuel', validators=[InputRequired(), Length(min=6, max=80)])
    new_password = PasswordField('Nouveau mot de passe', validators=[Optional(), Length(min=6, max=80)])
    new_password_confirm = PasswordField('Confirmer votre nouveau mot de passe', validators=[Optional(), Length(min=6, max=80)])


@login_manager.user_loader
def load_user(user_id):
    user = User(mongodb.db.Users.find_one({"_id": int(user_id)}))
    if user:
        return user

@app.route('/favicon.ico')
def fav():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico')

@app.route('/')
def index():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    return render_template('index.html', 
                            year=datetime.date.today().year,
                            theaming=theaming,
                            )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    error = None
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data == form.password_confirm.data:
            user = mongodb.db.Users.find_one({"email": form.email.data})
            if user:
                error = "Cet utilisateur existe déjà"
                return render_template('signup.html', 
                                        form=form,
                                        error=error,
                                        theaming=theaming,
                                        )
            hashed_password = generate_password_hash(form.password.data, method='sha256')
            username = form.surname.data.lower() + "." + form.name.data.lower()
            id  = int(str(int(generate_password_hash(form.name.data.upper() + form.surname.data, method='MD5')[22:], base=16))[:18])
            new_user = {"_id": id, 
                        "name": form.name.data.upper(),
                        "surname": form.surname.data,
                        "username": username,
                        "email": form.email.data,
                        "password": hashed_password,
                        "theaming": False,
                        "admin": False}
            mongodb.db.Users.insert_one(new_user)
            user = mongodb.db.Users.find_one({"email": form.email.data})
            login_user(User(user))
            return redirect(url_for('dashboard'))

        error = "Les mots de passe ne correspondent pas"
        return render_template('signup.html', 
                            form=form,
                            error=error,
                            theaming=theaming,
                            )

    return render_template('signup.html', 
                            form=form,
                            error=error,
                            theaming=theaming,
                            )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    error = None
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        if "@" in username:
            user = User(mongodb.db.Users.find_one({"email": username}))
        else:
            user = User(mongodb.db.Users.find_one({"username": username}))
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))

        error = "Mot de passe ou nom d'utilisateur incorrect"        
        return render_template('login.html', 
                                form=form,
                                error=error,
                                theaming=theaming,
                                )

    return render_template('login.html', 
                            form=form,
                            error=error,
                            theaming=theaming,
                            )


@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    #userlist = [user for user in db.session.query(User)]
    userlist = []
    return render_template('dashboard.html', 
                            current_user=current_user,
                            userlist=userlist,
                            theaming=theaming,
                            )



@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    profileForm = ChangeSelfInformationsForm()
    if profileForm.validate_on_submit():
        if check_password_hash(current_user.password, profileForm.current_password.data):
            if profileForm.name.data != "":
                current_user.name = profileForm.name.data
            if profileForm.surname.data != "":
                current_user.surname = profileForm.surname.data
            if profileForm.username.data != "":
                current_user.username = profileForm.username.data
            if profileForm.email.data != "":
                current_user.email = profileForm.email.data
            if profileForm.new_password.data != "" and profileForm.new_password.data == profileForm.new_password_confirm.data:
                current_user.password = generate_password_hash(profileForm.new_password.data, method='sha256')
        
            mongodb.db.Users.update_one(
                {"_id": current_user.id},
                {'$set': 
                    {
                        "name": current_user.name,
                        "surname": current_user.surname,
                        "username": current_user.username,
                        "email": current_user.email,
                        "password": current_user.password
                    }
                }
            )
            return render_template('settings.html', 
                            profileForm=profileForm,
                            theaming=theaming,
                            )
        return "Mot de passe incorect"

    try:
        theme = request.form['theme']
        if theme == "dark-theme" and theme != theaming:
            theaming = "dark-theme"
            mongodb.db.Users.update_one(
                {"username": current_user.username},
                {'$set': {'theaming': "dark-theme"}}, upsert=False
            )
        elif theme == "light-theme" and theme != theaming:
            theaming = "light-theme"
            mongodb.db.Users.update_one(
                {"username": current_user.username},
                {'$set': {'theaming': "light-theme"}}, upsert=False
            )
        elif theme == "pink-pastel" and theme != theaming:
            theaming = "pink-pastel"
            mongodb.db.Users.update_one(
                {"username": current_user.username},
                {'$set': {'theaming': "pink-pastel"}}, upsert=False
            )

    except:
        pass
    return render_template('settings.html', 
                            profileForm=profileForm,
                            theaming=theaming,
                            )
                            

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    return render_template('404.html',
                            theaming=theaming,
                            ), 404


if __name__ == '__main__':
    app.run(debug=True)
