#!/usr/bin/env python
"""Fix database schema by removing the duplicate role column"""
import psycopg2

print("Fixing database schema - removing duplicate 'role' column from users table...")

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/automate')
cursor = conn.cursor()

try:
    # Drop the role column (keeping only role_id)
    print("Dropping 'role' column from users table...")
    cursor.execute("ALTER TABLE users DROP COLUMN IF EXISTS role")
    conn.commit()
    print("✅ Successfully dropped 'role' column")
    
    # Verify the change
    cursor.execute("""SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'users' AND column_name IN ('role', 'role_id')""")
    remaining_cols = cursor.fetchall()
    print(f"\nRemaining role columns: {[c[0] for c in remaining_cols]}")
    
    if len(remaining_cols) == 1 and remaining_cols[0][0] == 'role_id':
        print("✅ Schema fixed! Users table now only has 'role_id' column")
    else:
        print("⚠️ Warning: Unexpected columns remain")
        
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
