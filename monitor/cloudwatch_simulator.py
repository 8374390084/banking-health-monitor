import time
import random
import requests
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db_manager import DBManager

API_BASE      = "http://localhost:5000"
POLL_INTERVAL = 10

ENDPOINTS = [
    "/health",
    "/api/accounts",
    "/api/transactions",
    "/api/trades",
]

db = DBManager()

def simulate_ec2_metrics():
    cpu = random.uniform(20, 70)
    if random.random() < 0.15:
        cpu = random.uniform(80, 98)
    memory = random.uniform(40, 70)
    if random.random() < 0.10:
        memory = random.uniform(76, 92)
    return round(cpu, 2), round(memory, 2)

def poll_endpoint(endpoint):
    url = API_BASE + endpoint
    start = time.time()
    try:
        resp = requests.get(url, timeout=5)
        latency_ms = round((time.time() - start) * 1000, 2)
        return resp.status_code, latency_ms
    except requests.exceptions.ConnectionError:
        return 0, 0
    except requests.exceptions.Timeout:
        return 504, 5000

def check_alarms(cpu, memory, endpoint, status_code, latency_ms):
    alarms = []

    if cpu > 80.0:
        alarms.append({
            "alarm_name": "HighCPUUtilization",
            "message": f"CPU usage {cpu}% exceeds 80%",
            "severity": "CRITICAL" if cpu > 90 else "WARNING"
        })

    if memory > 75.0:
        alarms.append({
            "alarm_name": "HighMemoryUsage",
            "message": f"Memory {memory}% exceeds 75%",
            "severity": "WARNING"
        })

    if latency_ms > 1000:
        alarms.append({
            "alarm_name": "HighAPILatency",
            "message": f"API {endpoint} latency {latency_ms}ms exceeds 1000ms",
            "severity": "WARNING"
        })

    if status_code >= 500:
        alarms.append({
            "alarm_name": "APIServerError",
            "message": f"API {endpoint} returned HTTP {status_code}",
            "severity": "CRITICAL"
        })

    if status_code == 0:
        alarms.append({
            "alarm_name": "APIDown",
            "message": f"API {endpoint} is unreachable!",
            "severity": "CRITICAL"
        })

    return alarms

def run_monitor():
    print("=" * 55)
    print("  Banking Platform Health Monitor — Started")
    print(f"  Polling every {POLL_INTERVAL}s")
    print("=" * 55)

    db.init_db()

    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cpu, memory = simulate_ec2_metrics()

        print(f"\n[{timestamp}]")
        print(f"  EC2 → CPU: {cpu}%  Memory: {memory}%")

        for endpoint in ENDPOINTS:
            status_code, latency_ms = poll_endpoint(endpoint)
            is_up = 1 if 200 <= status_code < 400 else 0

            db.insert_metric(timestamp, endpoint, status_code,
                             latency_ms, cpu, memory, is_up)

            icon = "✅" if is_up else "❌"
            print(f"  {icon} {endpoint:<28} HTTP {status_code}  {latency_ms}ms")

            alarms = check_alarms(cpu, memory, endpoint, status_code, latency_ms)
            for alarm in alarms:
                db.insert_incident(timestamp, alarm["alarm_name"],
                                   alarm["message"], alarm["severity"], endpoint)
                print(f"    🚨 [{alarm['severity']}] {alarm['message']}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_monitor()