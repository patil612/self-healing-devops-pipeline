import os
import sys
import re

# Load .env file manually if python-dotenv is not installed
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

load_env()
db_url = os.environ.get('DATABASE_URL')

if not db_url or "aws_rds_endpoint" in db_url or "<aws_rds_endpoint>" in db_url:
    print("ERROR: DATABASE_URL environment variable is not set or not configured in .env file.")
    print("Please copy .env.example to .env and configure your AWS RDS PostgreSQL connection string.")
    sys.exit(1)

# Parse URL: postgresql://<user>:<password>@<host>:<port>/<db>
match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
if not match:
    # Try parsing without port
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^/]+)/(.+)', db_url)
    if not match:
        print("ERROR: Invalid DATABASE_URL format. Must be: postgresql://username:password@host:port/dbname")
        sys.exit(1)
    username, password, host, dbname = match.groups()
    port = 5432
else:
    username, password, host, port, dbname = match.groups()
    port = int(port)

print(f"Connecting to database '{dbname}' on AWS RDS host '{host}'...")

try:
    # Try importing psycopg2-binary or pg8000 or default modules
    try:
        import psycopg2
        conn = psycopg2.connect(
            dbname=dbname,
            user=username,
            password=password,
            host=host,
            port=port
        )
        print("Connected successfully via psycopg2 driver.")
    except ImportError:
        try:
            import pg8000
            conn = pg8000.dbapi.connect(
                database=dbname,
                user=username,
                password=password,
                host=host,
                port=port
            )
            print("Connected successfully via pg8000 driver.")
        except ImportError:
            print("\nERROR: Database driver not found.")
            print("Please install either psycopg2-binary or pg8000 in your Python environment:")
            print("  pip install psycopg2-binary")
            print("  OR")
            print("  pip install pg8000")
            sys.exit(1)

    cursor = conn.cursor()

    # Create tables
    print("Creating tables inside PostgreSQL...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS builds (
            id SERIAL PRIMARY KEY,
            build_number INT UNIQUE NOT NULL,
            status VARCHAR(50) NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            duration_seconds INT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS healing_audits (
            id SERIAL PRIMARY KEY,
            build_number INT NOT NULL,
            detected_error TEXT NOT NULL,
            recommended_playbook VARCHAR(100) NOT NULL,
            execution_status VARCHAR(50) NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_repository (
            id SERIAL PRIMARY KEY,
            build_number INT NOT NULL,
            severity VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    print("Database tables initialized successfully!")
    cursor.close()
    conn.close()

except Exception as e:
    print(f"\nDatabase connection error: {e}")
    sys.exit(1)
