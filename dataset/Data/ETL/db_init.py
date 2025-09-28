import os, re
from pathlib import Path
import pyodbc
from dotenv import load_dotenv

# --- locate and load DeepChessIQ/.env ---
ROOT = Path(__file__).resolve().parents[2]   # -> DeepChessIQ/
ENV_FILE = ROOT / ".env"
if not ENV_FILE.exists():
    raise SystemExit(f".env not found at: {ENV_FILE}")
load_dotenv(ENV_FILE)

# --- read from .env ---
SERVER   = os.getenv("AZURE_SQL_SERVER")           # e.g. myserver.database.windows.net
DATABASE = os.getenv("AZURE_SQL_DATABASE")
USER     = os.getenv("AZURE_SQL_USERNAME")
PWD      = os.getenv("AZURE_SQL_PASSWORD")
DRIVER   = os.getenv("AZURE_SQL_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")

if not all([SERVER, DATABASE, USER, PWD]):
    raise SystemExit("Missing one or more .env keys: AZURE_SQL_SERVER / AZURE_SQL_DATABASE / AZURE_SQL_USERNAME / AZURE_SQL_PASSWORD")

DSN = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER=tcp:{SERVER},1433;"
    f"DATABASE={DATABASE};UID={USER};PWD={PWD};"
    "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)

def apply_sql_file(sql_path: Path):
    text = sql_path.read_text(encoding="utf-8")
    batches = [b.strip() for b in re.split(r'^\s*GO\s*$', text, flags=re.MULTILINE|re.IGNORECASE) if b.strip()]
    with pyodbc.connect(DSN) as conn:
        cur = conn.cursor()
        for i, b in enumerate(batches, 1):
            cur.execute(b)
        conn.commit()

if __name__ == "__main__":
    sql_file = ROOT / "Data" / "SQL" / "schema.sql"
    print("Using .env at:", ENV_FILE)
    print("Applying schema from:", sql_file)
    apply_sql_file(sql_file)
    print("Schema applied (includes pgn_movetext_full)")
