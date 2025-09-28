import os, pyodbc
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
load_dotenv(ENV_FILE)

SERVER   = os.getenv("AZURE_SQL_SERVER", "")
DATABASE = os.getenv("AZURE_SQL_DATABASE", "")
USER     = os.getenv("AZURE_SQL_USERNAME", "")
PWD      = os.getenv("AZURE_SQL_PASSWORD", "")
DRIVER   = os.getenv("AZURE_SQL_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")

print("ODBC drivers found:", pyodbc.drivers())

# show DSN (password redacted)
dsn_print = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER=tcp:{SERVER},1433;"
    f"DATABASE={DATABASE};UID={USER};PWD=***REDACTED***;"
    "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=15;"
)
print("DSN preview:", dsn_print)

if not all([SERVER, DATABASE, USER, PWD]):
    raise SystemExit("Missing .env keys: AZURE_SQL_SERVER / AZURE_SQL_DATABASE / AZURE_SQL_USERNAME / AZURE_SQL_PASSWORD")

dsn_real = dsn_print.replace("***REDACTED***", PWD).replace("{DRIVER}", DRIVER)

try:
    with pyodbc.connect(dsn_real, timeout=15) as conn:
        cur = conn.cursor()
        cur.execute("SELECT @@VERSION;")
        version = cur.fetchone()[0]
        cur.execute("SELECT DB_NAME();")
        dbname = cur.fetchone()[0]
        print("✅ Connected")
        print("   Database:", dbname)
        print("   Server version:", version.splitlines()[0])
except pyodbc.Error as e:
    print("❌ Connection failed.")
    print("ODBC error:", e)
