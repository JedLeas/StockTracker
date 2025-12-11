import requests
import concurrent.futures
from datetime import datetime
from config import PUSHOVER_APP_TOKEN

def fetch_stock_price(symbol):
    if not symbol: return None, None
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {'interval': '1d', 'range': '1d'}
        response = requests.get(url, headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                if 'meta' in result:
                    current = result['meta'].get('regularMarketPrice')
                    prev = result['meta'].get('previousClose') or result['meta'].get('chartPreviousClose')
                    if not prev and 'indicators' in result and 'quote' in result['indicators']:
                        quotes = result['indicators']['quote'][0]
                        if 'close' in quotes and quotes['close'] and len(quotes['close']) >= 2:
                            prev = quotes['close'][-2]
                    if current:
                        return symbol, {'price': current, 'prev': prev}
    except Exception as e:
        print(f"Error price {symbol}: {e}")
    return symbol, None

def fetch_batch_prices(symbols):
    if not symbols: return {}
    price_map = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_symbol = {executor.submit(fetch_stock_price, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_to_symbol):
            try:
                sym, data = future.result()
                if data:
                    price_map[sym] = data
            except Exception as e:
                print(f"Thread error: {e}")
    return price_map

def fetch_stock_news_grouped(symbols):
    if not symbols: return {}
    news_map = {}
    headers = {'User-Agent': 'Mozilla/5.0'}
    def get_single_news(symbol):
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={symbol}&newsCount=3"
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                clean_news = []
                if 'news' in data:
                    for n in data['news']:
                        pub_time = n.get('providerPublishTime', 0)
                        clean_news.append({
                            'title': n.get('title'),
                            'link': n.get('link'),
                            'publisher': n.get('publisher'),
                            'time': datetime.fromtimestamp(pub_time).strftime('%Y-%m-%d')
                        })
                return symbol, clean_news
        except:
            return symbol, None
        return symbol, None
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(get_single_news, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                sym, news_items = future.result()
                if news_items:
                    news_map[sym] = news_items
            except:
                pass
    return news_map

def send_pushover(user_key, message):
    if not user_key: return False
    try:
        requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSHOVER_APP_TOKEN,
            "user": user_key,
            "message": message
        })
        return True
    except:
        return False