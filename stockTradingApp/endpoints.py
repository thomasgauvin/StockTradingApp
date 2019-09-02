from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Blueprint, flash, current_app
from collections import defaultdict
from . import helper_functions as helpFunc
from .db import get_db
import requests
import json
from iexfinance.stocks import Stock, get_historical_data
from datetime import date

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

    return render_template('./containers/dashboard.html', username=username, title="Dashboard", holdings = get_holdings(user['id'], db))

@bp.route('/trade')
@helpFunc.login_required
def trade():
    db = get_db()
    user = db.execute("SELECT * from user WHERE id = ?", (session.get('user_id'),)).fetchone()

    if user: 
        username = user['username']
    else: 
        username = ""

    return render_template('./containers/trade.html', title="Trade", trade_log = get_trade_log(user['id'], db))

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
    stockTitle = ""
    stockPrice = 0
    today = ""

    try:

        #if non US exchange
        if check_for_non_us_exchange(stockTicker):
            stockTitle=get_name(stockTicker[stockTicker.index(':')+1:])
            return render_template('./containers/stock.html', username=username, stockTitle=stockTitle, stockTicker=stockTicker, title="Buy/Sell " + stockTitle)

        #special check for bitcoin and ethereum to usd
        if stockTicker == "BITCOIN":
            stockTicker = "BTCUSD"
        if stockTicker == "ETHEREUM":
            stockTicker = "ETHUSD"

        if stockTicker is None:
            stockTicker = ""
        stockTitle=get_name(stockTicker)

           # get stock price
        stock = Stock(stockTicker, token = current_app.config['IEX_TOKEN'])
        stockPrice = stock.get_price()
        today = str(date.today())

        # check if user searched stock title/name
        if stockTitle is None:
            stockTitle= request.args.get('stockTicker')
            if stockTitle is None:
                stockTitle=""
            stockTicker = get_ticker(stockTitle)
            stockTitle=get_name(stockTicker)
        
    except:
        return render_template('./containers/404.html', title="404")

    if stockTicker is None or stockTitle is None:
        return render_template('./containers/404.html', title="404")

    # remove commas since trading view bug
    stockTitle = stockTitle.replace(',', '')

 

    return render_template('./containers/stock.html', username=username, stockTitle=stockTitle, stockTicker=stockTicker, title="Buy/Sell " + stockTitle, stockPrice = stockPrice, date = today)

@bp.route('/buy', methods=['GET', 'POST'])
@helpFunc.login_required
def buy():
    db = get_db()
    user = db.execute("SELECT * from user WHERE id = ?", (session.get('user_id'),)).fetchone()

    if user: 
        username = user['username']
    else: 
        username = ""

    stockTicker=request.form['stockTicker'].upper()
    stockPrice = request.form['stockPrice']
    amountToBuy = request.form['amount']
    date = request.form['date']

    if not stockTicker or not stockPrice or not amountToBuy or not date:
        error = 'Missing information.'
        flash(error)
        return render_template('./containers/trade.html', username=username, title="Trade", trade_log = get_trade_log(user['id'], db))

    # if not get_name(stockTicker): # if we cant get a stock name, the stock ticker is wrong
    #     error = 'Wrong stock ticker.'
    #     flash(error)
    #     return render_template('./containers/trade.html', username=username, title="Trade", trade_log = get_trade_log(user['id'], db))

    action = 'BUY'
    db.execute(
        'INSERT INTO action (userId, type, stock, quantity, price, date) VALUES (?, ?, ?, ?, ?, ?)',
        (user['id'], action, stockTicker, amountToBuy, stockPrice, date)
    )
    db.commit()
    message = "You have successfully bought " + str(amountToBuy) + " " + str(stockTicker) + " at a cost of " + str(stockPrice)
    flash(message)
    return render_template('./containers/trade.html', username=username, title="Trade", trade_log=get_trade_log(user['id'], db))


