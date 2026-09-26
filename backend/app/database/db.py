"""
MediKiosk & AyurKiosk - Database Access Layer
SIH26047: AI-Powered Digital Clinical Intake Platform

Exports the centralized, persistent SQLDatabase instance `db`.
Replaces previous in-memory storage with SQLite relational persistence.
"""

from backend.app.database.sql_db import SQLDatabase

# Primary relational database instance connected to SQLite (patient_intake.db)
db = SQLDatabase()

# Alias for backwards compatibility
InMemoryDB = SQLDatabase

__all__ = ["db", "SQLDatabase", "InMemoryDB"]
