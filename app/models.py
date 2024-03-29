
"""
    Module qui définit certains objets utilisés dans l'application
"""

import datetime
from flask import Flask, send_from_directory, request
from flask_login import UserMixin, LoginManager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from app import app, mongodb, login_manager

@login_manager.user_loader
def load_user(user_id):
    user = User(mongodb.db.Users.find_one({"_id": int(user_id)}))
    if user:
        return user

class User(UserMixin):
    def __init__(self, user_dict):
        self.id = user_dict.get('_id')
        self.name = user_dict.get('name')
        self.surname = user_dict.get('surname')
        self.username = user_dict.get('username')
        self.email = user_dict.get('email')
        self.password = user_dict.get('password')
        self.accountType = user_dict.get('accountType')
        self.theaming = user_dict.get('theaming')
        self.promo = user_dict.get("promo")
        self.profil_pic_url = user_dict.get("profil_pic_url")
    
    def annee(self):
        date = datetime.datetime.now()
        if date.month > 7 :
            return date.year - 2009 - self.promo + 1
        return date.year - 2010 - self.promo + 1
    
    def semestre(self):
        date = datetime.datetime.now()
        annee = self.annee()
        if annee == 1:
            if date.month > 7:
                return 1
            return 2
        elif annee == 2:
            if date.month > 7:
                return 3
            return 4
        return None

    def est_admin(self):
        return self.accountType == "admin"
    
    def est_etudiant(self):
        return self.accountType in ("élève", "admin")

    def est_secretaire(self):
        return self.accountType in ("secretaire", "admin")
    
    def get_id(self):
        return str(self.id)

    def get_reset_token(self, expires_sec=1800):
        # Permet de créer un token de rénitialisation de mot de passe.
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        # Permet de vérifier qu'un token de rénitialisation de mot de passe est valide.
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User(mongodb.db.Users.find_one({"_id": user_id}))


class Tool():
    def __init__(self, tool_dict):
        self.id = tool_dict.get('_id')
        self.name = tool_dict.get('name')
        self.description = tool_dict.get('description')
        self.url = tool_dict.get('url')


class Addresses():
    def __init__(self, addresses_dict):
        self.id = addresses_dict.get('_id')
        self.name = addresses_dict.get('name')
        self.description = addresses_dict.get('description')
        self.stars = addresses_dict.get('stars')
        self.url = addresses_dict.get('url')
        self.maps = addresses_dict.get('maps')
        self.localisation = addresses_dict.get('localisation')
    

