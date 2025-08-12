import os
from flask import Flask
import yfinance as yf
import http.client, urllib
import psutil
import shutil

app = Flask(__name__)

@app.route('/')
def run_stock_tracker():
    try:
        # Disable yfinance cache
        os.environ["YFINANCE_NO_CACHE"] = "1"

        # --- Your stock portfolio classes and data ---

        class OwnedStock:
            def __init__(self, symbol, qty, priceBought, dateBought=None):
                self.symbol = symbol
                self.qty = qty
                self.priceBought = priceBought
                self.dateBought = dateBought

            def UnrealisedReturn(self, current_price):
                return (current_price - self.priceBought) * self.qty

        AllStocks = {}
        def AddStock(stock):
            if stock.symbol not in AllStocks:
                AllStocks[stock.symbol] = []
            AllStocks[stock.symbol].append(stock)

        # Add your stocks here
        AddStock(OwnedStock("AAPL", 6, 120.5))
        AddStock(OwnedStock("ASML", 1, 702))
        AddStock(OwnedStock("AMD", 2, 138.14))
        AddStock(OwnedStock("NVDA", 4.012, 122.26))
        AddStock(OwnedStock("WMT", 4.038, 91.6493313522))
        AddStock(OwnedStock("AMD", 2.898, 145.281716869))
        AddStock(OwnedStock("GOOGL", 2.06, 178.470873786))
        AddStock(OwnedStock("AAPL", 1.064, 232.462406015))
        AddStock(OwnedStock("AMZN", 0.854, 165.339578454))
        AddStock(OwnedStock("MSFT", 0.24, 416.666666667))
        AddStock(OwnedStock("ASML", 0.144, 685.416666667))

        # --- Download all stock data at once ---
        unique_symbols = list(AllStocks.keys())
        data = yf.download(unique_symbols, period="1d", group_by='ticker', progress=False, auto_adjust=False)

        symbol_prices = {}
        daily_changes = {}

        for symbol in unique_symbols:
            try:
                df = data[symbol]
                open_price = df['Open'].iloc[0]
                close_price = df['Close'].iloc[0]
                symbol_prices[symbol] = close_price
                daily_changes[symbol] = ((close_price - open_price) / open_price) * 100
            except Exception:
                continue

        total_unrealised = 0
        for symbol, stocks in AllStocks.items():
            current_price = symbol_prices.get(symbol)
            if current_price is None:
                continue
            for stock in stocks:
                total_unrealised += stock.UnrealisedReturn(current_price)

        if daily_changes:
            top_mover = max(daily_changes.items(), key=lambda x: abs(x[1]))
            mover_msg = f"{top_mover[0]} moved {top_mover[1]:.2f}% today"
        else:
            mover_msg = "Could not determine top mover."

        NotificationMessage = f"Total Unrealised Return: ${total_unrealised:.2f}\n{mover_msg}"

        # --- Send Notification (Pushover example) ---
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
          urllib.parse.urlencode({
            "token": "adn6izynevtqe2iu7yqg84g7teu5t5",  
            "user": "ugtxi8ez6skpf6vfe8i8bewkfm85rk",  
            "message": NotificationMessage,
          }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()

        # Return success message to browser
        return f"Stock tracker ran successfully! Notification sent.\n\n{NotificationMessage}"

    except Exception as e:
        return f"Error occurred: {str(e)}"

if __name__ == '__main__':
    app.run()
