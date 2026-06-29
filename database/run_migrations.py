"""Database migration runner"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5433)),
            database=os.getenv('DB_NAME', 'automate'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None


def run_migration_file(conn, file_path):
    """Run a single migration file"""
    try:
        with open(file_path, 'r') as f:
            sql_content = f.read()
        
        with conn.cursor() as cur:
            cur.execute(sql_content)
        
        conn.commit()
        print(f"✓ Executed: {file_path}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to execute {file_path}: {e}")
        return False


def main():
    """Run all migrations"""
    conn = get_db_connection()
    if not conn:
        sys.exit(1)
    
    migrations_dir = Path(__file__).parent / "migrations"
    
    # List of migration files to run in order
    migration_files = [
        "012_redesign_schema_final_updates.sql",
    ]
    
    print("Running database migrations...")
    print(f"Migrations directory: {migrations_dir}\n")
    
    failed = False
    for migration_file in migration_files:
        file_path = migrations_dir / migration_file
        if file_path.exists():
            if not run_migration_file(conn, file_path):
                failed = True
        else:
            print(f"✗ Migration file not found: {file_path}")
            failed = True
    
    conn.close()
    
    if not failed:
        print("\n✓ All migrations executed successfully!")
        return 0
    else:
        print("\n✗ Some migrations failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())