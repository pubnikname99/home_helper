from flask import Flask, flash, redirect, url_for, render_template, request
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SearchField, IntegerField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_ckeditor import CKEditor, CKEditorField
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, or_
from typing import List
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from datetime import date, datetime
from os import environ
from bleach import clean
from urllib.parse import quote
from werkzeug.security import check_password_hash

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
    user_searches: Mapped[List["SearchHistory"]] = relationship(back_populates="author")

class Note(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(32), nullable=False)
    body: Mapped[str] = mapped_column(String(20000))
    added: Mapped[datetime] = mapped_column(default=datetime.now())
    edited: Mapped[datetime] = mapped_column(default=datetime.now())
    primary: Mapped[bool] = mapped_column(default=False)
    sticky: Mapped[bool] = mapped_column(default=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    author: Mapped["User"] = relationship(back_populates="user_notes")

class SearchHistory(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    search_type: Mapped[str] = mapped_column(String(32), nullable=False)
    search_value: Mapped[str] = mapped_column(String(32), nullable=False)
    times_searched: Mapped[int] = mapped_column(default=1, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    author: Mapped["User"] = relationship(back_populates="user_searches")

with app.app_context():
    db.create_all()

@app.context_processor
def global_vars():
    search_form = SearchForm()
    refresh_form = RefreshForm()
    return dict(year=year, user=current_user, search_form=search_form, refresh_form=refresh_form, auto_refresh_on=auto_refresh_on)

class SearchForm(FlaskForm):
    search_type = SelectField(choices=[("self", "This site"), ("goo", "Google"), ("yt", "YouTube")], validate_choice=True, validators=[DataRequired(), Length(min=4, max=16)])
    search_value = SearchField(validators=[DataRequired(), Length(min=1, max=32)])

@app.route("/search", methods=["POST"])
@login_required
def do_search():
    search_form = SearchForm()
    search_query = search_form.search_value.data
    search_query_encoded = quote(search_query, safe='')
    existing_search_id = db.session.execute(db.select(SearchHistory).where(SearchHistory.search_value == f"{search_query}",
                                                                           SearchHistory.search_type == f"{search_form.search_type.data}")).scalar()
    if existing_search_id:
        with app.app_context():
            search_to_update = db.get_or_404(SearchHistory, existing_search_id.id)
            search_to_update.times_searched = search_to_update.times_searched + 1
            db.session.commit()
    else:
        new_search = SearchHistory(
            search_type=search_form.search_type.data,
            search_value=search_form.search_value.data,
            author=current_user
        )
        db.session.add(new_search)
        db.session.commit()
    match search_form.search_type.data:
        case "self":
            return redirect(url_for('search_results', query=search_query))
        case "goo":
            return redirect(f"https://www.google.com/search?q={search_query_encoded}")
        case "yt":
            return redirect(f"https://www.youtube.com/results?search_query={search_query_encoded}")
        case _:
            flash('Invalid search type!', 'bg-success text-light')
            return render_template(f'{request.url_rule.endpoint}')

@app.route("/search/results", methods=["GET"])
@login_required
def search_results():
    query = request.args.get('query')
    found_items = Note.query.where(or_(Note.body.like(f"%{query}%"),
                                       Note.title.like(f"%{query}%"))).order_by(Note.added).all()
    return render_template("search.html", found_items=found_items)

@app.route("/search/history", methods=["GET"])
@login_required
def search_history():
    found_items = SearchHistory.query.where(SearchHistory.author_id == f"{current_user.id}").order_by(SearchHistory.times_searched).all()
    return render_template("history.html", found_items=found_items)

class RefreshForm(FlaskForm):
    refresh_seconds = IntegerField('Auto Refresh (9 - 180 seconds): ', validators=[DataRequired(), NumberRange(min=9, max=180)])

refresh_seconds = None
auto_refresh_on = False
@app.route("/", methods=["POST", "GET"])
@login_required
def home():
    # Flash your users with fun messages with the code below:
    # flash('Very Important!', 'bg-success text-light text-center')
    refresh_form = RefreshForm()
    global refresh_seconds, auto_refresh_on
    if refresh_form.validate_on_submit():
        if refresh_form.refresh_seconds.data is 9:
            auto_refresh_on = False
        else:
            auto_refresh_on = True
        refresh_seconds = refresh_form.refresh_seconds.data
    primary_notes = Note.query.where(Note.author_id == f"{current_user.id}", Note.primary == True).order_by(Note.added).all()
    return render_template('index.html', primary_notes=primary_notes, refresh_seconds=refresh_seconds)

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
            return render_template('login.html', form=login_form)
    else:
        return render_template('login.html', form=login_form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/notes")
@login_required
def notes():
    with app.app_context():
        allowed_tags = ['a', 'b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li', 'blockquote']
        allowed_attrs = {
            'a': ['href', 'title', 'target'],
        }
        all_notes = Note.query.where(Note.author_id == f"{current_user.id}").order_by(Note.added).all()
        short_bodies = [clean(note.body[:40], tags=allowed_tags, attributes=allowed_attrs) for note in all_notes]
    return render_template('notes.html', all_notes=all_notes, short_bodies=short_bodies)


class UpdateNote(FlaskForm):
    title = StringField('Note Title:', validators=[DataRequired(), Length(max=32)])
    body = CKEditorField('Note Body:', validators=[Length(max=20000)])
    primary = BooleanField('Primary Note')
    sticky = BooleanField('Sticky Note')
    submit = SubmitField(label="Save & Return")
    delete = SubmitField(label="Delete")

@app.route("/notes/edit", methods=["POST", "GET"])
@app.route("/notes/edit/<int:note_id>", methods=["POST", "GET"])
@login_required
def update_note(note_id=None):
    update_note_form = UpdateNote()
    print(f"Request Path: {request.path}")
    print(note_id)
    if update_note_form.validate_on_submit():
        print(note_id)
        if note_id:
            note_to_update = db.get_or_404(Note, note_id)
            if update_note_form.delete.data:
                db.session.delete(note_to_update)
                flash('You successfully deleted the note.', 'bg-success text-light text-center')
            else:
                with app.app_context():
                    note_to_update.title = update_note_form.title.data
                    note_to_update.body = update_note_form.body.data
                    note_to_update.edited = datetime.now()
                    note_to_update.primary = update_note_form.primary.data
                    note_to_update.sticky = update_note_form.sticky.data
                flash('You successfully updated the note.', 'bg-success text-light text-center')
            db.session.commit()
        else:
            print(note_id)
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
            flash('You successfully added the note.', 'bg-success text-light text-center')
        return redirect(url_for('home'))
    else:
        if note_id:
            note_to_update = db.get_or_404(Note, note_id)
            update_note_form.title.data = note_to_update.title
            update_note_form.body.data = note_to_update.body
            update_note_form.primary.data = note_to_update.primary
            update_note_form.sticky.data = note_to_update.sticky
            return render_template('update_note.html', form=update_note_form, note_id=note_id)
        else:
            return render_template('update_note.html', form=update_note_form, note_id=note_id)

if __name__ == '__main__':
    app.run(host=APP_HOST, port=APP_PORT, debug=True)
