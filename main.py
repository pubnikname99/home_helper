from flask import Flask, render_template
from datetime import date

app = Flask(__name__)
year = date.today().year

#!!!!!!!! Once you upgrade from Python 3.7 on Pi4 please use below syntax and remove .close() at bottom .. also remove
# .read().splitlines()
# with (open("data/backgrounds.txt") as backgrounds,
#       open("data/watchies.txt") as watchies,
#       open("data/soundies.txt") as soundies,
#       open('data/notes.txt') as notes):
#     backgrounds = backgrounds.read().splitlines()
#     watchies = watchies.read().splitlines()
#     soundies = soundies.read().splitlines()
#     extracted_notes = notes.read().splitlines()
#     #users = [line.removeprefix("User: ") for line in raw_input if line.startswith("User: ")]
backgrounds = open("data/backgrounds.txt")
watchies = open("data/watchies.txt")
soundies = open("data/soundies.txt")
extracted_notes = open("data/notes.txt")


@app.route("/")
def home():
    return render_template('index.html', year=year, backgrounds=backgrounds.read().splitlines()
                           , watchies=watchies.read().splitlines(), soundies=soundies.read().splitlines())


@app.route("/notes")
def notes():
    return render_template('notes.html', year=year, extracted_notes=extracted_notes.read().splitlines())

# # Variable routing
# @app.route("/<username>")
# def userspace(username):
#     return render_template('index.html')

if __name__ == '__main__':
    app.run(port=23232, debug=True)

# closes
backgrounds.close()
watchies.close()
soundies.close()
extracted_notes.close()
