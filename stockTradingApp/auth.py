from flask import Flask, request, redirect, url_for, Blueprint, session, render_template, flash
from werkzeug.security import check_password_hash, generate_password_hash
from stockTradingApp.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# this login is a client-side login. the server does not store sessions. instead,
# the session object is stored on the client browser and encryptyed. this is the way flask
# does sessions by default. so, in reality, the 'session' object is passed to the server 
# when the browser does any HTTP request to the server. for more info, see flask_session.txt
@bp.route('/login', methods=['GET','POST'])
def login(message=None):
    if not message:
        message = None

    print(session)
    if request.method == 'POST':
        db = get_db()
        message = None

        username = request.form['username']
        password = request.form['password']

        if not username:
            message = 'Username is required.'
        elif not password:
            message = 'Password is required.'
        else:
            user = db.execute("SELECT * FROM user WHERE username = ?", (username,)).fetchone()

        if user is None:
            message = "Incorrect username"
        elif not check_password_hash(user['password'], password):
            message = "Incorrect password"
        
        if message is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('endpoints.index'))
        else:
            return render_template('./login_forms/login_form--homepage.html', message=message)
    else:
        if not session or not session.get('user_id'):
            return render_template('./login_forms/login_form--homepage.html', message=message)
        else:
            return redirect(url_for('endpoints.index'))

@bp.route('/register', methods=['GET','POST'])
def register():
    message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            db.execute(
                'INSERT INTO user (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            db.commit()
            message = "Successfully registered!"
            flash(message)
            return redirect(url_for('.login'))
        else:
            return render_template('./login_forms/register_form--homepage.html', message=error)

    else:
        if not session or not session['user_id']:
            return render_template('./login_forms/register_form--homepage.html', message=message)
        else:
            return redirect(url_for('endpoints.index'))


# simple get request to logout
@bp.route('/logout')
def logout():
   # remove the username from the session if it is there
   session.pop('user_id', None)
   return redirect(url_for('endpoints.index'))