@bp.route('/sell', methods=['POST'])
@helpFunc.login_required
def sell():
    db = get_db()
    user = db.execute("SELECT * from user WHERE id = ?", (session.get('user_id'),)).fetchone()

    if user: 
        username = user['username']
    else: 
        username = ""

    stockTicker=request.form['stockTicker'].upper()
    stockPrice = float(request.form['stockPrice'])
    amountToBuy = float(request.form['amount'])
    date = request.form['date']

    if not stockTicker or not stockPrice or not amountToBuy or not date or not user:
        error = 'Missing information.'
        flash(error)
        return render_template('./containers/trade.html', username=username, title="Trade", trade_log = get_trade_log(user['id'], db))

    # if not get_name(stockTicker): # if we cant get a stock name, the stock ticker is wrong
    #     error = 'Wrong stock ticker.'
    #     flash(error)
    #     return render_template('./containers/trade.html', username=username, title="Trade", trade_log = get_trade_log(user['id'], db))

    if amountToBuy > amount_of_stock_to_sell(stockTicker, db): # if trying to sell more than we have
        error = 'You do not have enough stock to sell.'
        flash(error)
        return render_template('./containers/trade.html', username=username, title="Trade", trade_log = get_trade_log(user['id'], db))
    
    action = 'SELL'
    db.execute(
        'INSERT INTO action (userId, type, stock, quantity, price, date) VALUES (?, ?, ?, ?, ?, ?)',
        (user['id'], action, stockTicker, amountToBuy, stockPrice, date)
    )
    db.commit()
    message = "You have successfully sold " + str(amountToBuy) + " " + str(stockTicker) + " at a cost of " + str(stockPrice)
    flash(message)
    return render_template('./containers/trade.html', username=username, title="Trade", trade_log = get_trade_log(user['id'], db))


##################################################################################################################

# helper functions
def get_name(symbol):
    if symbol is None:
        return ""
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)
    result = requests.get(url).json()
    for x in result['ResultSet']['Result']:
        if symbol in x['symbol']:
            return x['name']

def get_ticker(name):
    if name is None:
        return ""
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(name)
    result = requests.get(url).json()
    for x in result['ResultSet']['Result']:
        if name in x['name']:
            return x['symbol']

def check_for_non_us_exchange(stockTicker):
    if ':' in stockTicker:
        return True
    else:
        return False

def amount_of_stock_to_sell(stockTicker, db):
    stockRows = db.execute("SELECT * from action WHERE stock = ?", (stockTicker,)).fetchall()
    stockAmount = 0
    for row in stockRows:
        if row['type']=='BUY':
            stockAmount += row['quantity'] 
        elif row['type'] == 'SELL':
            stockAmount -= row['quantity']
    return stockAmount

def get_trade_log(user_id, db):
    stockRows = db.execute("SELECT * from action WHERE userId = ? ORDER BY date DESC", (user_id,)).fetchall()
    return stockRows

def get_holdings(user_id, db):
    stockRows = db.execute("SELECT * from action WHERE userId = ?", (user_id,)).fetchall()
    holdings = dict(defaultdict())
    print(holdings)

    for row in stockRows:
        if not row['stock'] in holdings:
            holdings[row['stock']] = {'stock':row['stock'], 'quantity':0, 'book_price': "", 'current_price':0, 'book_worth': 0, 'current_worth':0,  'historical_data': [], 'gain$':0, 'gain%':0}
        if row['type']=='BUY':
            holdings[row['stock']]['quantity']+=row['quantity']
        elif row['type'] == 'SELL':
            holdings[row['stock']]['quantity']-=row['quantity']
        holdings[row['stock']]['date_bought']=row['date']
        holdings[row['stock']]['book_price']=helpFunc.currency(row['price'])

    print(holdings)
    for holding in list(holdings):
        if holdings[holding]['quantity']==0:
            del holdings[holding]
    
    print(holdings)
    for holding in holdings:
        print(holding)
        holdings[holding]['book_worth']=helpFunc.currency(holdings[holding]['book_price']*holdings[holding]['quantity'])

        stock = Stock(holdings[holding]['stock'], token = current_app.config['IEX_TOKEN'])

        # catch error if IEX is unable to fulfill the request
        try:
            stockPrice = stock.get_price()
            print(stockPrice)
            holdings[holding]['current_price']= helpFunc.currency(stockPrice)
            holdings[holding]['current_worth']= helpFunc.currency(holdings[holding]['current_price']*holdings[holding]['quantity'])
            holdings[holding]['historical_data']= stock.get_historical_prices()
            holdings[holding]['gain$']=helpFunc.currency(stockPrice-holdings[holding]['book_price'])
            holdings[holding]['gain%']=helpFunc.currency(stockPrice/holdings[holding]['book_price']*100-100)
        except:
            holdings[holding]['current_price']= "N/A, API limited to US stocks"
            holdings[holding]['current_worth']= "N/A"

    print(holdings)   
    return holdings
