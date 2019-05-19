from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Blueprint
from . import helper_functions as helpFunc
from .db import get_db
import requests

bp = Blueprint('endpoints', __name__)

@bp.route('/')
@helpFunc.login_required
def index():
    return redirect(url_for('.dashboard'))

@bp.route('/dashboard')
@helpFunc.login_required
def dashboard():
    db = get_db()
    user = db.execute("SELECT * from user WHERE id = ?", (session.get('user_id'),)).fetchone()

    if user: 
        username = user['username']
    else: 
        username = ""

    return render_template('./containers/dashboard.html', username=username, title="Dashboard")

@bp.route('/trade')
@helpFunc.login_required
def trade():
    db = get_db()
    user = db.execute("SELECT * from user WHERE id = ?", (session.get('user_id'),)).fetchone()

    if user: 
        username = user['username']
    else: 
        username = ""
    
    stockTitle='Apple'
    stockTicker='AAPL'

    return render_template('./containers/trade.html', username=username, stockTitle=stockTitle, stockTicker=stockTicker, title="Buy/Sell " + stockTicker)

@bp.route('/search')
@helpFunc.login_required
def search():
    db = get_db()
    user = db.execute("SELECT * from user WHERE id = ?", (session.get('user_id'),)).fetchone()

    if user: 
        username = user['username']
    else: 
        username = ""
    
    # check if user searched stock ticker
    stockTicker=request.args.get('stockTicker').upper()
    if stockTicker is None:
        stockTicker = ""
    stockTitle=get_name(stockTicker)

    # check if user searched stock title/name
    if stockTitle is None:
        stockTitle= request.args.get('stockTicker')
        if stockTitle is None:
            stockTitle=""
        stockTicker = get_ticker(stockTitle)
        stockTitle=get_name(stockTicker)

    if stockTicker is None or stockTitle is None:
        return render_template('./containers/404.html', title="404")

    # remove commas since trading view bug
    stockTitle = stockTitle.replace(',', '')

    return render_template('./containers/trade.html', username=username, stockTitle=stockTitle, stockTicker=stockTicker, title="Buy/Sell " + stockTitle)


# helper functions
def get_name(symbol):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)
    result = requests.get(url).json()
    for x in result['ResultSet']['Result']:
        if x['symbol'] == symbol:
            return x['name']

def get_ticker(name):
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(name)
    result = requests.get(url).json()
    for x in result['ResultSet']['Result']:
        if name in x['name']:
            return x['symbol']
