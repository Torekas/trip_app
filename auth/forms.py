from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(4, 25)])
    password = PasswordField("Password", validators=[DataRequired(), Length(6, 128)])
    confirm = PasswordField("Repeat Password", validators=[
        DataRequired(), EqualTo("password", message="Passwords must match")
    ])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")
