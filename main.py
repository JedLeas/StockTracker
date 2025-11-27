import os
import json
import time
import requests
import http.client
import urllib.parse
from flask import Flask, request, redirect, url_for, make_response

PushOver_API_Token = "PUSHOVERTOKENHEREFORAPP"
PushOver_User_Token = "PUSHOVERTOKENHEREFORUSER"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOLDINGS_FILE = os.path.join(BASE_DIR, "holdings.json")

app = Flask(__name__)

class OwnedStock:
    def __init__(self, symbol, qty, priceBought, dateBought=None):
        self.symbol = symbol
        self.qty = qty
        self.priceBought = priceBought
        self.dateBought = dateBought

    def UnrealisedReturn(self, current_price):
        return (current_price - self.priceBought) * self.qty

def load_holdings():
    if not os.path.exists(HOLDINGS_FILE):
        return []
    try:
        with open(HOLDINGS_FILE, "r") as f:
            data = json.load(f)
        return [OwnedStock(d["symbol"], d["qty"], d["priceBought"], d.get("dateBought")) for d in data]
    except Exception as e:
        print(f"Error reading holdings.json: {e}")
        return []

def save_holdings(holdings):
    try:
        data = []
        for h in holdings:
            if isinstance(h, OwnedStock):
                data.append({
                    "symbol": h.symbol,
                    "qty": h.qty,
                    "priceBought": h.priceBought,
                    "dateBought": h.dateBought
                })
            else:
                data.append(h)
        with open(HOLDINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving holdings.json: {e}")

@app.route('/')
def run_stock_tracker():
    try:
        os.environ["YFINANCE_NO_CACHE"] = "1"

        AllStocks = {}
        def AddStock(stock):
            if stock.symbol not in AllStocks:
                AllStocks[stock.symbol] = []
            AllStocks[stock.symbol].append(stock)

        holdings = load_holdings()
        if not holdings:
            return f"""
            <h1>No holdings found in JSON file.</h1>
            <p>Please add holdings first.</p>
            <a href="{url_for('manage_holdings')}"><button>Manage Holdings</button></a>
            """

        for stock in holdings:
            AddStock(stock)

        unique_symbols = list(AllStocks.keys())
        symbol_prices = {}
        daily_changes = {}

        def fetch_stock_price(symbol):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0'
                }
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                params = {'interval': '1d', 'range': '1d'}
                response = requests.get(url, headers=headers, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                        result = data['chart']['result'][0]
                        if 'meta' in result:
                            current_price = result['meta'].get('regularMarketPrice')
                            prev_close = result['meta'].get('previousClose') or result['meta'].get('chartPreviousClose')

                            if not prev_close and 'indicators' in result and 'quote' in result['indicators']:
                                quotes = result['indicators']['quote'][0]
                                if 'close' in quotes and quotes['close'] and len(quotes['close']) >= 2:
                                    prev_close = quotes['close'][-2]
                                elif 'open' in quotes and quotes['open'] and quotes['open'][0]:
                                    prev_close = quotes['open'][0]

                            if current_price and prev_close:
                                return current_price, prev_close
                return None, None
            except Exception as e:
                print(f"Error with Yahoo API for {symbol}: {str(e)}")
                return None, None

        for symbol in unique_symbols:
            max_retries = 2
            for attempt in range(max_retries):
                if attempt > 0:
                    time.sleep(1)
                current_price, prev_close = fetch_stock_price(symbol)
                if current_price is not None:
                    symbol_prices[symbol] = current_price
                    if prev_close and prev_close != 0:
                        daily_change = ((current_price - prev_close) / prev_close) * 100
                        daily_changes[symbol] = daily_change
                    break

        total_unrealised = 0
        total_value = 0
        stocks_with_data = 0
        for symbol, stocks in AllStocks.items():
            current_price = symbol_prices.get(symbol)
            if current_price is None:
                continue
            stocks_with_data += 1
            for stock in stocks:
                total_unrealised += stock.UnrealisedReturn(current_price)
                total_value += stock.qty*current_price

        if daily_changes:
            top_mover = max(daily_changes.items(), key=lambda x: abs(x[1]))
            mover_msg = f"{top_mover[0]} moved {top_mover[1]:.2f}% today"
        else:
            mover_msg = "Could not determine top mover."

        if stocks_with_data == 0:
            NotificationMessage = f"Unable to fetch stock data. Attempted symbols: {', '.join(unique_symbols)}"
        else:
            NotificationMessage = f"Total Unrealised Return: ${total_unrealised:.2f}\n{mover_msg}\nTotal Value: ${total_value:.2f}"

        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
            urllib.parse.urlencode({
                "token": PushOver_API_Token,
                "user": PushOver_User_Token,
                "message": NotificationMessage,
            }), {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()

        return f"""
        <h1>Stock tracker ran successfully!</h1>
        <p>{NotificationMessage}</p>
        <a href="{url_for('manage_holdings')}"><button>Manage Holdings</button></a>
        """

    except Exception as e:
        return f"Error occurred: {str(e)}"

@app.route('/holdings', methods=['GET', 'POST'])
def manage_holdings():
    PASSWORD = os.environ.get("HOLDINGS_PASSWORD", "changeme")
    authenticated = request.cookies.get("auth") == "true"
    message = ""

    if request.method == 'POST' and request.form.get("action") == "login":
        password = request.form.get("password")
        if password == PASSWORD:
            resp = make_response(redirect(url_for('manage_holdings')))
            resp.set_cookie("auth", "true", max_age=3600)
            return resp
        else:
            message = "Incorrect password."

    if request.method == 'POST' and request.form.get("action") == "logout":
        resp = make_response(redirect(url_for('manage_holdings')))
        resp.set_cookie("auth", "false", max_age=0)
        return resp

    holdings = load_holdings()

    if authenticated and request.method == 'POST' and request.form.get("action") in ["buy", "sell"]:
        action = request.form.get('action')
        symbol = request.form.get('symbol').upper()
        qty = float(request.form.get('qty'))
        priceBought = float(request.form.get('priceBought') or 0)

        existing = next((h for h in holdings if h.symbol == symbol), None)

        if action == "buy":
            if existing:
                new_qty = existing.qty + qty
                new_avg_price = ((existing.qty * existing.priceBought) + (qty * priceBought)) / new_qty
                existing.qty = new_qty
                existing.priceBought = new_avg_price
            else:
                holdings.append(OwnedStock(symbol, qty, priceBought))
            message = f"Bought {qty} of {symbol}."

        elif action == "sell":
            if existing:
                if qty > existing.qty:
                    message = f"Error: You only own {existing.qty} of {symbol}."
                elif qty == existing.qty:
                    holdings = [h for h in holdings if h.symbol != symbol]
                    message = f"Sold all holdings of {symbol}."
                else:
                    existing.qty -= qty
                    message = f"Sold {qty} of {symbol}."
            else:
                message = f"Error: You don't own any {symbol}."

        save_holdings(holdings)
        return redirect(url_for('manage_holdings'))

    def fetch_stock_price(symbol):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {'interval': '1d', 'range': '1d'}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                    result = data['chart']['result'][0]
                    if 'meta' in result:
                        return result['meta'].get('regularMarketPrice')
        except:
            return None
        return None

    total_unrealised = 0
    total_value = 0
    total_cost_basis = 0

    table_rows = ""
    for h in holdings:
        current_price = fetch_stock_price(h.symbol)
        if current_price is None:
            unrealised = 0
            total_val = 0
            pct_change = 0
        else:
            unrealised = (current_price - h.priceBought) * h.qty
            total_val = current_price * h.qty
            pct_change = ((current_price - h.priceBought) / h.priceBought) * 100

            total_unrealised += unrealised
            total_value += total_val
            total_cost_basis += h.priceBought * h.qty

        table_rows += f"""
        <tr>
            <td>{h.symbol}</td>
            <td>{h.qty:.4f}</td>
            <td>${h.priceBought:.2f}</td>
            <td>{'N/A' if current_price is None else f'${current_price:.2f}'}</td>
            <td>{'N/A' if current_price is None else f'${unrealised:.2f}'}</td>
            <td>{'N/A' if current_price is None else f'${total_val:.2f}'}</td>
            <td>{'N/A' if current_price is None else f'{pct_change:.2f}%'}</td>
        </tr>
        """

    total_pct = ((total_value - total_cost_basis) / total_cost_basis) * 100 if total_cost_basis > 0 else 0

    html = f"""
    <h1>Manage Stock Holdings</h1>
    <p style="color:green;">{message}</p>

    <table border="1" cellpadding="5">
        <tr>
            <th>Symbol</th>
            <th>Quantity</th>
            <th>Price Bought</th>
            <th>Current Price</th>
            <th>Unrealised Return</th>
            <th>Total Value</th>
            <th>Change %</th>
        </tr>
        {table_rows}
    </table>

    <h3>Totals</h3>
    <p>Total Unrealised Return: ${total_unrealised:.2f}</p>
    <p>Total Value: ${total_value:.2f}</p>
    <p>Total Change: {total_pct:.2f}%</p>
    """

    if authenticated:
        html += """
        <h2>Buy Stock</h2>
        <form method="POST">
            <input type="hidden" name="action" value="buy">
            Symbol: <input name="symbol" required><br>
            Quantity: <input name="qty" type="number" step="0.0001" required><br>
            Price Bought: <input name="priceBought" type="number" step="0.01" required><br>
            <button type="submit">Buy</button>
        </form>

        <h2>Sell Stock</h2>
        <form method="POST">
            <input type="hidden" name="action" value="sell">
            Symbol: <input name="symbol" required><br>
            Quantity: <input name="qty" type="number" step="0.0001" required><br>
            <button type="submit">Sell</button>
        </form>

        <form method="POST">
            <input type="hidden" name="action" value="logout">
            <button type="submit">Logout</button>
        </form>
        """
    else:
        html += f"""
        <p style="color:red;">{message}</p>
        <form method="POST">
            <input type="hidden" name="action" value="login">
            Password: <input name="password" type="password" required>
            <button type="submit">Unlock Buy/Sell</button>
        </form>
        """

    html += f'<br><a href="{url_for("run_stock_tracker")}"><button>Back to Tracker</button></a>'

    return html


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
