

"""
    Module qui gère les différentes routes api
"""

from app import app, mongodb, mail
from flask import render_template, redirect, url_for, request
from werkzeug.security import generate_password_hash
from flask_login import login_required, logout_user, current_user

import requests
from bs4 import BeautifulSoup

import os
import datetime
import json

from flask_mail import Message

from app.models import User
from app.forms import ResetPasswordForm, RequestResetPasswordForm

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

    msg.html = f'''

    <h1 style="font-family : Poppins, Arial">
        Bonjour,
    </h1>
    <p>
        Vous recevez ce mail car vous avez effectué une demande de modification de votre mot de passe. <br>
        Afin de modifier votre mot de passe, cliquez sur le lien ci-dessous :
    </p>

    <a href="{url_for('reset_token', token=token, _external=True)}" 
        style="
            margin-right: 5%; width: 10em; cursor: pointer;
            transition: 100ms ease; border: none; color: white;
            background-color: #1d3658;
        "
    >
        Rénitialiser mon mot de passe
    </a>

    <p>
        Bonne journée, <br>
        L'équipe des comptes cpp-connect. <br>
        <br>
        Si vous n'êtes pas à l'origine de cette demande, ignorez simplement ce mail.
    </p>
    
    
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
            message = "Lien de réinitialisation envoyé à : " + email + ". <br>Pensez à verifier dans le dossier spam..."
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


@app.route('/update_user')
@login_required
def update_user():

    """
        Api destinée aux admins qui permet de modifier les informations d'un utilisateur.
    """

    if current_user.accountType != "admin":
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
                        "accountType": request.args['accountType'],
                        "promo" : int(request.args['newPromo']),
                    }
                }
            )

    return "fait"


@app.route('/delete_user')
@login_required
def delete_user():

    """
        Api destinée aux admins qui permet de supprimer un utilisateur
    """

    if current_user.accountType != "admin":
        return "Forbidden"


    mongodb.db.Users.delete_one({"username": request.args['username']})

    return "fait"

# SSL

@app.route('/.well-known/acme-challenge/FNVVMzI1B9O9hdJyJPburQd3Q7AIj1DmDKExpbpcwiM')
def ssl():
    return 'FNVVMzI1B9O9hdJyJPburQd3Q7AIj1DmDKExpbpcwiM.bnhQavHXSDbRj6Jvs6xUE_o00M2DDvLxpqzbdsNXVR8'