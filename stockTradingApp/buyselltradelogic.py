from flask import g, Blueprint, current_app
from .db import get_db

bp = Blueprint('buyselltradelogic', __name__)

@bp.route('/deposit', methods=['POST'])
def deposit():
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
