
"""
    Module qui réference les formulaires de flask_wtf
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Email, Length, Optional

class LoginForm(FlaskForm):
    username = StringField("Nom d'utilisateur ou Email", validators=[InputRequired()])
    password = PasswordField('Mot de passe', validators=[InputRequired(), Length(min=6, max=80)])
    remember = BooleanField('Se rappeller de moi')

class RegisterForm(FlaskForm):
    name = StringField('Prénom', validators=[InputRequired()])
    surname = StringField('Nom', validators=[InputRequired()])
    promo = IntegerField('Promo', validators=[InputRequired()])
    sesame = StringField("Sésame", validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('Mot de passe', validators=[InputRequired(), Length(min=6, max=80)])
    password_confirm = PasswordField('', validators=[InputRequired(), Length(min=6, max=80)])
    remember = BooleanField('Se rappeller de moi')


class ChangeSelfInformationsForm(FlaskForm):
    name = StringField('Prénom')
    surname = StringField('Nom')
    email = StringField('Email', validators=[Optional(), Email(message='Invalid email'), Length(max=50)])
    current_password = PasswordField('Mot de passe actuel *', validators=[InputRequired(), Length(min=6, max=80)])
    new_password = PasswordField('Nouveau mot de passe', validators=[Optional(), Length(min=6, max=80)])
    new_password_confirm = PasswordField('Confirmer votre nouveau mot de passe', validators=[Optional(), Length(min=6, max=80)])

class ProfilePicForm(FlaskForm):
    profile_pic = StringField("Changer votre photo de profil")
    

class RequestResetPasswordForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired()])

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('Nouveau mot de passe', validators=[InputRequired(), Length(min=6, max=80)])
    new_password_confirm = PasswordField('Confirmer votre nouveau mot de passe', validators=[InputRequired(), Length(min=6, max=80)])
    submit = SubmitField('Réinitialiser mon mot de passe')
