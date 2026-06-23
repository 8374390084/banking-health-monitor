 
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, jsonify
from database.db_manager import DBManager

app = Flask(__name__)
db  = DBManager()

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/dashboard")
def dashboard_data():
    stats    = db.get_dashboard_stats()
    ep_stats = db.get_endpoint_stats()
    return jsonify({
        "total_checks":     stats["total_checks"],
        "successful":       stats["successful"],
        "failed":           stats["failed"],
        "avg_latency":      stats["avg_latency"],
        "avg_cpu":          stats["avg_cpu"],
        "avg_memory":       stats["avg_memory"],
        "uptime_pct":       stats["uptime_pct"],
        "total_incidents":  stats["total_incidents"],
        "recent_metrics":   stats["recent_metrics"],
        "recent_incidents": stats["recent_incidents"],
        "endpoint_stats":   ep_stats,
    })

if __name__ == "__main__":
    db.init_db()
    print("\n🚀 Dashboard running → http://localhost:8080\n")
    app.run(host="0.0.0.0", port=8080, debug=False)