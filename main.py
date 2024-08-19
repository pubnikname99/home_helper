from flask import Flask, render_template
from datetime import date

app = Flask(__name__)
year = date.today().year

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

# # Variable routing
# @app.route("/<username>")
# def userspace(username):
#     return render_template('index.html')

if __name__ == '__main__':
    app.run(port=23232, debug=True)
