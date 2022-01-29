from flask import Flask, json, render_template, request, jsonify
from dotenv import load_dotenv
from db import PortfolioDB, PortfolioAlreadyExistsException, PortfolioNotFoundException
from util import result_to_csv
import requests
import math
import os

load_dotenv()


app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True

auth = {
    'username': os.environ.get('usernamedb'),
    'password': os.environ.get('passworddb'),
}
db_name = os.environ.get('database')

db = PortfolioDB(auth, db_name)

SYMBOLS = []


@app.route('/', methods=['GET'])
def home():
    portfolio_names = db.get_portfolio_names()
    return render_template('index.html', portfolio_names=portfolio_names, calculated='false')


def load_symbols():
    with open('symbols.csv', 'r', encoding='utf8') as f:
        global SYMBOLS
        SYMBOLS = [symbol.replace('|', ' - ') for symbol in f.read().split('\n')]
        print('Symbols loaded')
        
@app.route('/symbols', methods=['GET'])
def get_symbols():
    global SYMBOLS
    return jsonify(SYMBOLS)


#Calculator Routes    

@app.route('/calculate', methods=['GET'])
def calculate_page():
    portfolio_names = db.get_portfolio_names()
    return render_template('calculate.html', portfolio_names=portfolio_names, calculated='false')

@app.route('/calculate/calculator', methods=['POST'])
def calculate():
    form = request.form.to_dict()
    years = int(form['years'])
    commission = float(form.get('commission'))
    symbol = form.get('symbols')
    mode = form.get('modes')
    portfolio_name = form.get('portfolio')
    frequency = form.get('frequency')
    try:
        portfolio_data = db.get_portfolio_data(portfolio_name)
        #stock_data = get_temp_stock_data()
        stock_data = get_stock_data(symbol, frequency)
        if stock_data is None:
            return 'There was a problem getting a request from the API'
        result = {}
        if mode == "cash":
            cash = float(form.get('cash')) 
            if portfolio_data['funds'] < float(cash):
                return render_template('calculate.html', has_error=True, error_message='Not enough funds', calculated='false')
            
            calculation_result = dividend_calculator(cash, portfolio_data['funds'],years, stock_data, frequency=frequency, commission=commission)
            result['calculation_result'] = calculation_result
            form['funds'] = (portfolio_data['funds'] - cash) + result['calculation_result'][1][1]['cash_balance_after_invest']
        
        elif mode == "share":
            stock_number = int(form['stockBuyCount'])
            custom_stock_price = float(form['stockPrice'])
            funds_required = custom_stock_price * stock_number
            if portfolio_data['funds'] < funds_required:
                return render_template('calculate.html', has_error=True, error_message='Not enough funds', calculated='false')
            
            stock_data['price'] = custom_stock_price
            calculation_result = dividend_calculator(funds_required, portfolio_data['funds'], years, stock_data, frequency=frequency,commission=commission)
            result['calculation_result'] = calculation_result
            form['funds'] = (portfolio_data['funds'] - funds_required) + result['calculation_result'][1][1]['cash_balance_after_invest']
        else:
            return render_template('calculate.html', has_error=True, error_message='Invalid investment method', calculated='false')
        result['stock_data'] = stock_data
        is_drip = True if request.form.get('drip') == '1' else False
        csv_result = result_to_csv(result, form)
        frequency = get_frequency_data(1)[frequency]['name']
        return render_template('calculate.html', result=result, csv=csv_result, is_drip=is_drip, frequency=frequency, calculated='true', prev_form=form)
    except PortfolioNotFoundException:
        return render_template('calculate.html', has_error=True, error_message='Portfolio doesn\t exists', calculated='false')

#Portfolio Routes

