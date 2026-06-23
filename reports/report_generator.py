import os
import sys
import json
from datetime import datetime, date
from fpdf import FPDF

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db_manager import DBManager

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(REPORTS_DIR, exist_ok=True)

db = DBManager()

class HealthReportPDF(FPDF):
    def header(self):
        self.set_fill_color(30, 58, 95)
        self.rect(0, 0, 210, 30, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.set_xy(10, 8)
        self.cell(0, 10, "Banking Platform - Daily Health Report", align="L")
        self.set_font("Helvetica", "", 9)
        self.set_xy(10, 18)
        self.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align="L")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()} | Capco Application Platform Support", align="C")


def generate_report():
    today = date.today().isoformat()
    stats = db.get_dashboard_stats()
    ep_stats = db.get_endpoint_stats()

    # Save JSON
    json_data = {
        "report_date": today,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_checks": stats["total_checks"],
            "successful": stats["successful"],
            "failed": stats["failed"],
            "uptime_percent": stats["uptime_pct"],
            "avg_latency_ms": stats["avg_latency"],
            "avg_cpu": stats["avg_cpu"],
            "avg_memory": stats["avg_memory"],
            "total_incidents": stats["total_incidents"],
        },
        "endpoints": [
            {"endpoint": r[0], "total": r[1], "uptime": r[4], "avg_latency": r[3]}
            for r in ep_stats
        ],
        "recent_incidents": [
            {"time": r[0], "alarm": r[1], "message": r[2], "severity": r[3]}
            for r in stats["recent_incidents"]
        ]
    }
    json_path = os.path.join(REPORTS_DIR, f"report_{today}.json")
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)

    # Save TXT
    txt_path = os.path.join(REPORTS_DIR, f"report_{today}.txt")
    with open(txt_path, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("  BANKING PLATFORM - DAILY HEALTH REPORT\n")
        f.write(f"  Date: {today}\n")
        f.write("=" * 60 + "\n\n")
        f.write("SUMMARY\n")
        f.write("-" * 40 + "\n")
        f.write(f"  Total Checks   : {stats['total_checks']}\n")
        f.write(f"  Successful     : {stats['successful']}\n")
        f.write(f"  Failed         : {stats['failed']}\n")
        f.write(f"  Uptime         : {stats['uptime_pct']}%\n")
        f.write(f"  Avg Latency    : {stats['avg_latency']} ms\n")
        f.write(f"  Avg CPU        : {stats['avg_cpu']}%\n")
        f.write(f"  Avg Memory     : {stats['avg_memory']}%\n")
        f.write(f"  Total Incidents: {stats['total_incidents']}\n\n")
        f.write("ENDPOINT BREAKDOWN\n")
        f.write("-" * 40 + "\n")
        for r in ep_stats:
            f.write(f"  {r[0]:<30} Uptime: {r[4]}%  Avg: {r[3]}ms\n")
        f.write("\nRECENT INCIDENTS\n")
        f.write("-" * 40 + "\n")
        if stats["recent_incidents"]:
            for r in stats["recent_incidents"]:
                f.write(f"  [{r[3]}] {r[0]}  {r[1]}\n")
                f.write(f"         {r[2]}\n")
        else:
            f.write("  No incidents recorded.\n")
        f.write("\n" + "=" * 60 + "\n")

    # Save PDF
    pdf = HealthReportPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Summary Section
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 10, "Summary", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    summary_items = [
        ("Total Checks",    str(stats["total_checks"])),
        ("Uptime",          f"{stats['uptime_pct']}%"),
        ("Successful",      str(stats["successful"])),
        ("Failed",          str(stats["failed"])),
        ("Avg Latency",     f"{stats['avg_latency']} ms"),
        ("Avg CPU",         f"{stats['avg_cpu']}%"),
        ("Avg Memory",      f"{stats['avg_memory']}%"),
        ("Total Incidents", str(stats["total_incidents"])),
    ]

    for i, (label, value) in enumerate(summary_items):
        if i % 2 == 0:
            x = 10
            y = pdf.get_y()
        else:
            x = 110
            y = pdf.get_y()
        pdf.set_fill_color(235, 243, 251)
        pdf.rect(x, y, 90, 14, 'F')
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(x + 3, y + 2)
        pdf.cell(84, 5, label, ln=False)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 58, 95)
        pdf.set_xy(x + 3, y + 7)
        pdf.cell(84, 5, value, ln=False)
        if i % 2 == 1:
            pdf.ln(18)

    pdf.ln(8)

    # Endpoint Table
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 10, "Endpoint Breakdown", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_fill_color(30, 58, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(80, 8, "Endpoint",     fill=True)
    pdf.cell(30, 8, "Total Checks", fill=True, align="C")
    pdf.cell(30, 8, "Uptime %",     fill=True, align="C")
    pdf.cell(30, 8, "Avg Latency",  fill=True, align="C")
    pdf.ln()

    for i, r in enumerate(ep_stats):
        if i % 2 == 0:
            pdf.set_fill_color(245, 249, 255)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(50, 50, 50)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(80, 7, str(r[0]), fill=True)
        pdf.cell(30, 7, str(r[1]), fill=True, align="C")
        if r[4] and r[4] >= 99:
            pdf.set_text_color(0, 150, 0)
        else:
            pdf.set_text_color(200, 100, 0)
        pdf.cell(30, 7, f"{r[4]}%", fill=True, align="C")
        pdf.set_text_color(50, 50, 50)
        pdf.cell(30, 7, f"{r[3]} ms", fill=True, align="C")
        pdf.ln()

    pdf.ln(6)

    # Incidents Section
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 10, "Recent Incidents", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    if stats["recent_incidents"]:
        for r in stats["recent_incidents"]:
            if r[3] == "CRITICAL":
                pdf.set_fill_color(255, 245, 245)
                pdf.set_text_color(200, 0, 0)
            else:
                pdf.set_fill_color(255, 250, 240)
                pdf.set_text_color(200, 100, 0)
            pdf.rect(10, pdf.get_y(), 190, 14, 'F')
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_xy(13, pdf.get_y() + 2)
            pdf.cell(30, 5, f"[{r[3]}]", ln=False)
            pdf.set_text_color(80, 80, 80)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(0, 5, f"{r[1]}  -  {r[0]}", ln=True)
            pdf.set_xy(13, pdf.get_y())
            pdf.set_text_color(120, 120, 120)
            pdf.cell(0, 5, str(r[2]), ln=True)
            pdf.ln(1)
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 150, 0)
        pdf.cell(0, 8, "  No incidents recorded. Platform is healthy!", ln=True)

    pdf_path = os.path.join(REPORTS_DIR, f"report_{today}.pdf")
    pdf.output(pdf_path)

    print("\n" + "=" * 55)
    print("  DAILY HEALTH REPORT GENERATED!")
    print("=" * 55)
    print(f"  JSON -> reports/output/report_{today}.json")
    print(f"  TXT  -> reports/output/report_{today}.txt")
    print(f"  PDF  -> reports/output/report_{today}.pdf")
    print("=" * 55)
    print(f"\n  Uptime       : {stats['uptime_pct']}%")
    print(f"  Avg Latency  : {stats['avg_latency']} ms")
    print(f"  Total Checks : {stats['total_checks']}")
    print(f"  Incidents    : {stats['total_incidents']}")
    print("\n  Report saved successfully!")


if __name__ == "__main__":
    db.init_db()
    generate_report()