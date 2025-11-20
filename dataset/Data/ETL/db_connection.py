import os
import pyodbc
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
load_dotenv(ENV_FILE)

def get_connection() -> pyodbc.Connection:
    DRIVER   = os.getenv("AZURE_SQL_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
    SERVER   = os.getenv("AZURE_SQL_SERVER")
    DATABASE = os.getenv("AZURE_SQL_DATABASE")
    USER     = os.getenv("AZURE_SQL_USERNAME")
    PWD      = os.getenv("AZURE_SQL_PASSWORD")

    DSN = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER=tcp:{SERVER},1433;"
        f"DATABASE={DATABASE};UID={USER};PWD={PWD};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return pyodbc.connect(DSN)
