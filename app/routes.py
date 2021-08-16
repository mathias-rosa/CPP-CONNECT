
"""
    Module qui gère les différentes routes de l'application
"""

import os
from app import app
from flask import Flask, render_template, send_from_directory, redirect, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import datetime
import requests
from bs4 import BeautifulSoup

from flask_mail import Message

from app import mongodb, mail
from app.models import User, Tool, Addresses
from app.forms import (LoginForm, RegisterForm, ChangeSelfInformationsForm, ResetPasswordForm, 
                        RequestResetPasswordForm)


@app.route('/favicon.ico')
def fav():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico')


@app.route('/')
def index():

    # On définit le thème de la page des utilisateurs connectés.
    # Pour les utilisateurs non connectés, le thème clair est utilisé par default.

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
    message = None
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data == form.password_confirm.data:
            user = mongodb.db.Users.find_one({"email": form.email.data})
            if user:
                error = "Cet utilisateur existe déjà"
                return render_template('signup.html', 
                                        form=form,
                                        error=error,
                                        message=message,
                                        theaming=theaming,
                                        )

            # Pour des raisons de sécurité, on hache le mot de passe de l'utilisateur avant de
            # l'enregistrer dans la base de donnée.
            hashed_password = generate_password_hash(form.password.data, method='sha256')
            # Création du nom d'utilisateur.
            # Note : On remplace les espaces par du vide afin de pouvoir les manipuler plus facilement
            username = form.name.data.lower() + "." + form.surname.data.lower()
            username = username.replace(" ", "")

            # Afin d'éviter des problèmes d'homonymes, on ajoute un caractère à la fin du nom d'utilisateur
            # si celui-ci est déjà pris
            c = 0
            while mongodb.db.Users.find_one({"username": username}):
                c += 1
                username = username + str(c)
            
            # Géneration d'un id unique
            id  = int(str(int(generate_password_hash(form.name.data.upper() + form.surname.data + username, method='MD5')[22:], base=16))[:18])
            # Création d'un nouvel utilisateur
            new_user = {"_id": id, 
                        "name": form.name.data,
                        "surname": form.surname.data.upper(),
                        "username": username,
                        "email": form.email.data.lower(),
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
                            message=message,
                            theaming=theaming,
                            )

    return render_template('signup.html', 
                            form=form,
                            error=error,
                            message=message,
                            theaming=theaming,
                            )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    error = None
    warning = None
    # On essaie de récuperer un éventuel message passé en argument dans l'url. Si il n'y en a pas,
    # on fixe message à None
    try:
        message = request.args["message"]
    except:
        message = None

    form = LoginForm()
    # Si l'utilisateur à clické sur le bouton submit du formulaire
    if form.validate_on_submit():
        # On peut identifier les utilisateurs par leur email ou leur nom d'utilisateur.
        # On le récupère ce que l'utilisateur a rentré puis on determine comment il a souhaité s'identifier.
        username = form.username.data
        try:
            if "@" in username:
                # par email
                user = User(mongodb.db.Users.find_one({"email": username.lower()}))
            else:
                # par nom d'utilisateur
                user = User(mongodb.db.Users.find_one({"username": username}))
        except:
            # L'utilisateur n'est pas dans la base de donnée ou il s'est trompé sur son identifiant.
            error = "Nom d'utilisateur incorrect"        
            return render_template('login.html', 
                                    form=form,
                                    error=error,
                                    message=message,
                                    warning=warning,
                                    theaming=theaming,
                                    )

        if check_password_hash(user.password, form.password.data):
            # si le hash du mot de passe entré correspond à celui de la base de donnée,
            # on identifie l'utilisateur.
            login_user(user, remember=form.remember.data)
            return redirect(url_for('dashboard'))
        error = "Mot de passe incorrect"

    return render_template('login.html', 
                            form=form,
                            error=error,
                            message=message,
                            warning=warning,
                            theaming=theaming,
                            )


