from functools import wraps
from flask import g, request, redirect, url_for, Blueprint, session

bp = Blueprint('helper_functions', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def currency(f):
    return float(int(f * 100))/100