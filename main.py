from flask import Flask, flash, redirect, url_for, render_template
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired, Length, length
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from datetime import date, datetime
from os import environ

year = date.today().year
SECRET_KEY = environ.get('CUSTOM_KEY')
APP_HOST = environ.get('CUSTOM_HOST')
APP_PORT = environ.get('CUSTOM_PORT')

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__, instance_relative_config=True)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///home_helper.db"
db.init_app(app)
bootstrap = Bootstrap5(app)

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(16), unique=True)
    email: Mapped[str] = mapped_column(unique=True)

class Note(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(32))
    body: Mapped[str] = mapped_column(String(250))
    added: Mapped[datetime] = mapped_column(default=datetime.now())

with app.app_context():
    db.create_all()

@app.context_processor
def inject_year():
    return dict(year=year)

@app.route("/")
def home():
    flash('Very Important!', 'bg-success text-light')
    return render_template('index.html')

class LoginForm(FlaskForm):
    username = StringField('Username:', validators=[DataRequired(), Length(min=8, max=16)])
    password = PasswordField('Password:', validators=[DataRequired(), Length(min=8, max=32)])
    submit = SubmitField(label="Log In")

@app.route("/login", methods=["POST", "GET"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User(
            username=login_form.username.data,
            email=login_form.password.data,
        )
        db.session.add(user)
        db.session.commit()
        return "<h1>Done</h1>"
    else:
        return render_template('login.html', year=year, form=login_form)

@app.route("/notes")
def notes():
    with app.app_context():
        result = db.session.execute(db.select(Note).order_by(Note.title))
        all_notes = result.scalars().all()
    return render_template('notes.html', all_notes=all_notes)


class UpdateNote(FlaskForm):
    title = StringField('Note Title:', validators=[DataRequired(), Length(max=32)])
    body = StringField('Note Body:', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField(label="Create Note")

@app.route("/notes/edit", methods=["POST", "GET"])
@app.route("/notes/edit/<note_id>", methods=["POST", "GET"])
def update_note(note_id=None):
    update_note_form = UpdateNote()
    if update_note_form.validate_on_submit():
        note = Note(
            title=update_note_form.title.data,
            body=update_note_form.body.data,
        )
        db.session.add(note)
        db.session.commit()
        flash('You successfully added/updated the note.', 'bg-success text-light text-center')
        return redirect(url_for('notes'))
    else:
        if note_id:
            return render_template('update_note.html', form=update_note_form, note_id=note_id)
        else:
            return render_template('update_note.html', form=update_note_form)

if __name__ == '__main__':
    app.run(host=APP_HOST, port=APP_PORT, debug=True)