@app.route('/portfolio/add', methods=['POST'])
def add_portfolio():
    portfolio_name = request.form.get('portfolioName', None)
    deposit = request.form.get('deposit', None)
    result = {
        'is_success': False,
        'message': ''
    }
    if portfolio_name is None:
        result['message'] = 'No porfolio name found'
        return jsonify(result)
    if deposit is None or not deposit.isnumeric():
        result['message'] = 'Cash funds is invalid or not found'
        return jsonify(result)
    try:
        db.insert_portfolio(portfolio_name, float(deposit))
        result['is_success'] = True
    except PortfolioAlreadyExistsException:
        result['is_success'] = False
        result['message'] = 'Portfolio already exists'
    return jsonify(result)

@app.route('/portfolio/delete', methods=['POST'])
def remove_portfolio():
    portfolio_name = request.form.get('portfolioName', None)
    result = {
        'is_success': False,
        'message': ''
    }
    if portfolio_name is None:
        result['message'] = 'No porfolio name found'
        return jsonify(result)
    delete_result = db.remove_portfolio(portfolio_name)
    if not delete_result:
        result['is_success'] = False
        result['message'] = 'Portfolio doesn\'t exists.'
    else:
        result['is_success'] = True
        result['message'] = f'Portfolio {portfolio_name} is successfully deleted'
    return jsonify(result)        
    
@app.route('/portfolio/names', methods=['GET'])
def get_portfolio_names():
    portfolio_names = db.get_portfolio_names()
    return jsonify(portfolio_names)

@app.route('/portfolio/funds/add', methods=['POST'])
def add_portfolio_funds():
    portfolio_name = request.form.get('portfolioName', None)
    to_deposit = request.form.get('deposit', None)
    result = {
        'is_success': True,
        'message': ''
    }
    if portfolio_name is None:
        result['is_success'] = False
        result['message'] = 'Portfolio is not set'
    if not to_deposit.isnumeric():
        result['is_success'] = False
        result['message'] = 'Must be a number'
    if to_deposit.isnumeric() and float(to_deposit) < 0.0:
        result['is_success'] = False
        result['message'] = 'Number must be greater than 0'

    is_portfolio_exists = db.is_portfolio_exists(portfolio_name)

    if not is_portfolio_exists:
        result['is_success'] = False
        result['message'] = f'Portfolio \'{portfolio_name}\' does not exists'
    if not result['is_success']:
        return jsonify(result)
    try:
        db.add_portfolio_funds(portfolio_name, float(to_deposit))
        result['message'] = 'Funds successfully added'
        return jsonify(result)
    except PortfolioNotFoundException:
        result['is_success'] = False
        result['message'] = f'Portfolio \'{portfolio_name}\' does not exists'
        return jsonify(result)

@app.route('/portfolio/funds/get', methods=['POST'])
def get_funds():
    portfolio_name = request.form.get('portfolioName', None)
    result = {
        'is_success': True,
        'message': ''
    }
    if portfolio_name is None:
        result['is_success'] = False
        result['message'] = 'Portfolio is not set'
        return jsonify(result)
    try:
        portfolio_data = db.get_portfolio_data(portfolio_name)
        result['sucess'] = True
        result['funds'] = portfolio_data['funds']
        return jsonify(result)
    except PortfolioNotFoundException:
        result['is_success'] = False
        result['message'] = f'Porfolio \'{portfolio_name}\' doesn not exists'

