
"""
    Module qui gère les différentes routes de l'application
"""

import os
import datetime

from app import app, mongodb
from flask import render_template, send_from_directory, redirect, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import datetime

from app.models import User, Tool, Addresses
from app.forms import LoginForm, RegisterForm, ChangeSelfInformationsForm, ProfilePicForm


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
                            baseURL=request.base_url
                            )

@app.route('/presentation')
def presentation():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"

    return render_template('presentation.html',
                            theaming=theaming,
                            baseURL=request.base_url
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
    date = datetime.datetime.now()
    proposition_promo = date.year - 2009 if date.month > 7 else date.year - 2010
    if form.validate_on_submit():
        if form.password.data == form.password_confirm.data:
            email = form.email.data.replace(" ", "").lower()
            user = mongodb.db.Users.find_one({"email": email})
            if user:
                error = "Cet utilisateur existe déjà"
                return render_template('signup.html',
                                        form=form,
                                        proposition_promo=proposition_promo,
                                        error=error,
                                        message=message,
                                        theaming=theaming,
                                        baseURL=request.base_url
                                        )

            accountType = ""

            # Afin d'éviter que n'importe qui puisse se créer un compte, on demande à l'utilisateur
            # de rentrer un "sésame" qu'on lui aura donné au préalable. Si ce sésame est correct, il peut
            # se créer un compte.
            if form.sesame.data == "f(pâté)=samoussa":
                accountType = "élève"
            else:
                error = "Sésame invalide."
                return render_template('signup.html',
                        form=form,
                        proposition_promo=proposition_promo,
                        error=error,
                        message=message,
                        theaming=theaming,
                        baseURL=request.base_url
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
                        "email": email,
                        "password": hashed_password,
                        "theaming": "light-theme",
                        "accountType": accountType,
                        "profil_pic_url": "Benjamin La cucarracha",
                        "promo": form.promo.data}
            mongodb.db.Users.insert_one(new_user)
            user = mongodb.db.Users.find_one({"email": email})
            login_user(User(user), remember=form.remember.data)
            return redirect(url_for('dashboard'))

        error = "Les mots de passe ne correspondent pas"
        return render_template('signup.html',
                            form=form,
                            proposition_promo=proposition_promo,
                            error=error,
                            message=message,
                            theaming=theaming,
                            baseURL=request.base_url
                            )

    return render_template('signup.html',
                            form=form,
                            proposition_promo=proposition_promo,
                            error=error,
                            message=message,
                            theaming=theaming,
                            baseURL=request.base_url
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
        username = form.username.data.replace(" ", "").lower()
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
                                    baseURL=request.base_url
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
                            baseURL=request.base_url
                            )


@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"
    userlist = [User(user) for user in mongodb.db.Users.find({})]

    #edt = mongodb.db.edt.find_one({"semaine": datetime.datetime.utcnow().isocalendar()[1]})
    edt = mongodb.db.edt.find_one({"promo": current_user.promo})

    if edt:
        edt = edt['semaines'][str(datetime.datetime.utcnow().isocalendar()[1])]

    return render_template('dashboard.html',
                            current_user=current_user,
                            userlist=userlist,
                            theaming=theaming,
                            baseURL=request.base_url,
                            edt=edt
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


@app.route('/addresses')
@login_required
def addresses():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"

    # On récupère la liste des bonnes adresses depuis la base de donnée
    addresses_list = [Addresses(address) for address in mongodb.db.Addresses.find({})]

    # nord = [adresse for adresse in addresses_list if adresse.localisation == "nord"]

    Nord, Ouest, Sud, Est = [], [], [], []
    for addresse in addresses_list:
        if addresse.localisation == "nord":
            Nord.append(addresse)
        elif addresse.localisation == "ouest":
            Ouest.append(addresse)
        elif addresse.localisation == "sud":
            Sud.append(addresse)
        elif addresse.localisation == "est":
            Est.append(addresse)

    return render_template('addresses.html',
                            current_user=current_user,
                            theaming=theaming,
                            baseURL=request.base_url,
                            Nord=Nord,
                            Ouest=Ouest,
                            Sud=Sud,
                            Est=Est,
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
                        baseURL=request.base_url,
                        record_list=record_list
                        )


@app.route('/anciens')
@login_required
def anciens():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"

    # On récupère la liste des anciens étudiants et les écoles qu'ils ont eu dans la base de donnée.
    anciens_list = [ancien for ancien in mongodb.db.Anciens.find({})]

    anciens_list.sort(key=lambda k: k['promo'], reverse=True)

    return render_template('anciens.html',
                            current_user=current_user,
                            theaming=theaming,
                            anciens_list=anciens_list,
                            baseURL=request.base_url
                            )


@app.route('/anciens/<userid>')
def social(userid):
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"

    error = ""
    user = {}

    try:
        userid = userid.replace("&s", " ").replace("&r", " ").split(".", 1)
        user_promo = int(userid[0][1:])
        username = userid[1]
        name, surname = [e.capitalize() for e in username.split(".", 1)]
    except Exception as e:
        error = "Impossible d'identifier cette personne"
        return render_template('social.html',
            current_user=current_user,
            theaming=theaming,
            error=error,
            user=user,
            baseURL=request.base_url
            )
    try:
        liste_promo = mongodb.db.Anciens.find_one({"promo" : user_promo})["eleves"]
        print([eleve["name"] for eleve in liste_promo])
        for eleve in liste_promo:
            if eleve["name"].capitalize() == name and eleve["surname"].capitalize() == surname:
                user = eleve
                user["promo"] = user_promo
                error = ""
                break
            error = f"Auccun {name} {surname}, Promo {user_promo} dans la base de donnée"
        if error:
            return render_template('social.html',
                    current_user=current_user,
                    theaming=theaming,
                    error=error,
                    user=user,
                    baseURL=request.base_url
                    )
    except:
        error = f"Auccun {name} {surname}, Promo {user_promo} dans la base de donnée"
        return render_template('social.html',
            current_user=current_user,
            theaming=theaming,
            error=error,
            user=user,
            baseURL=request.base_url
            )
    
    try:
        cpp_connect_user = User(mongodb.db.Users.find_one({"username": f"{name.lower()}.{surname.lower()}"}))
        profile_pic_url = cpp_connect_user.profil_pic_url
    except:
        cpp_connect_user = None

    
    return render_template('social.html',
                            current_user=current_user,
                            theaming=theaming,
                            error=error,
                            user=user,
                            cpp_connect_user=cpp_connect_user,
                            baseURL=request.base_url
                            )


@app.route('/edt')
@login_required
def edt():
    if not current_user.is_anonymous:
        theaming = current_user.theaming
    else:
        theaming = "light-theme"

    return render_template('edt.html',
                            current_user=current_user,
                            theaming=theaming,
                            baseURL=request.base_url
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
                            baseURL=request.base_url,
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

    profileForm = ChangeSelfInformationsForm()
    profilePicForm = ProfilePicForm()
    # Modification des informations personnelles
    if profileForm.validate_on_submit():
        # L'utilisateur doit rentrer son mot de passe afin effectuer toute modification.
        # Si le mot de passe est incorect, on retourne "mot de passe incorect" (il faudra créer une belle page)
        if check_password_hash(current_user.password, profileForm.current_password.data):
            # Si un form n'est pas vide (à été rempli), on met à jour l'information correspondante.
            if profileForm.name.data != "":
                current_user.name = profileForm.name.data
            if profileForm.surname.data != "":
                current_user.surname = profileForm.surname.data
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
                        "email": current_user.email,
                        "password": current_user.password,
                    }
                }
            )
            return render_template('settings.html',
                            profilePicForm=profilePicForm,
                            profileForm=profileForm,
                            theaming=theaming,
                            baseURL=request.base_url
                            )
        return "Mot de passe incorect"

    # Modification de ma photo de profile

    if profilePicForm.validate_on_submit():


        if profilePicForm.profile_pic.data != "":

            if "Benjamin La cucarracha" in profilePicForm.profile_pic.data:
                    
                mongodb.db.Users.update_one(
                    {"_id": current_user.id},
                    {'$set':
                        {
                            "profil_pic_url" : "Benjamin La cucarracha"
                        }
                    }
                )

            elif ".svg" in profilePicForm.profile_pic.data or \
                ".png" in profilePicForm.profile_pic.data or \
                ".jpg" in profilePicForm.profile_pic.data or \
                ".jpeg" in profilePicForm.profile_pic.data or \
                ".gif" in profilePicForm.profile_pic.data :
                    
                current_user.profil_pic_url = profilePicForm.profile_pic.data

                mongodb.db.Users.update_one(
                    {"_id": current_user.id},
                    {'$set':
                        {
                            "profil_pic_url" : profilePicForm.profile_pic.data
                        }
                    }
                )
            

        return render_template('settings.html',
                        profilePicForm=profilePicForm,
                        profileForm=profileForm,
                        theaming=theaming,
                        baseURL=request.base_url
                        )

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
        elif theme == "prepa-theme" and theme != theaming:
            theaming = "prepa-theme"
            mongodb.db.Users.update_one(
                {"username": current_user.username},
                {'$set': {'theaming': "prepa-theme"}}, upsert=False
            )


    except:
        pass
    return render_template('settings.html',
                            profilePicForm=profilePicForm,
                            profileForm=profileForm,
                            theaming=theaming,
                            baseURL=request.base_url
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
                            baseURL=request.base_url
                            ), 404
