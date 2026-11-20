"""
    Module qui gère les api de la page notes
"""

from flask import request
from flask_login import login_required, current_user

from app import app, mongodb


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


def calcul_moyennes(notes_prepa):
    """Recalcule les moyennes de chaque matière, semestre et la moyenne prépa."""
    for semestre in range(1, 5):

        for matiere in notes_prepa["semestres"]["semestre" + str(semestre)]["notes"]:
            matiere["moyenne"] = calcul_moyenne(matiere["notes"], type="note")

        notes_prepa["semestres"]["semestre" + str(semestre)]["moyenne"] = calcul_moyenne(
            notes_prepa["semestres"]["semestre" + str(semestre)]["notes"])

    notes_prepa["semestres"]["prepa"] = {
        "moyenne": 20,
        "notes": [
            {"semestre": 1, "coef": 1, "moyenne": notes_prepa["semestres"]["semestre1"]["moyenne"]},
            {"semestre": 2, "coef": 1, "moyenne": notes_prepa["semestres"]["semestre2"]["moyenne"]},
            {"semestre": 3, "coef": 1.5, "moyenne": notes_prepa["semestres"]["semestre3"]["moyenne"]},
            {"semestre": 4, "coef": 1.5, "moyenne": notes_prepa["semestres"]["semestre4"]["moyenne"]}
        ]
    }

    sum_prepa = 0
    coef_prepa = 0
    for semestre in range(0, 4):
        if notes_prepa["semestres"]["prepa"]["notes"][semestre]["moyenne"]:
            sum_prepa += (notes_prepa["semestres"]["prepa"]["notes"][semestre]["moyenne"]
                          * notes_prepa["semestres"]["prepa"]["notes"][semestre]["coef"])
            coef_prepa += notes_prepa["semestres"]["prepa"]["notes"][semestre]["coef"]

    if coef_prepa != 0:
        notes_prepa["semestres"]["prepa"]["moyenne"] = round(sum_prepa / coef_prepa, 3)

    return notes_prepa


@app.route('/notes/get_notes')
@login_required
def get_notes():
    """
        Api qui permet de récupérer les notes de l'utilisateur depuis la base de données
    """
    notes_prepa = mongodb.db.Notes.find_one(
        {"username": str(current_user.username)})

    if not notes_prepa:
        notes_prepa = {
            "username": str(current_user.username),
            "semestres": {
                "semestre1": {"moyenne": 20, "notes": []},
                "semestre2": {"moyenne": 20, "notes": []},
                "semestre3": {"moyenne": 20, "notes": []},
                "semestre4": {"moyenne": 20, "notes": []},
                "prepa": {"moyenne": 20, "notes": []},
            }
        }
        mongodb.db.Notes.insert_one(notes_prepa)

    notes_prepa = calcul_moyennes(notes_prepa)

    mongodb.db.Notes.replace_one(
        {"username": str(current_user.username)}, notes_prepa)

    return notes_prepa["semestres"]


@app.route('/notes/update_notes', methods=['POST'])
@login_required
def update_notes():
    """
        Api qui permet d'enregistrer les notes modifiées par l'utilisateur
    """
    notes_prepa = mongodb.db.Notes.find_one(
        {"username": str(current_user.username)})

    if not notes_prepa:
        notes_prepa = {"username": str(current_user.username)}

    notes_prepa["semestres"] = request.json

    notes_prepa = calcul_moyennes(notes_prepa)

    mongodb.db.Notes.replace_one(
        {"username": str(current_user.username)}, notes_prepa, upsert=True)

    return notes_prepa["semestres"]
