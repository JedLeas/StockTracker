import os
import io
import csv
from flask import render_template_string, redirect, url_for, request, session, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import MARKET_OPEN, MARKET_CLOSE, US_EASTERN, CRON_SECRET
from models import load_users, save_users, get_safe_filename, load_json, save_json
from utils import fetch_stock_price, fetch_batch_prices, fetch_stock_news_grouped, send_pushover
from templates_html import LOGIN_PAGE, REGISTER_PAGE, DASHBOARD_PAGE, SETTINGS_PAGE


def register_routes(app):
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )

    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user' not in session: return redirect(url_for('login'))
            return f(*args, **kwargs)

        return decorated

    @app.route('/')
    def root():
        return redirect(url_for('dashboard')) if 'user' in session else redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("5 per minute")
    def login():
        if request.method == 'POST':
            users = load_users()
            u = users.get(request.form.get('username'))
            if u and check_password_hash(u['hash'], request.form.get('password')):
                session['user'] = request.form.get('username')
                return redirect(url_for('dashboard'))
            flash("Invalid credentials", "danger")
        return render_template_string(LOGIN_PAGE)

    @app.route('/register', methods=['GET', 'POST'])
    @limiter.limit("10 per hour")
    def register():
        if request.method == 'POST':
            n = request.form.get('username')
            users = load_users()
            if n not in users:
                users[n] = {'hash': generate_password_hash(request.form.get('password')),
                            'po_user': request.form.get('po_user'), 'notify_freq': 'none'}
                save_users(users)
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        return render_template_string(REGISTER_PAGE)

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        h = load_json(get_safe_filename(session['user'], 'holdings'))
        hist = load_json(get_safe_filename(session['user'], 'history'))

        sell_txns = [t for t in hist if t.get('type') == 'SELL']
        total_sells = len(sell_txns)
        wins = len([t for t in sell_txns if t.get('realized_gain', 0) > 0])
        win_rate = (wins / total_sells * 100) if total_sells > 0 else 0

        total_realized = sum(txn.get('realized_gain', 0) or 0 for txn in hist if txn.get('realized_gain') is not None)
        total_realized_cost_basis = sum(
            txn.get('price', 0) * txn.get('qty', 0) for txn in hist if txn.get('type') == 'SELL')

        tv, tc, tu = 0, 0, 0
        daily_dollar_change = 0
        previous_portfolio_val = 0

        proc = []

        symbols = list(set([s['symbol'] for s in h]))

        price_map = fetch_batch_prices(symbols)

        chart_labels = []
        chart_data = []

        for s in h:
            data = price_map.get(s['symbol'])

            if data:
                curr = data['price']
                prev = data['prev']
                s['current_price'] = curr

                val = curr * s['qty']
                cost_basis = s['priceBought'] * s['qty']
                unr = val - cost_basis

                if prev:
                    day_gain = (curr - prev) * s['qty']
                    daily_dollar_change += day_gain
                    previous_portfolio_val += (prev * s['qty'])

                s['total_value'] = val
                s['unrealised'] = unr
                s['pct_change'] = ((curr - s['priceBought']) / s['priceBought']) * 100

                tv += val
                tc += cost_basis
                tu += unr

                chart_labels.append(s['symbol'])
                chart_data.append(round(val, 2))
            else:
                s['current_price'] = None
                s['total_value'] = s['unrealised'] = s['pct_change'] = None

            proc.append(s)

        total_growth = total_realized + tu
        lifetime_cost_basis = tc + total_realized_cost_basis
        total_growth_pct = (total_growth / lifetime_cost_basis * 100) if lifetime_cost_basis > 0 else 0
        daily_pct = (daily_dollar_change / previous_portfolio_val * 100) if previous_portfolio_val > 0 else 0

        totals = {
            'value': tv,
            'unrealised': tu,
            'pct': ((tv - tc) / tc * 100) if tc > 0 else 0,
            'realized': total_realized,
            'growth': total_growth,
            'growth_pct': total_growth_pct,
            'daily_val': daily_dollar_change,
            'daily_pct': daily_pct,
            'win_rate': win_rate,
            'total_trades': total_sells
        }

        sorted_holdings = sorted(proc, key=lambda x: (x.get('total_value') or 0), reverse=True)
        
        news = fetch_stock_news_grouped(symbols)

        return render_template_string(DASHBOARD_PAGE, holdings=sorted_holdings, history=hist, totals=totals, news=news,
                                      chart_labels=chart_labels, chart_data=chart_data)

    @app.route('/trade', methods=['POST'])
    @login_required
    def trade():
        n = session['user']
        act = request.form.get('action')
        sym = request.form.get('symbol', '').upper().strip()

        try:
            qty = float(request.form.get('qty'))
            price = float(request.form.get('price'))
            if qty <= 0 or price < 0: raise ValueError
        except:
            flash("Invalid input numbers.", "danger")
            return redirect(url_for('dashboard'))

        h_f, hist_f = get_safe_filename(n, 'holdings'), get_safe_filename(n, 'history')
        h, hist = load_json(h_f), load_json(hist_f)
        idx = next((i for i, x in enumerate(h) if x['symbol'] == sym), -1)

        if act == 'buy':
            if idx == -1:
                _, data = fetch_stock_price(sym)
                if not data:
                    flash("Ticker verification failed. Stock not found.", "danger")
                    return redirect(url_for('dashboard'))

            if idx >= 0:
                old = h[idx]
                new_qty = old['qty'] + qty
                h[idx]['priceBought'] = ((old['qty'] * old['priceBought']) + (qty * price)) / new_qty
                h[idx]['qty'] = new_qty
            else:
                h.append({'symbol': sym, 'qty': qty, 'priceBought': price})
            hist.append({'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'type': 'BUY', 'symbol': sym, 'qty': qty,
                         'price': price, 'realized_gain': None})

        elif act == 'sell':
            if idx >= 0 and h[idx]['qty'] >= qty:
                gain = (price - h[idx]['priceBought']) * qty
                h[idx]['qty'] -= qty
                if h[idx]['qty'] <= 1e-6: h.pop(idx)
                hist.append(
                    {'date': datetime.now().strftime("%Y-%m-%d %H:%M"), 'type': 'SELL', 'symbol': sym, 'qty': qty,
                     'price': price, 'realized_gain': gain})
            else:
                flash("Insufficient quantity.", "danger")

        save_json(h_f, h);
        save_json(hist_f, hist)
        return redirect(url_for('dashboard'))

    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        n = session['user']
        users = load_users()
        if request.method == 'POST':
            users[n]['po_user'] = request.form.get('po_user')
            users[n]['notify_freq'] = request.form.get('notify_freq')
            save_users(users)
            flash("Saved", "success")
        return render_template_string(SETTINGS_PAGE, user=users[n])

    @app.route('/export_data')
    @login_required
    def export_data():
        n = session['user']
        holdings = load_json(get_safe_filename(n, 'holdings'))
        history = load_json(get_safe_filename(n, 'history'))
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(["--- CURRENT HOLDINGS ---"])
        cw.writerow(["Symbol", "Qty", "Avg Price"])
        for x in holdings: cw.writerow([x['symbol'], x['qty'], x['priceBought']])
        cw.writerow([])
        cw.writerow(["--- TRANSACTION HISTORY ---"])
        cw.writerow(["Date", "Type", "Symbol", "Qty", "Price", "Realized Gain"])
        for x in history: cw.writerow(
            [x['date'], x['type'], x['symbol'], x['qty'], x['price'], x.get('realized_gain', '-')])
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename=stock_data_{n}.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    @app.route('/wipe_portfolio', methods=['POST'])
    @login_required
    def wipe_portfolio():
        n = session['user']
        try:
            save_json(get_safe_filename(n, 'holdings'), [])
            save_json(get_safe_filename(n, 'history'), [])
            flash("All holdings and history wiped.", "warning")
        except Exception as e:
            flash(f"Error wiping: {e}", "danger")
        return redirect(url_for('settings'))

    @app.route('/delete_account', methods=['POST'])
    @login_required
    def delete_account():
        n = session['user']
        try:
            h_f, hist_f = get_safe_filename(n, 'holdings'), get_safe_filename(n, 'history')
            if os.path.exists(h_f): os.remove(h_f)
            if os.path.exists(hist_f): os.remove(hist_f)
        except:
            pass
        users = load_users()
        if n in users: del users[n]; save_users(users)
        session.clear()
        flash("Account deleted.", "info")
        return redirect(url_for('login'))

    @app.route('/test_notification', methods=['POST'])
    @login_required
    def test_notification():
        users = load_users()
        u = users[session['user']]
        if send_pushover(u.get('po_user'), "Test Notification Success"):
            flash("Sent!", "success")
        else:
            flash("Failed", "danger")
        return redirect(url_for('settings'))

    @app.route('/cron/trigger')
    def cron_trigger():
        if request.args.get("secret") != CRON_SECRET:
            return "Unauthorized", 401
            
        now_et = datetime.now(US_EASTERN)
        current_time = now_et.time()

        def is_time_match(th, tm):
            nm = current_time.hour * 60 + current_time.minute
            tm_mins = th * 60 + tm
            return tm_mins <= nm < (tm_mins + 30)

        is_open = MARKET_OPEN <= current_time <= MARKET_CLOSE

        users = load_users()
        sent = 0
        for u, d in users.items():
            freq = d.get('notify_freq', 'none')
            if freq == 'none': continue
            do_send = False
            if freq == 'open' and is_time_match(9, 30):
                do_send = True
            elif freq == 'open_close' and (is_time_match(9, 30) or is_time_match(15, 30)):
                do_send = True
            elif freq == 'hourly' and is_open and current_time.minute < 30:
                do_send = True
            elif freq == '2hours' and is_open and (current_time.hour % 2 != 0) and current_time.minute < 30:
                do_send = True

            if do_send:
                holdings = load_json(get_safe_filename(u, 'holdings'))
                if not holdings: continue

                symbols = [h['symbol'] for h in holdings]
                price_map = fetch_batch_prices(symbols)

                tv, tu = 0, 0
                daily_moves = {}
                for h in holdings:
                    data = price_map.get(h['symbol'])
                    if data:
                        c = data['price']
                        prev = data['prev']
                        tv += c * h['qty']
                        tu += (c - h['priceBought']) * h['qty']
                        if prev:
                            daily_moves[h['symbol']] = ((c - prev) / prev) * 100

                mover = f"{max(daily_moves, key=lambda k: abs(daily_moves[k]))} {daily_moves[max(daily_moves, key=lambda k: abs(daily_moves[k]))]:.2f}%" if daily_moves else "N/A"
                if send_pushover(d.get('po_user'), f"Update: Val ${tv:,.0f} | P/L ${tu:,.0f} | Top: {mover}"): sent += 1
        return f"Processed {sent}"