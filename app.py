from flask import Flask, render_template, request, jsonify, session, redirect
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

class Testing:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def myfunc(self):
        print("Hello my name is " + self.name)

a = Testing('Thomas', 18)

@app.route('/')
def index():
    if not session.get('logged_in'):
        return "<h1>Not logged in</h1>"
    else:
        return "<h1>Logged in</h1>"

@app.route('/api/randomobject')
def randomObject():
    return jsonify(
        name=a.name,
        age=a.age
    )

# this login is a client-side login. the server does not store sessions. instead,
# the session object is stored on the client browser and encryptyed. this is the way flask
# does sessions by default. so, in reality, the 'session' object is passed to the server 
# when the browser does any HTTP request to the server. for more info, see flask_session.txt
@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    print(session)
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'pass':
            error = 'Invalid Credentials. Please try again.'
        else:
            session['logged_in'] = True
            return render_template('./login_forms/login_form--homepage.html', error="logged in dude")
    return render_template('./login_forms/login_form--homepage.html', error=error)

@app.route('/logout')
def logout():
   # remove the username from the session if it is there
   session.pop('logged_in', None)
   return index()