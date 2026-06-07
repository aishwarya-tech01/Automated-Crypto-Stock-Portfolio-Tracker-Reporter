import os
import sqlite3
import threading
import time
from datetime import datetime
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'super_secret_crypto_portfolio_key'
DATABASE = 'portfolio.db'

# ---- 1. DATABASE MANAGEMENT SETUP ----
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables and inserts starting assets for immediate testing."""
    conn = get_db_connection()
    
    # User's Portfolio Assets Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS investments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT NOT NULL,       -- e.g., 'bitcoin', 'ethereum'
            asset_name TEXT NOT NULL,     -- e.g., 'Bitcoin', 'Ethereum'
            buy_price REAL NOT NULL,      -- Price per coin when purchased
            quantity REAL NOT NULL        -- Number of coins owned
        )
    ''')
    
    # Real-Time Price Caching Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS market_cache (
            asset_id TEXT PRIMARY KEY,
            current_price REAL NOT NULL,
            last_updated TIMESTAMP
        )
    ''')
    
    # Injects standard benchmark crypto rows if the table is brand new
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM investments")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO investments (asset_id, asset_name, buy_price, quantity) VALUES ('bitcoin', 'Bitcoin', 62000.0, 0.5)")
        cursor.execute("INSERT INTO investments (asset_id, asset_name, buy_price, quantity) VALUES ('ethereum', 'Ethereum', 3100.0, 2.5)")
        cursor.execute("INSERT INTO investments (asset_id, asset_name, buy_price, quantity) VALUES ('solana', 'Solana', 140.0, 10.0)")
        
        # Populate initial cache baselines
        cursor.execute("INSERT OR IGNORE INTO market_cache (asset_id, current_price) VALUES ('bitcoin', 65000.0)")
        cursor.execute("INSERT OR IGNORE INTO market_cache (asset_id, current_price) VALUES ('ethereum', 3300.0)")
        cursor.execute("INSERT OR IGNORE INTO market_cache (asset_id, current_price) VALUES ('solana', 150.0)")
        
    conn.commit()
    conn.close()


# ---- 2. REAL-TIME BACKGROUND ENGINE WORKER ----
def fetch_live_market_prices():
    """
    Independent background worker thread microservice.
    Wakes up every 60 seconds, fetches live market rates from the public CoinGecko REST API,
    and updates the database cache without interrupting the user.
    """
    print("🚀 Real-Time Market API Engine Thread Started Successfully!")
    while True:
        try:
            target_assets = ['bitcoin', 'ethereum', 'solana']
            assets_str = ",".join(target_assets)
            
            # Consuming the live public external REST API feed
            api_url = f"https://api.coingecko.com/api/v3/simple/price?ids={assets_str}&vs_currencies=usd"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Establish database connection to save live numbers
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                for asset_id in target_assets:
                    if asset_id in data:
                        live_price = float(data[asset_id]['usd'])
                        # If row exists, update it; otherwise, insert it
                        cursor.execute('''
                            INSERT INTO market_cache (asset_id, current_price, last_updated)
                            VALUES (?, ?, ?)
                            ON CONFLICT(asset_id) DO UPDATE SET
                                current_price = excluded.current_price,
                                last_updated = excluded.last_updated
                        ''', (asset_id, live_price, timestamp))
                
                conn.commit()
                conn.close()
                print(f"📡 [API Sync] Live prices synchronized successfully in database at {timestamp}")
            else:
                print(f"⚠️ [API Warning] Could not fetch data. API status code: {response.status_code}")
                
        except Exception as e:
            print(f"❌ [API Engine Error] Background connection failed: {str(e)}")
            
        # Hold engine activity for exactly 60 seconds before making the next API network request
        time.sleep(60)


# ---- 3. FRONTEND DASHBOARD LAYOUT INTERFACE ----
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Live Financial Portfolio Engine</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 40px; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { border-bottom: 1px solid #334155; padding-bottom: 20px; margin-bottom: 30px; }
        h1 { color: #38bdf8; margin: 0; }
        .summary-grid { display: flex; gap: 20px; margin-bottom: 35px; }
        .card { background-color: #1e293b; padding: 20px; border-radius: 10px; flex: 1; border: 1px solid #334155; }
        .card-label { font-size: 12px; color: #94a3b8; font-weight: bold; text-transform: uppercase; }
        .card-value { font-size: 26px; font-weight: bold; margin-top: 5px; }
        .profit { color: #4ade80; }
        .loss { color: #f87171; }
        table { width: 100%; border-collapse: collapse; background-color: #1e293b; border-radius: 10px; overflow: hidden; border: 1px solid #334155; }
        th, td { padding: 14px 18px; text-align: left; }
        th { background-color: #111827; color: #94a3b8; font-size: 13px; text-transform: uppercase; }
        td { border-bottom: 1px solid #334155; }
        .form-section { background-color: #1e293b; padding: 25px; border-radius: 10px; border: 1px solid #334155; margin-top: 40px; }
        .form-grid { display: flex; gap: 15px; margin-top: 15px; }
        input, select, button { background-color: #0f172a; border: 1px solid #334155; color: white; padding: 10px; border-radius: 6px; font-size: 14px; }
        button { background-color: #38bdf8; color: #0f172a; font-weight: bold; cursor: pointer; border: none; padding: 10px 20px; }
        button:hover { background-color: #7dd3fc; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>📡 Live Portfolio Tracker Dashboard</h1>
        <p style="color: #64748b; margin: 5px 0 0 0;">Consuming External Third-Party REST APIs via Multi-Threaded Microservices</p>
    </div>

    <div class="summary-grid">
        <div class="card">
            <div class="card-label">Total Invested Cost</div>
            <div class="card-value">${{ "%.2f"|format(totals.cost) }}</div>
        </div>
        <div class="card">
            <div class="card-label">Current Market Value</div>
            <div class="card-value" style="color: #38bdf8;">${{ "%.2f"|format(totals.value) }}</div>
        </div>
        <div class="card">
            <div class="card-label">Net Profit / Loss Margin</div>
            <div class="card-value {% if totals.pnl >= 0 %}profit{% else %}loss{% endif %}">
                ${{ "%.2f"|format(totals.pnl) }} ({{ "%.2f"|format(totals.percent) }}%)
            </div>
        </div>
    </div>

    <p style="font-size: 12px; color: #64748b; text-align: right; margin-top: -15px;">🔄 Background microservice auto-syncs market feeds every 60 seconds.</p>

    <table>
        <thead>
            <tr>
                <th>Asset Name</th>
                <th>Quantity</th>
                <th>Avg Purchase Price</th>
                <th>Live Market Price</th>
                <th>Invested Cost</th>
                <th>Current Value</th>
                <th>Net Return Margin</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td><strong>{{ item.name }}</strong> <span style="color: #64748b; font-size: 11px;">({{ item.id.upper() }})</span></td>
                <td>{{ item.quantity }}</td>
                <td>${{ "%.2f"|format(item.buy_price) }}</td>
                <td style="color: #38bdf8; font-weight: bold;">${{ "%.2f"|format(item.live_price) }}</td>
                <td>${{ "%.2f"|format(item.cost) }}</td>
                <td>${{ "%.2f"|format(item.value) }}</td>
                <td class="{% if item.pnl >= 0 %}profit{% else %}loss{% endif %}">${{ "%.2f"|format(item.pnl) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="form-section">
        <h3 style="margin-top: 0; color: #38bdf8;">➕ Log New Transaction Asset Position</h3>
        <form action="/add-asset" method="POST">
            <div class="form-grid">
                <div style="display: flex; flex-direction: column; flex: 1;">
                    <select name="asset_id">
                        <option value="bitcoin">Bitcoin (BTC)</option>
                        <option value="ethereum">Ethereum (ETH)</option>
                        <option value="solana">Solana (SOL)</option>
                    </select>
                </div>
                <div style="display: flex; flex-direction: column; flex: 1;">
                    <input type="number" step="any" name="quantity" placeholder="Quantity Owned" required>
                </div>
                <div style="display: flex; flex-direction: column; flex: 1;">
                    <input type="number" step="any" name="buy_price" placeholder="Purchase Price USD" required>
                </div>
                <button type="submit">Commit Entry</button>
            </div>
        </form>
    </div>
</div>
</body>
</html>
"""