def send_reset_email(user):
    """
        Permet d'envoyer un mail à un utilisateur comprenant un lien pour rénitialiser leur mot de passe.
        Prend en argument user : Instance de la classe User.

        Note : Il semble que, dans la configuration actuelle,
        les utilisateurs outlook notamment ne reçoivent pas les mails
        
    """
    # On crée un token unique valable une demi-heure.
    token = user.get_reset_token()
    msg = Message('Rénitialisation du mot de passe',
                  sender=("Equipe des comptes CPP-CONNECT", 'cpp.reunion.promo11@gmail.com'),
                  recipients=[user.email])
    msg.body = f'''Bonjour,\n\nVous recevez ce mail car vous avez effectué une demande de modification de votre mot de passe.
Afin de modifier votre mot de passe, cliquez sur le lien ci-dessous :
{url_for('reset_token', token=token, _external=True)}

Bonne journée,
L'équipe des comptes cpp-connect.

Si vous n'êtes pas à l'origine de cette demande, ignorez simplement ce mail.

    '''
    mail.send(msg)
    


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
    """
        Permet à un utilisateur de rénitialiser son mot de passe.
    """
    if not current_user.is_anonymous:
        return redirect(url_for("dashboard"))

    form = RequestResetPasswordForm()
    error = None
    message = None

    # On essaie de récuperer un éventuel message passé en argument dans l'url. Si il n'y en a pas,
    # on fixe warning à None.

    try:
        warning = request.args["warning"]
    except:
        warning = None

    if form.validate_on_submit():
        email = form.email.data.lower()
        user = mongodb.db.Users.find_one({"email": email})
        if user:
            user = User(user)
            message = "Lien de réinitialisation envoyé à : " + email
            send_reset_email(user) # Envoi du mail
            return render_template('reset_request.html',
                            theaming="light-theme",
                            error=error,
                            message=message,
                            warning=warning,
                            form=form)

        error = "Email incorrect"

    return render_template('reset_request.html',
                            theaming="light-theme",
                            error=error,
                            message=message,
                            warning=warning,
                            form=form)


