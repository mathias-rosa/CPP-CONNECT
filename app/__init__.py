import os
from flask import Flask, render_template, redirect, url_for, send_from_directory, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField, RadioField
from wtforms.validators import InputRequired, Email, Length, Optional
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

class TheamingForm(FlaskForm):
    theme = RadioField('Thème', choices=[('lightmode','Thème Clair'), ('darkmode','Thème Sombre')], default='lightmode')


@app.route('/favicon.ico')
def fav():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico')

@app.route('/')
def index():
    theaming = "lightmode"
    try:
        if current_user.darkmode == True:
            theaming = 'darkmode'
    except:
        print("current_user n'existe pas")
    return render_template('index.html', 
                            year=datetime.date.today().year,
                            theaming=theaming,
                            )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    theaming = "lightmode"
    error = None
    try:
        if current_user.darkmode == True:
            theaming = 'darkmode'
    except:
        print("current_user n'existe pas")
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data == form.password_confirm.data:
            user = User.query.filter_by(email=form.email.data).first()
            if user:
                error = "Cet utilisateur existe déjà"
                return render_template('signup.html', 
                                        form=form,
                                        error=error,
                                        theaming=theaming,
                                        )
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
    theaming = "lightmode"
    error = None
    try:
        if current_user.darkmode == True:
            theaming = 'darkmode'
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
    theaming = "lightmode"
    if current_user.admin == 1:
        return redirect(url_for("admin"))
    else:
        if current_user.darkmode == True:
            theaming = 'darkmode'
        return render_template('dashboard.html', 
                                current_user=current_user,
                                theaming=theaming,
                                )


@app.route('/admin-dashboard')
@login_required
def admin():
    theaming = "lightmode"
    if current_user.admin == 0:
        return redirect(url_for("dashboard"))
    else:
        if current_user.darkmode == True:
            theaming = 'darkmode'
        userlist = [user for user in db.session.query(User)]
        return render_template('admin.html', 
                                current_user=current_user,
                                userlist=userlist,
                                theaming=theaming,
                                )

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    theaming = "lightmode"
    if current_user.darkmode == True:
        theaming = 'darkmode'
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
        
            db.session.commit()
            print(profileForm.name.data, profileForm.surname.data, profileForm.username.data, profileForm.email.data)
            return render_template('settings.html', 
                            profileForm=profileForm,
                            TheamingForm=theamingForm,
                            theaming=theaming,
                            )
        print(current_user.password, generate_password_hash(profileForm.current_password.data, method='sha256'))
        return "Mot de passe incorect"

    theamingForm = TheamingForm()
    if theamingForm.validate_on_submit():
        theaming = theamingForm.theme.data
        if theaming == "darkmode":
            current_user.darkmode = True
        else:
            current_user.darkmode = False
        db.session.commit()
        return render_template('settings.html', 
                            profileForm=profileForm,
                            TheamingForm=theamingForm,
                            theaming=theaming,
                            )

    return render_template('settings.html', 
                            profileForm=profileForm,
                            TheamingForm=theamingForm,
                            theaming=theaming,
                            )

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    theaming = "lightmode"
    try:
        if current_user.darkmode == True:
            theaming = 'darkmode'
    except:
        print("current_user n'existe pas")

    return render_template('404.html',
                            theaming=theaming,
                            ), 404

def chatapp():
    theaming = "lightmode"
    try:
        if current_user.darkmode == True:
            theaming = 'darkmode'
    except:
        print("current_user n'existe pas")
    return render_template('chatapp.html', 
                            year=datetime.date.today().year,
                            theaming=theaming,
                            )


if __name__ == '__main__':
    app.run(debug=True)
