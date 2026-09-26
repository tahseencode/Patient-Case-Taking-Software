"""
Database Administration & CLI Tool for MediKiosk / AyurKiosk
SIH26047: AI-Powered Digital Clinical Intake Platform

Usage:
    python -m backend.app.database.init_db --status
    python -m backend.app.database.init_db --init
    python -m backend.app.database.init_db --seed
    python -m backend.app.database.init_db --reset
"""

import sys
import os
import argparse
from datetime import datetime

# Ensure project root is in sys.path when running script directly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app.database.sql_db import SQLDatabase
from backend.app.core.config import settings


def print_banner():
    print("=" * 70)
    print(" MediKiosk / AyurKiosk - SQL Relational Database Management CLI")
    print(f" Database File: {settings.DATABASE_PATH}")
    print(f" Standard: ABDM FHIR R4 & DPDP Act 2023 Compliant")
    print("=" * 70)


def show_status(db: SQLDatabase):
    stats = db.get_database_stats()
    print("\n[+] Database Engine & Health Status:")
    print(f"    - Engine:          {stats['engine']}")
    print(f"    - SQLite Version:  {stats['sqlite_version']}")
    print(f"    - Journal Mode:    {stats['journal_mode']}")
    print(f"    - File Path:       {stats['database_file']}")
    print(f"    - File Size:       {stats['file_size_kb']} KB ({stats['file_size_bytes']} bytes)")
    print(f"    - Status:          {stats['status'].upper()}")

    print("\n[+] Relational Table Row Counts:")
    print("-" * 50)
    print(f" {'Table Name':<28} | {'Rows / Records':>15}")
    print("-" * 50)
    for table, count in stats["table_counts"].items():
        print(f" {table:<28} | {count:>15}")
    print("-" * 50)

    # Show active queue
    queue = db.get_opd_queue()
    print(f"\n[+] Active Waiting OPD Queue ({len(queue)} Patients):")
    if queue:
        for idx, item in enumerate(queue, 1):
            flag = "[RED-FLAG]" if item["is_red_flag"] else "[ROUTINE]"
            print(f"    {idx}. Token: {item['token']} | {item['patient_name']} ({item['gender']}, {item['age']}y) | Stream: {item['stream'].upper()} | {flag} {item['chief_complaint']}")
    else:
        print("    (Queue is currently empty)")

    # Show triage alerts
    alerts = db.get_triage_alerts()
    print(f"\n[+] Active Triage Alerts ({len(alerts)}):")
    if alerts:
        for idx, a in enumerate(alerts, 1):
            print(f"    {idx}. Token: {a['token']} - {a['patient_name']} -> {a['rationale']} [Action: {a['action']}]")
    else:
        print("    (No emergency alerts active)")


def reset_database(db: SQLDatabase):
    print("\n[!] Resetting database tables...")
    tables = [
        "audit_logs", "triage_alerts", "opd_queue", "consultations",
        "documents", "clinical_summaries", "intake_sessions", "consents", "patients"
    ]
    with db.get_connection() as conn:
        for t in tables:
            conn.execute(f"DROP TABLE IF EXISTS {t};")
    print("[+] All tables dropped successfully.")
    db.init_schema()
    print("[+] Schema re-initialized from schema.sql.")
    db.seed_initial_demo_data()
    print("[+] Demo data re-seeded.")


def seed_database(db: SQLDatabase):
    print("\n[!] Seeding demo data...")
    db.seed_initial_demo_data()
    print("[+] Demo data seeded successfully.")


def main():
    parser = argparse.ArgumentParser(description="MediKiosk Database Administration Utility")
    parser.add_argument("--status", action="store_true", help="Display database health and table record counts")
    parser.add_argument("--init", action="store_true", help="Initialize tables from schema.sql if not existing")
    parser.add_argument("--seed", action="store_true", help="Seed initial demo patients and records")
    parser.add_argument("--reset", action="store_true", help="Drop all tables and re-create schema with fresh seed data")

    args = parser.parse_args()
    print_banner()

    db = SQLDatabase()

    if args.reset:
        reset_database(db)
        show_status(db)
    elif args.seed:
        seed_database(db)
        show_status(db)
    elif args.init:
        db.init_schema()
        print("[+] Schema initialized successfully.")
        show_status(db)
    else:
        # Default action: show status
        show_status(db)


if __name__ == "__main__":
    main()
