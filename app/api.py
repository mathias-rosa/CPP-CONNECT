

"""
    Module qui gère les différentes routes api
"""

from app import app, mongodb, mail
from flask import render_template, redirect, url_for, request
from werkzeug.security import generate_password_hash
from flask_login import login_required, logout_user, current_user

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
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


def rajouter_note(liste_matiere, colles, maths_ou_physique):
    """
        Cette fonction sert à rajouter les notes de colles de maths et de physique dans les
        moyennes de maths et de physique.
    """
    # On souhaite rajouter la moyenne des colles de maths dans la moyenne de maths
    moyenne_colles = None
    for matiere in liste_matiere:
        if matiere[0] == colles:
            moyenne_colles = matiere[1]
            break
    if moyenne_colles:
        # Si la moyenne de mat n'existe pas encore,
        # On crée une liste contenant le nom des matières
        liste_matiere_nom = [matiere[0] for matiere in liste_matiere]
        if not maths_ou_physique in liste_matiere_nom:
            liste_matiere.append([maths_ou_physique, moyenne_colles, {
                            "nom_note": colles,
                            "note": moyenne_colles,
                            "coef": 3.0,
                            "date": datetime.date.today().strftime("%d/%m/%Y"),
                        }])
        else:
            index_maths = liste_matiere_nom.index(maths_ou_physique)
            liste_matiere[index_maths].insert(2,{
                            "nom_note": colles,
                            "note": moyenne_colles,
                            "coef": 3.0,
                            "date": datetime.date.today().strftime("%d/%m/%Y")
                        })


@app.route('/notes/get_notes_gepi')
@login_required
def get_notes_gepi():

    """
        Api qui permet de recuperere les notes
    """

    try:
        USER = request.args['USER']
        GEPI_LOGIN = request.args['GEPI_LOGIN']
        GEPI_PASSWORD = request.args['GEPI_PASSWORD']

    except:
        return "login ou mot de passe gepi invalide ou non passé en argument"

    """
    # On crée une instance du web-driver Firefox (environement de production)

    options = Options()
    options.headless = False
    driver = webdriver.Firefox(options=options)

    """
    # On crée une instance du web-driver chrome (environement de déploiment)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

    # """

    # On va sur https://cppreunion.fr/gepi/login.php
    driver.get("https://cppreunion.fr/gepi/login.php")
    # En fonction de notre connection et des performance de notre machine il faudra attendre

    # login

    wait = WebDriverWait(driver, 20)

    # sert à attendre que la page charge
    login_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input#login")))

    login_box.send_keys(GEPI_LOGIN)

    password_box = driver.find_element_by_css_selector("input#no_anti_inject_password")
    password_box.send_keys(GEPI_PASSWORD)

    login_button = driver.find_element_by_css_selector("input#soumettre")
    login_button.send_keys(Keys.ENTER)

    # On va sur le détail des notes
    detail_des_notes = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#menu_barre > div.menu_barre_container > ul > li:nth-child(2) > a")))

    detail_des_notes.send_keys(Keys.ENTER)

    # on recupère tous les elements td.releve qui contiennent les notes et matieres
    selenium_lines = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "td.releve")))

    selenium_lines = driver.find_elements_by_css_selector("td.releve")

    liste_matiere = []

    while selenium_lines:
        # On récupère le nom de chaque matière
        matiere :str = selenium_lines.pop(0).text.split("\n")[0]
        # On récupère la liste de toutes les notes dans la matière
        liste_notes :list = selenium_lines.pop(0).text.split("\n")

        # On crée une liste qui contiendra toutes les notes de la matière
        liste_notes_matiere = [matiere]

        # On crée une variable qui servira à calculer le moyenne de la matière

        somme_notes = 0
        somme_coef = 0

        # On transforme chaque note de la liste des notes en dictionnaire
        for note in liste_notes:
            nom_note = re.search(r'.+?:', note)
            if nom_note:
                nom_note = nom_note.group(0)[:-1]
            else:
                nom_note = None

            note_obtenue = re.search(r': [0-9\.]+', note)
            if note_obtenue:
                note_obtenue = float(note_obtenue.group(0)[2:])
            else:
                note_obtenue = None

            coef = re.search(r'coef:[1-9]+', note)
            if coef:
                coef = float(coef.group(0)[5:])
            else:
                coef = 1.0

            date = re.search(r'[0-9]{2}\/[0-9]{2}/[0-9]{4}', note)
            if date:
                date = date.group(0)
            else:
                date = None

            dict_note = {
                            "nom_note": nom_note,
                            "note": note_obtenue,
                            "coef": coef,
                            "date": date,
                        }
            if dict_note["note"]:
                liste_notes_matiere.append(dict_note)
                somme_coef += dict_note["coef"]
                somme_notes += dict_note["note"] * dict_note["coef"]

        # On ajoute la liste des notes de la matière dans la liste de toutes les matières
        # s'il y a au moins une note dans la liste (donc pas seulement le titre)
        if len(liste_notes_matiere) > 1:
            liste_notes_matiere.insert(1, round(somme_notes/somme_coef, 2))
            liste_matiere.append(liste_notes_matiere)

    rajouter_note(liste_matiere, "Colles de mathématiques", "Mathématiques")
    rajouter_note(liste_matiere, "Colles de physique", "Physique Chimie")

    mongodb.db.Users.update_one(
            {"username": USER},
            {'$set': {'notes': liste_matiere}}, upsert=False
        )

    return {"notes": liste_matiere}