@app.route('/')
def index():
    """Gathers investment balances and calculates net profits instantly using live data points."""
    conn = get_db_connection()
    investments = conn.execute('SELECT * FROM investments').fetchall()
    cache = conn.execute('SELECT * FROM market_cache').fetchall()
    conn.close()
    
    # Map cached values into a dictionary lookup map
    live_prices = {row['asset_id']: row['current_price'] for row in cache}
    
    processed_items = []
    total_cost = 0.0
    total_value = 0.0
    
    # Perform math equations on the fly for UI dashboard delivery
    for row in investments:
        asset_id = row['asset_id']
        live_price = live_prices.get(asset_id, row['buy_price'])  # Fallback to buy price if loading
        
        cost = row['buy_price'] * row['quantity']
        value = live_price * row['quantity']
        pnl = value - cost
        
        total_cost += cost
        total_value += value
        
        processed_items.append({
            'name': row['asset_name'],
            'id': row['asset_id'],
            'quantity': row['quantity'],
            'buy_price': row['buy_price'],
            'live_price': live_price,
            'cost': cost,
            'value': value,
            'pnl': pnl
        })
        
    total_pnl = total_value - total_cost
    pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0
    
    totals = {
        'cost': total_cost,
        'value': total_value,
        'pnl': total_pnl,
        'percent': pnl_percent
    }
    
    return render_template_string(DASHBOARD_HTML, items=processed_items, totals=totals)

@app.route('/add-asset', methods=['POST'])
def add_asset():
    """Adds a new token purchase position transaction record right into the database."""
    asset_id = request.form['asset_id']
    quantity = float(request.form['quantity'])
    buy_price = float(request.form['buy_price'])
    asset_name = asset_id.capitalize()
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO investments (asset_id, asset_name, buy_price, quantity)
        VALUES (?, ?, ?, ?)
    ''', (asset_id, asset_name, buy_price, quantity))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    
    # 🔥 ACTIVATE THE BACKGROUND MICROSERVICE WORKER ENGINE THREAD 🔥
    api_thread = threading.Thread(target=fetch_live_market_prices, daemon=True)
    api_thread.start()
    
    # Run user web routing container channel
    app.run(debug=True, use_reloader=False)