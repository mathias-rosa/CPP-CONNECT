"""
    Module qui gère les api de la page notes
"""

from app import app, mongodb, mail
from flask import render_template, redirect, url_for, request
from werkzeug.security import generate_password_hash
from flask_login import login_required, logout_user, current_user

import requests
import os

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

import re


def calcul_moyenne(notes: list, type="generale"):

    moy_ou_note = "moyenne" if type == "generale" else "note"
    moyenne = 0
    coefs = 0
    for matiere_ou_note in notes:
        moyenne += matiere_ou_note[moy_ou_note] * matiere_ou_note['coef']
        coefs += matiere_ou_note['coef']

    if coefs == 0:
        return None
    return round(moyenne / coefs, 2)


def add_notes(liste_notes, matiere):

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
            "coef": coef,
            "name": nom_note,
            "note": note_obtenue,
            "date": date,
            "gepi": True
        }

        if not dict_note in matiere["notes"]:
            matiere["notes"].append(dict_note)

    return matiere


@app.route('/notes/get_notes_gepi', methods=['GET', 'POST'])
@login_required
def get_notes_gepi():
    """
        Api qui permet de recuperere les notes
    """

    credentials = request.json

    gepi_username = credentials["gepi_username"]
    gepi_password = credentials["gepi_password"]
    semestre = credentials["semestre"]
    
    gepi_semestre = int(semestre)

    if gepi_semestre > 2:
        gepi_semestre -= 2

    notes_prepa = mongodb.db.Notes.find_one(
        {"username": str(current_user.username)})
    liste_matieres = [
        matiere["name"] for matiere in notes_prepa["semestres"][f"semestre{semestre}"]["notes"]] 

    if "Physique" in liste_matieres:
        liste_matieres.append("Physique Chimie")


    # ===========================================================================
    # On crée une instance du web-driver Firefox (environement de production)
    # ===========================================================================

    # options = Options()
    # options.headless = False
    # driver = webdriver.Firefox(options=options)

    # ===========================================================================
    #  On crée une instance du web-driver chrome (environement de déploiment)
    # ===========================================================================

    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

    # On va sur https://cppreunion.fr/gepi/login.php
    driver.get("https://cppreunion.fr/gepi/login.php")
    # En fonction de notre connection et des performance de notre machine il faudra attendre

    # login

    wait = WebDriverWait(driver, 20)

    # sert à attendre que la page charge
    login_box = wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, "input#login")))

    login_box.send_keys(gepi_username)

    password_box = driver.find_element_by_css_selector(
        "input#no_anti_inject_password")
    password_box.send_keys(gepi_password)

    login_button = driver.find_element_by_css_selector("input#soumettre")
    login_button.send_keys(Keys.ENTER)

    # On va sur le détail des notes
    detail_des_notes = wait.until(EC.visibility_of_element_located(
        (By.CSS_SELECTOR, "#menu_barre > div.menu_barre_container > ul > li:nth-child(2) > a")))

    detail_des_notes.send_keys(Keys.ENTER)

    if gepi_semestre == 2:
        semestre2 = wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "#container > div:nth-child(13) > p:nth-child(3) > a:nth-child(3)")))

        semestre2.send_keys(Keys.ENTER)
        time.sleep(3)

    # on recupère tous les elements td.releve qui contiennent les notes et matieres
    selenium_lines = wait.until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "td.releve")))

    selenium_lines = driver.find_elements_by_css_selector("td.releve")

    colles_de_maths = {}
    colles_de_physique = {}

    while selenium_lines:

        try:
            nom_matiere = selenium_lines.pop(0).text.split("\n")[0]
        except:
            return notes_prepa
        # On récupère la liste de toutes les notes dans la matière
        liste_notes: list = selenium_lines.pop(0).text.split("\n")

        if nom_matiere not in liste_matieres:

            matiere = add_notes(liste_notes, {
                "coef": 1,
                "moyenne": 20,
                "name": nom_matiere if nom_matiere != "Physique Chimie" else "Physique",
                "notes": []
            })

            if len(matiere["notes"]) > 1:
                notes_prepa["semestres"][f"semestre{semestre}"]["notes"].append(
                    matiere)
            
            if nom_matiere == "Colles de mathématiques":
                colles_de_maths = matiere
                matiere["coef"] = 0
            elif nom_matiere == "Colles de physique":
                colles_de_physique = matiere
                matiere["coef"] = 0

        else:  # Si la matière existe déjà
            index_matiere = next((index for (index, d) in enumerate(
                notes_prepa["semestres"][f"semestre{semestre}"]["notes"]) if d["name"] == nom_matiere), None)

            notes_prepa["semestres"][f"semestre{semestre}"]["notes"][index_matiere] = add_notes(
                liste_notes, notes_prepa["semestres"][f"semestre{semestre}"]["notes"][index_matiere])
    
    driver.quit()

    # On rajoute les colles de maths et physique

    liste_matieres = [
        matiere["name"] for matiere in notes_prepa["semestres"][f"semestre{semestre}"]["notes"]]

    if "Physique" in liste_matieres:
        liste_matieres.append("Physique Chimie")

    if colles_de_maths:
        index_matiere = next((index for (index, d) in enumerate(
            notes_prepa["semestres"][f"semestre{semestre}"]["notes"]) if d["name"] == "Mathématiques"), None)
        if index_matiere:
            note_colle_de_maths = {
                "coef": 3,
                "name": "Colles de mathématiques",
                "note": calcul_moyenne(colles_de_maths["notes"], type="note"),
                "gepi": True
            }
            if note_colle_de_maths in notes_prepa["semestres"][f"semestre{semestre}"]["notes"][index_matiere]["notes"]:
                notes_prepa["semestres"][f"semestre{semestre}"]["notes"][index_matiere].remove(note_colle_de_maths)
            notes_prepa["semestres"][f"semestre{semestre}"]["notes"][index_matiere]["notes"].append(note_colle_de_maths)

    if colles_de_physique:
        index_matiere = next((index for (index, d) in enumerate(
            notes_prepa["semestres"][f"semestre{semestre}"]["notes"]) if d["name"] == "Physique"), None)
        if index_matiere:
            note_colle_de_physique = {
                "coef": 3,
                "name": "Colles de physique",
                "note": calcul_moyenne(colles_de_physique["notes"], type="note"),
                "gepi": True
            }
            if note_colle_de_physique in notes_prepa["semestres"][f"semestre{semestre}"]["notes"][index_matiere]["notes"]:
                notes_prepa["semestres"][f"semestre{semestre}"]["notes"][index_matiere].remove(note_colle_de_physique)
            notes_prepa["semestres"][f"semestre{semestre}"]["notes"][index_matiere]["notes"].append(note_colle_de_physique)

    # On calcule les moyennes finales

    for semestre in range(1, 5):

        for matiere in notes_prepa["semestres"]["semestre" + str(semestre)]["notes"]:
            matiere["moyenne"] = calcul_moyenne(matiere["notes"], type="note")

        notes_prepa["semestres"]["semestre" + str(semestre)]["moyenne"] = calcul_moyenne(
            notes_prepa["semestres"]["semestre" + str(semestre)]["notes"])


    mongodb.db.Notes.replace_one(
            ({"username": str(current_user.username)}), notes_prepa)

    return notes_prepa["semestres"]