def calcul_moyenne(notes : list, type="generale"):

    moy_ou_note = "moyenne" if type == "generale" else "note"
    moyenne = 0
    coefs = 0
    for matiere_ou_note in notes:
        moyenne += matiere_ou_note[moy_ou_note] * matiere_ou_note['coef']
        coefs += matiere_ou_note['coef']
    
    if coefs == 0:
        return None
    return round(moyenne / coefs, 2)

@app.route('/notes/get_notes')
@login_required
def get_notes():
    notes_prepa = mongodb.db.Notes.find_one({"username" : str(current_user.username)})
    if notes_prepa:
        
        # Calcul des moyennes 

        for semestre in range(1, 5):

            for matiere in notes_prepa["semestres"]["semestre" + str(semestre)]["notes"]:
                matiere["moyenne"] = calcul_moyenne(matiere["notes"], type="note")
            
            notes_prepa["semestres"]["semestre" + str(semestre)]["moyenne"] = calcul_moyenne(notes_prepa["semestres"]["semestre" + str(semestre)]["notes"])

        mongodb.db.Notes.replace_one(({"username" : str(current_user.username)}), notes_prepa)


        return notes_prepa["semestres"]

    notes_prepa = {
        "username" : str(current_user.username),
        "semestres": {
            "semestre1" : {
                "moyenne" : 20,
                "notes" : []
            },
            "semestre2" : {
                "moyenne" : 20,
                "notes" : []
            },
            "semestre3" : {
                "moyenne" : 20,
                "notes" :  []
            },
            "semestre4" : {
                "moyenne" : 20,
                "notes" :  []
            },
            }
        }

    mongodb.db.Notes.insert_one(notes_prepa)
    

    return notes_prepa["semestres"]


@app.route('/notes/update_notes', methods=['GET', 'POST'])
@login_required
def update_notes():

    notes_prepa = mongodb.db.Notes.find_one({"username" : str(current_user.username)})

    notes_prepa["semestres"] = request.json

    for semestre in range(1, 5):

        for matiere in notes_prepa["semestres"]["semestre" + str(semestre)]["notes"]:
                matiere["moyenne"] = calcul_moyenne(matiere["notes"], type="note")
        
        notes_prepa["semestres"]["semestre" + str(semestre)]["moyenne"] = calcul_moyenne(notes_prepa["semestres"]["semestre" + str(semestre)]["notes"])

    mongodb.db.Notes.replace_one(({"username" : str(current_user.username)}), notes_prepa)

    return notes_prepa["semestres"]


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
                        "promo" : request.args['newPromo'],
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