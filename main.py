from flask import Flask, flash, redirect, url_for, render_template, request
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired, Length
from flask_ckeditor import CKEditor, CKEditorField
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from typing import List
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from datetime import date, datetime
from os import environ
from bleach import clean
from werkzeug.security import check_password_hash

allowed_tags = ['a', 'b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li', 'blockquote']
allowed_attrs = {
    'a': ['href', 'title', 'target'],
}

year = date.today().year
SECRET_KEY = environ.get('CUSTOM_KEY')
APP_HOST = environ.get('CUSTOM_HOST')
APP_PORT = environ.get('CUSTOM_PORT')

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__, instance_relative_config=True)
ckeditor = CKEditor(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///home_helper.db"
db.init_app(app)
bootstrap = Bootstrap5(app)

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    f_name: Mapped[str] = mapped_column(String(32), nullable=False)
    l_name: Mapped[str] = mapped_column(String(32), nullable=False)
    added: Mapped[datetime] = mapped_column(default=datetime.now())
    user_notes: Mapped[List["Note"]] = relationship(back_populates="author")

class Note(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(32), nullable=False)
    body: Mapped[str] = mapped_column(String(20000))
    added: Mapped[datetime] = mapped_column(default=datetime.now())
    primary: Mapped[bool] = mapped_column(default=False)
    sticky: Mapped[bool] = mapped_column(default=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    author: Mapped["User"] = relationship(back_populates="user_notes")

with app.app_context():
    db.create_all()

@app.context_processor
def global_vars():
    return dict(year=year, user=current_user)

@app.route("/")
@login_required
def home():
    # Flash your users with fun messages with the code below:
    # flash('Very Important!', 'bg-success text-light text-center')
    primary_notes = Note.query.where(Note.author_id == f"{current_user.id}", Note.primary == True).order_by(Note.added).all()
    return render_template('index.html', primary_notes=primary_notes)

class LoginForm(FlaskForm):
    username = StringField('Username:', validators=[DataRequired(), Length(min=4, max=16)])
    password = PasswordField('Password:', validators=[DataRequired(), Length(min=4, max=32)])
    submit = SubmitField(label="Log In")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/login", methods=["POST", "GET"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.username == f"{login_form.username.data}")).scalar()
        if user and check_password_hash(user.password, login_form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'bg-success text-light')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Incorrect details!', 'bg-success text-light')
            return render_template('login.html', year=year, form=login_form)
    else:
        return render_template('login.html', year=year, form=login_form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/notes")
@login_required
def notes():
    with app.app_context():
        all_notes = Note.query.where(Note.author_id == f"{current_user.id}").order_by(Note.added).all()
        short_bodies = [clean(note.body[:40], tags=allowed_tags, attributes=allowed_attrs) for note in all_notes]
    return render_template('notes.html', all_notes=all_notes, short_bodies=short_bodies)


class UpdateNote(FlaskForm):
    title = StringField('Note Title:', validators=[DataRequired(), Length(max=32)])
    body = CKEditorField('Note Body:', validators=[DataRequired(), Length(max=20000)])
    primary = BooleanField('Primary Note')
    sticky = BooleanField('Sticky Note')
    submit = SubmitField(label="Save & Return")

@app.route("/notes/edit", methods=["POST", "GET"])
@app.route("/notes/edit/<note_id>", methods=["POST", "GET"])
@login_required
def update_note(note_id=None):
    update_note_form = UpdateNote()
    if update_note_form.validate_on_submit():
        if note_id:
            with app.app_context():
                note_to_update = db.get_or_404(Note, note_id)
                note_to_update.title = update_note_form.title.data
                note_to_update.body = update_note_form.body.data
                note_to_update.primary = update_note_form.primary.data
                note_to_update.sticky = update_note_form.sticky.data
                db.session.commit()
        else:
            note = Note(
                title=update_note_form.title.data,
                body=update_note_form.body.data,
                primary=update_note_form.primary.data,
                sticky=update_note_form.sticky.data,
                author=current_user,
                author_id=current_user
            )
            db.session.add(note)
            db.session.commit()
        flash('You successfully added/updated the note.', 'bg-success text-light text-center')
        return redirect(url_for('notes'))
    else:
        if note_id:
            update_note_form.title.data = db.get_or_404(Note, note_id).title
            update_note_form.body.data = db.get_or_404(Note, note_id).body
            update_note_form.primary.data = db.get_or_404(Note, note_id).primary
            update_note_form.sticky.data = db.get_or_404(Note, note_id).sticky
            return render_template('update_note.html', form=update_note_form, note_id=note_id)
        else:
            return render_template('update_note.html', form=update_note_form)

if __name__ == '__main__':
    app.run(host=APP_HOST, port=APP_PORT, debug=True)