@app.route("/reset-password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    """
        Les utilisateurs souhaitant modifier leur mot de passe sont renvoyés sur cette page après 
        avoir cliqué sur le lien présent dans le mail qui leur a été envoyé.
    """
    if not current_user.is_anonymous:
        return redirect(url_for("dashboard"))

    error = None
    message = None
    warning = None
    
    form = ResetPasswordForm()
    user = User.verify_reset_token(token)

    if not user:
        warning = 'Jeton invalide ou expiré, Merci de recommencer.'
        return redirect(url_for("reset_request", warning=warning))
    
    if form.validate_on_submit():
        if form.new_password.data == form.new_password_confirm.data:
            hashed_password = generate_password_hash(form.new_password.data, method='sha256')
            mongodb.db.Users.update_one(
                    {"email": user.email},
                    {'$set': 
                        {
                            "password": hashed_password,
                        }
                    }
                )
            message = "Votre mot de passe a bien été modifié."
            return redirect(url_for('login', message=message))

        error = "Les mots de passes ne correspondent pas"

    return render_template('reset_token.html', 
                            theaming="light-theme",
                            error=error,
                            message=message,
                            warning=warning,
                            user=user,
                            form=form)


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
    
    # On récupère la liste des outils dans la base de donnée.
    tools_list = [Tool(tool) for tool in mongodb.db.Tools.find({})]

    return render_template('tools.html', 
                            current_user=current_user,
                            theaming=theaming,
                            tools_list=tools_list,
                            baseURL=request.base_url,
                            )

@app.route('/tools/get_image')
@login_required
def get_image():
    """
        Api qui permet de récuperer l'url du logo d'un site si celui-ci l'a enregistré dans une balise meta.
    """
    # On récupère l'url du site passé en argument dans l'url.
    url = request.args['url']

    # On parse le html avec le module BeautifulSoup pour récuperer le contenu dd'une balise meta : og:image (une url vers l'image)

    response = requests.get(url)
    soup = BeautifulSoup(response.text, features="html.parser")
    metas = soup.find_all('meta')
    try:
        image = [ meta.attrs['content'] for meta in metas if 'content' in meta.attrs and 'property' in meta.attrs and meta.attrs['property'] == 'og:image' ][0]
        if "https" in image:
            # L'url de l'image est absolue.
            return {"imageURL" : image}
        else:
            # L'url de l'image est relative, on rajoute l'url du site pour en faire une url absolue
            return {"imageURL" : url + image}
    except:
        # On a pas trouvé de balise meta avec l'attribut og-image donc on retourne l'url d'une image générique.
        return {"imageURL" : url_for('static', filename='img/Avatar/profile_pict_1.svg')}

@app.route('/addresses')
@login_required
def addresses():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    
    # On récupère la liste des bonnes adresses depuis la base de donnée
    addresses_list = [Addresses(address) for address in mongodb.db.Addresses.find({})]

    return render_template('addresses.html', 
                            current_user=current_user,
                            theaming=theaming,
                            addresses_list=addresses_list,
                            )

@app.route('/guiness')
@login_required
def guiness():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"

    # On initie une liste vide qui contiendra tous les reccords présents dans la base de donnée.
    record_list = []

    # On récupère les records dans la base de donnée.
    for record in mongodb.db.Guiness.find({}):
        # On classe les utilisateurs avec la clé rank. (Les utilisateurs ont un format d'objet)
        # Voir la structure de la base de donnée.
        record["content"].sort(key=lambda k: k['rank'])
        record_list.append(record)

    return render_template('guiness.html', 
                        current_user=current_user,
                        theaming=theaming,
                        record_list=record_list
                        )

@app.route('/add-record')
@login_required
def add_record():
    
    """
        Api qui sert à rajouter un nouveau record.
    """

    # On récupère les arguments : title, rank, name, promo et score depuis l'url.
    if request.args['title'] and request.args['rank'] and request.args['name'] and request.args['promo'] and request.args['score']:
        
        # On récupère le record en comparant son titre par rapport à ceux de la base de donnée.
        record = mongodb.db.Guiness.find_one({"title": request.args['title']})


        mongodb.db.Guiness.update_one(
                {"title": request.args['title']},
                {'$set': 
                    {
                        "content": record["content"] + [{
                            "name": request.args['name'],
                            "promo": request.args['promo'],
                            "score": request.args['score'],
                            "rank": request.args['rank']
                        }]
                    }
                }
            )

        return "Done"
    return "Invalid args"
        

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
                            baseURL=request.base_url
                            )


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():

    """
        Permet à l'utilisateur de changer certains paramètres.
    """

    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"

    # Modification des informations personnelles
    profileForm = ChangeSelfInformationsForm()
    if profileForm.validate_on_submit():
        # L'utilisateur doit rentrer son mot de passe afin effectuer toute modification.
        # Si le mot de passe est incorect, on retourne "mot de passe incorect" (il faudra créer une belle page)
        if check_password_hash(current_user.password, profileForm.current_password.data):
            # Si un form n'est pas vide (à été rempli), on met à jour l'information correspondante.
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

    # Mise à jour du thème de l'utilisateur.
    try:
        # On récupère le thème choisi par l'utilisateur.
        theme = request.form['theme']

        # if thème != theaming => Si le thème choisi est différent que celui que l'utilisateur a déjà.

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

    """
        Api destinée aux admins qui permet de modifier les informations d'un utilisateur.
    """

    if current_user.admin == False:
        return "Forbidden"

    # Si l'utilisateur souhaite modofier son mot de passe, On le hache. Sinon, on defini newPassword comme
    # le hash de l'ancien mot de passe de l'utilisateur.
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
                        "username": request.args['newUsername'].replace(" ", ""),
                        "email": request.args['newEmail'],
                        "password": newPassword,
                        "admin": request.args['admin'] in ("True")
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
