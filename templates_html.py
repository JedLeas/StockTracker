BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockTracker</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #f0f2f5; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .navbar { background: #1a1a1a; box-shadow: 0 2px 10px rgba(0,0,0,0.3); }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: transform 0.2s; }
        .card:hover { transform: translateY(-2px); }
        .text-profit { color: #10b981 !important; font-weight: 700; }
        .text-loss { color: #ef4444 !important; font-weight: 700; }
        .metric-label { color: #6b7280; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
        .metric-value { font-size: 1.75rem; font-weight: 700; }
        .badge-buy { background-color: #10b981; color: white; }
        .badge-sell { background-color: #ef4444; color: white; }
        .badge-hold { background-color: #f59e0b; color: white; }
        .badge-na { background-color: #9ca3af; color: white; }
        .news-link { text-decoration: none; color: #1f2937; font-weight: 600; }
        .news-link:hover { color: #2563eb; }
        .stock-header { border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-bottom: 15px; }

        .auth-card { max-width: 450px; margin: 80px auto; padding: 40px; }
        .auth-header { text-align: center; margin-bottom: 30px; }
        .form-control { padding: 12px; border-radius: 8px; }
        .btn-lg-custom { padding: 12px; border-radius: 8px; font-weight: 600; font-size: 1.1rem; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark mb-4">
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">Stock<span style="color:#10b981">Tracker</span></a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                {% if session.get('user') %}
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('dashboard') }}">Dashboard</a></li>
                    <li class="nav-item"><a class="nav-link text-info" href="{{ url_for('settings') }}">Settings</a></li>
                    <li class="nav-item"><a class="nav-link text-warning" href="{{ url_for('logout') }}">Logout</a></li>
                </ul>
                {% endif %}
            </div>
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for c, m in messages %}<div class="alert alert-{{ c }} shadow-sm">{{ m }}</div>{% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

LOGIN_PAGE = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
<div class="card auth-card shadow-lg">
    <div class="auth-header">
        <h2 class="fw-bold text-dark">Welcome Back</h2>
        <p class="text-muted">Login to manage your portfolio</p>
    </div>
    <form method="POST" action="{{ url_for('login') }}">
        <div class="mb-3"><label class="form-label fw-bold text-secondary">Username</label><input name="username" class="form-control" required></div>
        <div class="mb-4"><label class="form-label fw-bold text-secondary">Password</label><input name="password" type="password" class="form-control" required></div>
        <button class="btn btn-primary w-100 btn-lg-custom">Login</button>
    </form>
    <div class="text-center mt-4"><span class="text-muted">Don't have an account?</span><a href="{{ url_for('register') }}" class="fw-bold text-decoration-none ms-1">Create Account</a></div>
</div>
""")

REGISTER_PAGE = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
<div class="card auth-card shadow-lg">
    <div class="auth-header">
        <h2 class="fw-bold text-dark">Create Account</h2>
        <p class="text-muted">Start tracking your wealth today</p>
    </div>
    <form method="POST" action="{{ url_for('register') }}">
        <div class="mb-3"><label class="form-label fw-bold text-secondary">Username</label><input name="username" class="form-control" pattern="[a-zA-Z0-9]+" required></div>
        <div class="mb-3"><label class="form-label fw-bold text-secondary">Password</label><input name="password" type="password" class="form-control" required></div>
        <hr class="my-4">
        <div class="mb-4"><label class="form-label fw-bold text-secondary">PushOver User Key <span class="text-muted fw-normal">(Optional)</span></label><input name="po_user" class="form-control" placeholder="Found on your PushOver dashboard"></div>
        <button class="btn btn-success w-100 btn-lg-custom">Sign Up</button>
    </form>
    <div class="text-center mt-4"><span class="text-muted">Already have an account?</span><a href="{{ url_for('login') }}" class="fw-bold text-decoration-none ms-1">Login here</a></div>
</div>
""")

SETTINGS_PAGE = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
<div class="card p-5 mx-auto shadow-lg" style="max-width:600px">
    <h3 class="mb-4">User Settings</h3>
    <form method="POST">
        <div class="mb-3"><label class="form-label fw-bold">PushOver User Key</label><input name="po_user" class="form-control" value="{{ user.po_user or '' }}"></div>
        <hr class="my-4">
        <h5 class="mb-3">Notification Frequency</h5>
        <div class="mb-4">
            <select name="notify_freq" class="form-select">
                <option value="none" {% if user.notify_freq == 'none' %}selected{% endif %}>None (Manual Only)</option>
                <option value="open" {% if user.notify_freq == 'open' %}selected{% endif %}>1 at Market Open (9:30 AM ET)</option>
                <option value="open_close" {% if user.notify_freq == 'open_close' %}selected{% endif %}>Open & Close (9:30 AM & 4:00 PM ET)</option>
                <option value="hourly" {% if user.notify_freq == 'hourly' %}selected{% endif %}>Hourly (While Market is Open)</option>
                <option value="2hours" {% if user.notify_freq == '2hours' %}selected{% endif %}>Every 2 Hours (While Market is Open)</option>
            </select>
        </div>
        <button type="submit" class="btn btn-primary w-100 py-2 fw-bold">Save Changes</button>
    </form>
    <div class="mt-4 d-flex gap-2">
        <form action="{{ url_for('test_notification') }}" method="POST" class="flex-grow-1"><button class="btn btn-warning w-100">Send Test Notification</button></form>
        <a href="{{ url_for('export_data') }}" class="btn btn-secondary flex-grow-1 text-center text-decoration-none lh-lg">Export Data (CSV)</a>
    </div>
    <hr class="my-4">
    <div class="p-3 bg-light border rounded">
        <h5 class="text-danger">Danger Zone</h5>
        <p class="text-muted small mb-2"><strong>Wipe Portfolio:</strong> Clears all stocks and history, but keeps your account.</p>
        <button class="btn btn-outline-warning w-100 mb-3" data-bs-toggle="modal" data-bs-target="#wipeModal">Wipe All Data</button>
        <p class="text-muted small mb-2"><strong>Delete Account:</strong> Permanently deletes everything.</p>
        <button class="btn btn-outline-danger w-100" data-bs-toggle="modal" data-bs-target="#deleteModal">Delete My Account</button>
    </div>
</div>

<div class="modal fade" id="wipeModal" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><div class="modal-header bg-warning text-dark"><h5 class="modal-title">Confirm Wipe</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body"><p>Are you sure you want to <strong>wipe all holdings and history</strong>?</p></div><div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><form action="{{ url_for('wipe_portfolio') }}" method="POST"><button type="submit" class="btn btn-warning">Yes, Wipe Data</button></form></div></div></div></div>
<div class="modal fade" id="deleteModal" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><div class="modal-header bg-danger text-white"><h5 class="modal-title">Confirm Account Deletion</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body">Are you absolutely sure? This action cannot be undone.</div><div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button><form action="{{ url_for('delete_account') }}" method="POST"><button type="submit" class="btn btn-danger">Yes, Delete Everything</button></form></div></div></div></div>
""")

DASHBOARD_PAGE = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
<h5 class="mb-3 text-secondary">Today's Performance</h5>
<div class="row mb-4 text-center">
    <div class="col-md-12">
        <div class="card p-3 border-start border-4 {{ 'border-success' if totals.daily_val >= 0 else 'border-danger' }}">
            <div class="d-flex justify-content-between align-items-center px-4">
                <div>
                    <div class="metric-label">Today's Change ($)</div>
                    <div class="metric-value {{ 'text-profit' if totals.daily_val >= 0 else 'text-loss' }}">
                        ${{ "{:,.2f}".format(totals.daily_val) }}
                    </div>
                </div>
                <div>
                    <div class="metric-label">Today's Change (%)</div>
                    <div class="metric-value {{ 'text-profit' if totals.daily_pct >= 0 else 'text-loss' }}">
                        {{ "{:,.2f}".format(totals.daily_pct) }}%
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<h5 class="mb-3 text-secondary">Current Portfolio</h5>
<div class="row mb-4 text-center">
    <div class="col-md-4 mb-3"><div class="card p-4 h-100 border-start border-4 border-dark"><div class="metric-label">Portfolio Value</div><div class="metric-value text-dark">${{ "{:,.2f}".format(totals.value) }}</div></div></div>
    <div class="col-md-4 mb-3"><div class="card p-4 h-100 border-start border-4 {{ 'border-success' if totals.unrealised >= 0 else 'border-danger' }}"><div class="metric-label">Unrealized P/L ($)</div><div class="metric-value {{ 'text-profit' if totals.unrealised >= 0 else 'text-loss' }}">${{ "{:,.2f}".format(totals.unrealised) }}</div></div></div>
    <div class="col-md-4 mb-3"><div class="card p-4 h-100 border-start border-4 {{ 'border-success' if totals.pct >= 0 else 'border-danger' }}"><div class="metric-label">Unrealized Growth (%)</div><div class="metric-value {{ 'text-profit' if totals.pct >= 0 else 'text-loss' }}">{{ "{:,.2f}".format(totals.pct) }}%</div></div></div>
</div>

<div class="row mb-4">
    <div class="col-md-4 mb-3">
        <div class="card p-3 h-100 d-flex align-items-center justify-content-center">
            <h6 class="text-muted mb-3">Asset Allocation</h6>
            <div style="width: 100%; min-height: {{ 300 + (holdings|length * 25) }}px; position: relative;">
                <canvas id="portfolioChart"></canvas>
            </div>
        </div>
    </div>

    <div class="col-md-8 mb-3">
        <div class="card p-4 h-100 shadow-sm">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4 class="mb-0">Holdings</h4>
                <button class="btn btn-primary fw-bold px-4" data-bs-toggle="modal" data-bs-target="#buyModal">+ Add Stock</button>
            </div>
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead class="table-light"><tr><th>Symbol</th><th>Qty</th><th>Avg Cost</th><th>Price</th><th>Value</th><th>Return</th><th>Action</th></tr></thead>
                    <tbody>
                        {% for s in holdings %}
                        <tr>
                            <td class="fw-bold">{{ s.symbol }}</td>
                            <td>{{ "{:,.4f}".format(s.qty) }}</td>
                            <td>${{ "{:,.2f}".format(s.priceBought) }}</td>
                            <td>{{ "${:,.2f}".format(s.current_price) if s.current_price else '...' }}</td>
                            <td class="fw-bold">{{ "${:,.2f}".format(s.total_value) if s.total_value else '-' }}</td>
                            <td class="{{ 'text-profit' if s.unrealised is not none and s.unrealised >= 0 else 'text-loss' }}">{{ "{:,.2f}%".format(s.pct_change) if s.pct_change is not none else '-' }}</td>
                            <td><button class="btn btn-sm btn-outline-danger" onclick="openSell('{{ s.symbol }}', {{ s.qty }}, {{ s.current_price or 0 }})">Sell</button></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<h5 class="mb-3 text-secondary">Total Performance (Lifetime)</h5>
<div class="row mb-5 text-center">
    <div class="col-md-3 mb-3"><div class="card p-4 h-100 border-start border-4 {{ 'border-success' if totals.growth >= 0 else 'border-danger' }}"><div class="metric-label">Total Growth ($)</div><div class="metric-value {{ 'text-profit' if totals.growth >= 0 else 'text-loss' }}">${{ "{:,.2f}".format(totals.growth) }}</div></div></div>
    <div class="col-md-3 mb-3"><div class="card p-4 h-100 border-start border-4 {{ 'border-success' if totals.realized >= 0 else 'border-danger' }}"><div class="metric-label">Realized Profit</div><div class="metric-value {{ 'text-profit' if totals.realized >= 0 else 'text-loss' }}">${{ "{:,.2f}".format(totals.realized) }}</div></div></div>

    <div class="col-md-3 mb-3">
        <div class="card p-4 h-100 border-start border-4 border-info">
            <div class="metric-label">Trader Win Rate</div>
            <div class="metric-value text-primary">{{ "{:,.0f}".format(totals.win_rate) }}%</div>
            <div class="small text-muted">{{ totals.total_trades }} closed trades</div>
        </div>
    </div>

    <div class="col-md-3 mb-3"><div class="card p-4 h-100 border-start border-4 {{ 'border-success' if totals.growth_pct >= 0 else 'border-danger' }}"><div class="metric-label">Total Growth (%)</div><div class="metric-value {{ 'text-profit' if totals.growth_pct >= 0 else 'text-loss' }}">{{ "{:,.2f}".format(totals.growth_pct) }}%</div></div></div>
</div>

<div class="row">
    <div class="col-md-7 mb-4">
        <div class="card p-4 h-100">
            <h5 class="mb-4">Recent News by Holding</h5>
            {% if news %}
                <div style="max-height: 500px; overflow-y: auto; padding-right:10px;">
                {% for symbol, articles in news.items() %}
                    <div class="stock-header"><h6 class="fw-bold text-primary">{{ symbol }}</h6></div>
                    <ul class="list-group list-group-flush mb-4">
                    {% for n in articles %}
                        <li class="list-group-item px-0 border-0 pb-3">
                            <a href="{{ n.link }}" target="_blank" class="news-link">{{ n.title }}</a>
                            <div class="small text-muted mt-1 d-flex justify-content-between"><span>{{ n.publisher }}</span><span>{{ n.time }}</span></div>
                        </li>
                    {% endfor %}
                    </ul>
                {% endfor %}
                </div>
            {% else %}
                <p class="text-muted">No news articles found for your holdings right now.</p>
            {% endif %}
        </div>
    </div>

    <div class="col-md-5 mb-4">
        <div class="card p-4 h-100">
            <h5 class="mb-3">Transaction History</h5>
            <div style="max-height: 500px; overflow-y: auto;">
                <table class="table table-sm table-striped">
                    <thead><tr><th>Date</th><th>Type</th><th>Sym</th><th>Price</th><th>P/L</th></tr></thead>
                    <tbody>
                        {% for r in history|reverse %}
                        <tr>
                            <td>{{ r.date.split(' ')[0] }}</td>
                            <td><span class="badge {{ 'bg-success' if r.type=='SELL' else 'bg-primary' }}">{{ r.type }}</span></td>
                            <td class="fw-bold">{{ r.symbol }}</td>
                            <td>${{ "{:,.2f}".format(r.price) }}</td>
                            <td class="{{ 'text-profit' if r.realized_gain and r.realized_gain>=0 else 'text-loss' }}">
                                {{ "${:,.0f}".format(r.realized_gain) if r.realized_gain is not none else '-' }}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<div class="modal fade" id="buyModal" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><form method="POST" action="{{ url_for('trade') }}"><div class="modal-body"><input type="hidden" name="action" value="buy"><div class="mb-3"><label>Symbol</label><input name="symbol" class="form-control" required style="text-transform:uppercase"></div><div class="mb-3"><label>Qty</label><input name="qty" type="number" step="any" min="0.0001" class="form-control" required></div><div class="mb-3"><label>Price</label><input name="price" type="number" step="any" min="0.01" class="form-control" required></div></div><div class="modal-footer"><button class="btn btn-primary">Buy</button></div></form></div></div></div>
<div class="modal fade" id="sellModal" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><form method="POST" action="{{ url_for('trade') }}"><div class="modal-body"><input type="hidden" name="action" value="sell"><div class="mb-3"><label>Symbol</label><input name="symbol" id="sellSym" class="form-control" readonly></div><div class="mb-3"><label>Qty</label><input name="qty" id="sellQty" type="number" step="any" min="0.0001" class="form-control" required></div><div class="mb-3"><label>Price</label><input name="price" id="sellPrice" type="number" step="any" min="0.01" class="form-control" required></div></div><div class="modal-footer"><button class="btn btn-danger">Sell</button></div></form></div></div></div>

<script>
function openSell(s,q,p){document.getElementById('sellSym').value=s;document.getElementById('sellQty').value=q;if(p>0)document.getElementById('sellPrice').value=p;new bootstrap.Modal(document.getElementById('sellModal')).show();}

document.addEventListener("DOMContentLoaded", function() {
    var ctx = document.getElementById('portfolioChart').getContext('2d');
    var chartLabels = {{ chart_labels|tojson }};
    var chartData = {{ chart_data|tojson }};

    if(chartData.length === 0) {
        chartLabels = ["No Data"];
        chartData = [100];
        var bgColors = ['#e5e7eb'];
    } else {
        var bgColors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#6366f1', '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16', '#d946ef', '#64748b', '#a855f7', '#fbbf24'];
    }

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: chartLabels,
            datasets: [{
                data: chartData,
                backgroundColor: bgColors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
});
</script>
""")