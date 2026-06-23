import time
import random
import logging
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

logging.basicConfig(
    filename="logs/api.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

ACCOUNTS = {
    "ACC001": {"name": "Rajesh Kumar",         "balance": 125000.00, "type": "Savings"},
    "ACC002": {"name": "Priya Sharma",         "balance": 340000.50, "type": "Current"},
    "ACC003": {"name": "Nagesh Padakandla",    "balance": 87500.75,  "type": "Savings"},
}

TRADES = [
    {"id": "TRD001", "stock": "RELIANCE", "qty": 100, "price": 2450.00, "status": "EXECUTED"},
    {"id": "TRD002", "stock": "INFY",     "qty": 50,  "price": 1780.50, "status": "PENDING"},
    {"id": "TRD003", "stock": "TCS",      "qty": 200, "price": 3520.00, "status": "EXECUTED"},
]

def simulate_latency():
    delay = random.uniform(0.05, 0.5)
    if random.random() < 0.1:
        delay = random.uniform(1.5, 3.0)
    time.sleep(delay)
    return round(delay * 1000, 2)

def log_request(endpoint, status, latency_ms):
    level = "WARNING" if latency_ms > 1000 else "INFO"
    msg = f"endpoint={endpoint} status={status} latency={latency_ms}ms"
    if level == "WARNING":
        logging.warning(msg)
    else:
        logging.info(msg)

@app.route("/health", methods=["GET"])
def health_check():
    latency = simulate_latency()
    log_request("/health", 200, latency)
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_ms": latency,
        "version": "1.0.0"
    }), 200

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    latency = simulate_latency()
    if random.random() < 0.05:
        log_request("/api/accounts", 500, latency)
        return jsonify({"error": "Internal Server Error", "code": 500}), 500
    log_request("/api/accounts", 200, latency)
    return jsonify({"accounts": list(ACCOUNTS.values()), "count": len(ACCOUNTS)}), 200

@app.route("/api/accounts/<account_id>", methods=["GET"])
def get_account(account_id):
    latency = simulate_latency()
    if account_id not in ACCOUNTS:
        log_request(f"/api/accounts/{account_id}", 404, latency)
        return jsonify({"error": "Account not found"}), 404
    log_request(f"/api/accounts/{account_id}", 200, latency)
    return jsonify(ACCOUNTS[account_id]), 200

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    latency = simulate_latency()
    txns = [
        {"txn_id": f"TXN{i:04d}",
         "account": random.choice(list(ACCOUNTS.keys())),
         "amount": round(random.uniform(500, 50000), 2),
         "type": random.choice(["CREDIT", "DEBIT"]),
         "timestamp": datetime.now().isoformat()}
        for i in range(1, 6)
    ]
    log_request("/api/transactions", 200, latency)
    return jsonify({"transactions": txns, "count": len(txns)}), 200

@app.route("/api/trades", methods=["GET"])
def get_trades():
    latency = simulate_latency()
    log_request("/api/trades", 200, latency)
    return jsonify({"trades": TRADES, "count": len(TRADES)}), 200

@app.route("/api/trades", methods=["POST"])
def create_trade():
    latency = simulate_latency()
    data = request.json or {}
    if not all(k in data for k in ["stock", "qty", "price"]):
        return jsonify({"error": "Missing fields: stock, qty, price"}), 400
    trade = {
        "id": f"TRD{len(TRADES)+1:03d}",
        "stock": data["stock"].upper(),
        "qty": data["qty"],
        "price": data["price"],
        "status": "PENDING",
        "timestamp": datetime.now().isoformat()
    }
    TRADES.append(trade)
    log_request("/api/trades", 201, latency)
    return jsonify(trade), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)