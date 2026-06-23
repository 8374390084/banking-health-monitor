import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "health_monitor.db")

class DBManager:
    def __init__(self):
        self.db_path = DB_PATH

    def get_conn(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_conn()
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS api_metrics (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp      TEXT    NOT NULL,
                endpoint       TEXT    NOT NULL,
                status_code    INTEGER,
                latency_ms     REAL,
                cpu_percent    REAL,
                memory_percent REAL,
                is_up          INTEGER DEFAULT 1
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    TEXT    NOT NULL,
                alarm_name   TEXT    NOT NULL,
                message      TEXT,
                severity     TEXT,
                endpoint     TEXT,
                resolved     INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()
        print("  [DB] Database ready!")

    def insert_metric(self, timestamp, endpoint, status_code, latency_ms, cpu, memory, is_up):
        conn = self.get_conn()
        conn.execute("""
            INSERT INTO api_metrics
            (timestamp, endpoint, status_code, latency_ms, cpu_percent, memory_percent, is_up)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, endpoint, status_code, latency_ms, cpu, memory, is_up))
        conn.commit()
        conn.close()

    def insert_incident(self, timestamp, alarm_name, message, severity, endpoint):
        conn = self.get_conn()
        conn.execute("""
            INSERT INTO incidents (timestamp, alarm_name, message, severity, endpoint)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, alarm_name, message, severity, endpoint))
        conn.commit()
        conn.close()

    def get_dashboard_stats(self):
        conn = self.get_conn()

        stats = conn.execute("""
            SELECT
                COUNT(*)                                  AS total_checks,
                SUM(is_up)                                AS successful,
                COUNT(*) - SUM(is_up)                     AS failed,
                ROUND(AVG(latency_ms), 2)                 AS avg_latency,
                ROUND(AVG(cpu_percent), 2)                AS avg_cpu,
                ROUND(AVG(memory_percent), 2)             AS avg_memory,
                ROUND(SUM(is_up) * 100.0 / COUNT(*), 2)  AS uptime_pct
            FROM api_metrics
        """).fetchone()

        incidents = conn.execute(
            "SELECT COUNT(*) FROM incidents"
        ).fetchone()[0]

        recent_metrics = conn.execute("""
            SELECT timestamp, endpoint, status_code, latency_ms,
                   cpu_percent, memory_percent, is_up
            FROM api_metrics ORDER BY id DESC LIMIT 20
        """).fetchall()

        recent_incidents = conn.execute("""
            SELECT timestamp, alarm_name, message, severity, endpoint
            FROM incidents ORDER BY id DESC LIMIT 10
        """).fetchall()

        conn.close()
        return {
            "total_checks":     stats[0] or 0,
            "successful":       stats[1] or 0,
            "failed":           stats[2] or 0,
            "avg_latency":      stats[3] or 0,
            "avg_cpu":          stats[4] or 0,
            "avg_memory":       stats[5] or 0,
            "uptime_pct":       stats[6] or 0,
            "total_incidents":  incidents,
            "recent_metrics":   recent_metrics,
            "recent_incidents": recent_incidents,
        }

    def get_endpoint_stats(self):
        conn = self.get_conn()
        rows = conn.execute("""
            SELECT endpoint,
                   COUNT(*)                                    AS total,
                   SUM(is_up)                                  AS up_count,
                   ROUND(AVG(latency_ms), 2)                   AS avg_latency,
                   ROUND(SUM(is_up) * 100.0 / COUNT(*), 2)    AS uptime_pct
            FROM api_metrics
            GROUP BY endpoint
        """).fetchall()
        conn.close()
        return rows