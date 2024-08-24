from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired, Length
from datetime import date
from os import environ

year = date.today().year
SECRET_KEY = environ.get('CUSTOM_KEY')
APP_HOST = environ.get('CUSTOM_HOST')
APP_PORT = environ.get('CUSTOM_PORT')

app = Flask(__name__, instance_relative_config=True)
app.config["SECRET_KEY"] = SECRET_KEY
bootstrap = Bootstrap5(app)

with open("data/backgrounds.txt", "r") as backgrounds, open("data/watchies.txt", "r") as watchies, \
        open("data/soundies.txt", "r") as soundies,open('data/notes.txt', "r") as notes:
    backgrounds = backgrounds.read().splitlines()
    watchies = watchies.read().splitlines()
    soundies = soundies.read().splitlines()
    extracted_notes = notes.read().splitlines()
    #users = [line.removeprefix("User: ") for line in raw_input if line.startswith("User: ")]

@app.route("/")
def home():
    return render_template('index.html', year=year, backgrounds=backgrounds, watchies=watchies,
                           soundies=soundies)

@app.route("/notes")
def notes():
    return render_template('notes.html', year=year, extracted_notes=extracted_notes)

class LoginForm(FlaskForm):
    username = StringField('Username:', validators=[DataRequired(), Length(min=8, max=16)])
    password = PasswordField('Password:', validators=[DataRequired(), Length(min=8, max=32)])
    submit = SubmitField(label="Log In")

@app.route("/login", methods=["POST", "GET"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        print(f"<h1>{login_form.username.data}, {login_form.password.data}</h1>")
        return "<h1>hi</h1>"
    else:
        return render_template('login.html', year=year, form=login_form)


class CreateNote(FlaskForm):
    note_title = StringField('Note Title:', validators=[DataRequired(), Length(max=32)])
    note_body = StringField('Note Body:', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField(label="Create Note")

@app.route("/notes/add")
def add_note():
    add_note_form = CreateNote()
    if add_note_form.validate_on_submit():
        print(f"<h1>{add_note_form.note_title.data}, {add_note_form.note_body.data}</h1>")
        return "<h1>hi</h1>"
    else:
        return render_template('add_note.html', year=year, form=add_note_form)

# @app.route("/notes/edit/<note_id>")
# def edit(note_id):
#     edit_notes = CreateNote()
#     if edit_notes.validate_on_submit():
#         print(f"<h1>{edit_notes.username.data}, {edit_notes.password.data}</h1>")
#         return "<h1>hi</h1>"
#     else:
#         return render_template('edit.html', note_id=note_id, year=year, form=edit_notes)

if __name__ == '__main__':
    app.run(host=APP_HOST, port=APP_PORT, debug=True)
