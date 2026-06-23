 
import schedule
import time
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from reports.report_generator import generate_report
from database.db_manager import DBManager

db = DBManager()

def run_report():
    print(f"\n⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running scheduled report...")
    try:
        generate_report()
        print("✅ Scheduled report completed!")
    except Exception as e:
        print(f"❌ Report failed: {e}")

def main():
    db.init_db()

    print("=" * 55)
    print("  Auto Report Scheduler — Started")
    print("=" * 55)
    print("  📅 Daily report scheduled at 08:00 AM every day")
    print("  ⚡ Running one report now immediately...")
    print("=" * 55)

    # Run once immediately when started
    run_report()

    # Schedule to run every day at 8:00 AM
    schedule.every().day.at("08:00").do(run_report)

    # Also run every 1 hour (for testing purposes)
    schedule.every(1).hours.do(run_report)

    print("\n✅ Scheduler is running!")
    print("   Next report will run in 1 hour")
    print("   Daily report runs at 08:00 AM")
    print("\n   Press Ctrl+C to stop\n")

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()