@app.route('/notes/get_notes')
@login_required
def get_notes():
    notes_prepa = mongodb.db.Notes.find_one(
        {"username": str(current_user.username)})
    if notes_prepa:

        # Calcul des moyennes

        for semestre in range(1, 5):

            for matiere in notes_prepa["semestres"]["semestre" + str(semestre)]["notes"]:
                matiere["moyenne"] = calcul_moyenne(
                    matiere["notes"], type="note")

            notes_prepa["semestres"]["semestre" + str(semestre)]["moyenne"] = calcul_moyenne(
                notes_prepa["semestres"]["semestre" + str(semestre)]["notes"])

        mongodb.db.Notes.replace_one(
            ({"username": str(current_user.username)}), notes_prepa)

        return notes_prepa["semestres"]

    notes_prepa = {
        "username": str(current_user.username),
        "semestres": {
            "semestre1": {
                "moyenne": 20,
                "notes": []
            },
            "semestre2": {
                "moyenne": 20,
                "notes": []
            },
            "semestre3": {
                "moyenne": 20,
                "notes":  []
            },
            "semestre4": {
                "moyenne": 20,
                "notes":  []
            },
        }
    }

    mongodb.db.Notes.insert_one(notes_prepa)

    return notes_prepa["semestres"]


@app.route('/notes/update_notes', methods=['GET', 'POST'])
@login_required
def update_notes():

    notes_prepa = mongodb.db.Notes.find_one(
        {"username": str(current_user.username)})

    notes_prepa["semestres"] = request.json

    for semestre in range(1, 5):

        for matiere in notes_prepa["semestres"]["semestre" + str(semestre)]["notes"]:
            matiere["moyenne"] = calcul_moyenne(matiere["notes"], type="note")

        notes_prepa["semestres"]["semestre" + str(semestre)]["moyenne"] = calcul_moyenne(
            notes_prepa["semestres"]["semestre" + str(semestre)]["notes"])

    mongodb.db.Notes.replace_one(
        ({"username": str(current_user.username)}), notes_prepa)

    return notes_prepa["semestres"]
