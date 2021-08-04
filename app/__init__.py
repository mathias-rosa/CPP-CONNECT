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
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'VERY_SECRET_KEY'
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
        self.admin = user_dict.get('admin')
        self.theaming = user_dict.get('theaming')
    
    def get_id(self):
        return str(self.id)

class Tool():
    def __init__(self, tool_dict):
        self.id = tool_dict.get('_id')
        self.name = tool_dict.get('name')
        self.description = tool_dict.get('description')
        self.url = tool_dict.get('url')
        self.image = self.get_image()
    
    def get_id(self):
        return str(self.id)
    
    def get_image(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, features="html.parser")
        metas = soup.find_all('meta')
        try:
            image = [ meta.attrs['content'] for meta in metas if 'content' in meta.attrs and 'property' in meta.attrs and meta.attrs['property'] == 'og:image' ][0]
            if "https" in image:
                return image
            else:
                return self.url + image
        except:
            return url_for('static', filename='img/Avatar/profile_pict_1.svg')

class LoginForm(FlaskForm):
    username = StringField("Nom d'utilisateur ou Email", validators=[InputRequired()])
    password = PasswordField('Mot de passe', validators=[InputRequired(), Length(min=6, max=80)])
    remember = BooleanField('Se rappeller de moi')

class RegisterForm(FlaskForm):
    name = StringField('Prénom', validators=[InputRequired()])
    surname = StringField('Nom', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('Mot de passe', validators=[InputRequired(), Length(min=6, max=80)])
    password_confirm = PasswordField('', validators=[InputRequired(), Length(min=6, max=80)])


class ChangeSelfInformationsForm(FlaskForm):
    name = StringField('Prénom')
    surname = StringField('Nom')
    username = StringField("Nom d'utilisateur")
    email = StringField('Email', validators=[Optional(), Email(message='Invalid email'), Length(max=50)])
    current_password = PasswordField('Mot de passe actuel *', validators=[InputRequired(), Length(min=6, max=80)])
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
            username = form.name.data.lower() + "." + form.surname.data.lower()
            id  = int(str(int(generate_password_hash(form.name.data.upper() + form.surname.data, method='MD5')[22:], base=16))[:18])
            new_user = {"_id": id, 
                        "name": form.name.data,
                        "surname": form.surname.data.upper(),
                        "username": username,
                        "email": form.email.data,
                        "password": hashed_password,
                        "theaming": "light-theme",
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
    userlist = [User(user) for user in mongodb.db.Users.find({})]
    return render_template('dashboard.html', 
                            current_user=current_user,
                            userlist=userlist,
                            theaming=theaming,
                            baseURL=request.base_url
                            )


@app.route('/tools')
@login_required
def tools():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    
    tools_list = [Tool(tool) for tool in mongodb.db.Tools.find({})]

    return render_template('tools.html', 
                            current_user=current_user,
                            theaming=theaming,
                            tools_list=tools_list,
                            )

@app.route('/addresses')
@login_required
def addresses():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    return render_template('addresses.html', 
                            current_user=current_user,
                            theaming=theaming,
                            )

@app.route('/guiness')
@login_required
def guiness():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    return render_template('guiness.html', 
                            current_user=current_user,
                            theaming=theaming,
                            )

@app.route('/notes')
@login_required
def notes():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    return render_template('notes.html', 
                            current_user=current_user,
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


@app.route('/update_user')
@login_required
def update_user():

    if request.args['newPassword']:
        newPassword = generate_password_hash(request.args['newPassword'], method='sha256')
    else:
        newPassword = User(mongodb.db.Users.find_one({"username": request.args['username']})).password

    mongodb.db.Users.update_one(
                {"username": request.args['username']},
                {'$set': 
                    {
                        "name": request.args['newName'],
                        "surname": request.args['newSurname'],
                        "username": request.args['newUsername'],
                        "email": request.args['newEmail'],
                        "password": newPassword,
                        "admin": bool(request.args['admin'])
                    }
                }
            )

    return "fait"

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