def get_stock_data(symbol: str, frequency):
    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-summary"

    querystring = {"symbol":symbol,"region":"US"}

    headers = {
        'x-rapidapi-host': "apidojo-yahoo-finance-v1.p.rapidapi.com",
        'x-rapidapi-key': "407e5459c5msh75afa459d43eacep19ce25jsnf4d86076258d"
        }

    response = requests.request("GET", url, headers=headers, params=querystring)
    if response.status_code >= 400:
        return None
    response = response.json()
    stock_data = {}
    stock_data['symbol'] = response['price']['symbol']
    stock_data['exchange'] = response['price']['exchangeName']
    stock_data['name'] = response['price']['longName']
    stock_data['price'] = response['price']['regularMarketPrice']['raw']
    stock_data['previous_price'] = response['price']['regularMarketPreviousClose']['raw']
    stock_data['is_high'] = True if stock_data['price'] > stock_data['previous_price'] else False
    stock_data['currency'] = response['summaryDetail']['currency']
    stock_data['dividend'] = response['summaryDetail']['dividendRate']['raw']
    stock_data['dividend_yield'] = "{0:.2%}".format(float(response['summaryDetail']['dividendYield']['raw']))
    stock_data['dividend_divided'] = get_frequency_data(stock_data['dividend'])[frequency]['dividend']
    stock_data['payment_date'] = response['calendarEvents']['dividendDate']['fmt']
    stock_data['exdividend_date'] = response['summaryDetail']['exDividendDate']['fmt']
    stock_data['beta'] = response['summaryDetail']['beta']['fmt']
    stock_data['pe_ratio'] = response['summaryDetail']['trailingPE']['fmt']
    stock_data['fifty_day_average'] = response['summaryDetail']['fiftyDayAverage']['fmt']
    stock_data['two_hundred_day_average'] = response['summaryDetail']['twoHundredDayAverage']['fmt']
    stock_data['fifty_two_week_range'] = f"{response['summaryDetail']['fiftyTwoWeekLow']['fmt']} - {response['summaryDetail']['fiftyTwoWeekHigh']['fmt']}"
    stock_data['payout_ratio'] = response['summaryDetail']['payoutRatio']['fmt']
    return stock_data

def get_frequency_data(dividend_rate: float):
    frequency = {
        'auto': {
            'repeat': 4,
            'dividend': dividend_rate / 4,
            'name': 'Quarter'
        },
        'quarterly': {
            'repeat': 4,
            'dividend': dividend_rate / 4,
            'name': 'Quarter'
        },
        'yearly': {
            'repeat': 12,
            'dividend': dividend_rate / 12,
            'name': 'Month'
        }
    }
    return frequency

def dividend_calculator(investment: float, funds: float, year_count:int, stock_data:dict, frequency:str, commission=9.99, drip=True):
    cash_available = investment - commission
    initial_share_brought = cash_available / stock_data['price']
    initial_share_brought_rounded = int(initial_share_brought)
    frequencies = get_frequency_data(stock_data['dividend'])
    years = {}
    for y in range(1, year_count + 1):
        years[y] = {}
        for q in range(1, frequencies[frequency]['repeat'] + 1):
            if y == 1 and q == 1:
                investment = round(stock_data['price'] * initial_share_brought_rounded, 2) + commission
                years[y][q] = {
                    'investment': investment,
                    'cash_balance_after_invest': round((initial_share_brought - int(initial_share_brought)) * stock_data['price'], 2),
                    'initial_share_brought': (initial_share_brought_rounded, ),
                    'average_cost': investment / initial_share_brought_rounded
                }
                continue
            elif y > 1 and q == 1:
                #drip_received = (math.floor(years[y-1][4]['total_drip'][1]) * stock_data['dividend']) / stock_data['price']
                drip_received = (years[y-1][4]['total_drip'][1] * frequencies[frequency]['dividend']) / stock_data['price']
                total_drip = (initial_share_brought_rounded, int(drip_received + math.floor(years[y-1][4]['total_drip'][1])))
                dividend_cash_received = (total_drip[0] * frequencies[frequency]['dividend'], (drip_received - int(drip_received)) * stock_data['price'])
                cash_received_drip = int(drip_received) * stock_data['price']
                without = dividend_cash_received[0] + years[y-1][4]['portfolio_cash'][0]
                withd = dividend_cash_received[1] + years[y-1][4]['portfolio_cash'][1] + cash_received_drip
                years[y][q] = {
                'drip_received': drip_received,
                'total_drip': total_drip,
                'dividend_cash_received': dividend_cash_received,
                'cash_received_drip': cash_received_drip,
                'portfolio_cash': (without, withd)
            }
                continue
            to_drip = initial_share_brought_rounded if y == 1 and q == 2 else years[y][q-1]['total_drip'][1]
            drip_received = (to_drip * frequencies[frequency]['dividend']) / stock_data['price']
            total_drip = (initial_share_brought_rounded, int(drip_received + to_drip))
            dividend_cash_received = (total_drip[0] * frequencies[frequency]['dividend'], (drip_received - math.floor(drip_received)) * stock_data['price'])
            cash_received_drip = int(drip_received) * stock_data['price']
            portfolio_wodrip = 0.0
            portfolio_wdrip = 0.0
            if q == 2 and y == 1:
                portfolio_wodrip = years[y][1]['investment'] + dividend_cash_received[0]
                portfolio_wdrip = years[y][1]['investment'] + dividend_cash_received[1] + cash_received_drip
            else:
                portfolio_wodrip = dividend_cash_received[0] + years[y][q-1]['portfolio_cash'][0]
                portfolio_wdrip = dividend_cash_received[1] + years[y][q-1]['portfolio_cash'][1] + cash_received_drip
            
            years[y][q] = {
                'drip_received': drip_received,
                'total_drip': total_drip,
                'dividend_cash_received': dividend_cash_received,
                'cash_received_drip': cash_received_drip,
                'portfolio_cash': (portfolio_wodrip, portfolio_wdrip)
            }
            
            if q == frequencies[frequency]['repeat']:
                total_cash_received_wodrip = sum([years[y][x]['dividend_cash_received'][0] for x in range(2, q + 1)])
                total_cash_received_wdrip = sum([years[y][x]['dividend_cash_received'][1] for x in range(2, q + 1)])
                #total_cash_received_wodrip = years[y][q]['dividend_cash_received'][0] + years[y][3]['dividend_cash_received'][0] + years[y][2]['dividend_cash_received'][0] 
                #total_cash_received_wdrip = years[y][q]['dividend_cash_received'][1] + years[y][3]['dividend_cash_received'][1] + years[y][2]['dividend_cash_received'][1]
                if y > 1:
                    total_cash_received_wodrip += years[y][1]['dividend_cash_received'][0] + years[y-1][q]['total_cash_received'][0]
                    total_cash_received_wdrip += years[y][1]['dividend_cash_received'][1] + years[y-1][q]['total_cash_received'][1]
                years[y][q]['total_cash_received'] = (total_cash_received_wodrip, total_cash_received_wdrip)
                portfolio_gain_loss = ((years[y][4]['portfolio_cash'][0] - years[1][1]['investment']) / years[1][1]['investment'], (years[y][q]['portfolio_cash'][1] - years[1][1]['investment']) / years[1][1]['investment'])
                years[y][q]['portfolio_gain_loss'] = ("{0:.2%}".format(portfolio_gain_loss[0]), "{0:.2%}".format(portfolio_gain_loss[1]))     
                quarter1 = 0 if y == 1 else int(years[y][1]['drip_received'])
                years[y][q]['total_drip_share'] = quarter1 + int(years[y][2]['drip_received']) + int(years[y][3]['drip_received']) + int(years[y][q]['drip_received'])

    return years    

def get_temp_stock_data():
    stock_data = {}
    stock_data['symbol'] = 'BNS.TO'
    stock_data['exchange'] = 'Toronto'
    stock_data['name'] = 'The Bank of Nova Scotia'
    stock_data['price'] = 82.56
    stock_data['previous_price'] = 81.98
    stock_data['is_high'] = True if stock_data['price'] > stock_data['previous_price'] else False
    stock_data['currency'] = 'CAD'
    stock_data['dividend'] = 3.60
    stock_data['dividend_yield'] = 0.04610
    stock_data['exdividend_date'] = '3-Oct-21'
    return stock_data

load_symbols()

if __name__ == "__main__":
    app.run(host='0.0.0.0')    
