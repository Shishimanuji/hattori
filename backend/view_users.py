#!/usr/bin/env python
"""View users in the database"""
import sqlite3

# Connect to database
conn = sqlite3.connect('prms.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all users
cursor.execute("SELECT id, username, email, password_hash, role, is_active FROM users")
rows = cursor.fetchall()

print("=" * 120)
print("USERS TABLE - Where Credentials Are Stored".center(120))
print("=" * 120)
print()

for i, row in enumerate(rows, 1):
    print(f"USER #{i}")
    print(f"  ID:              {row['id']}")
    print(f"  Username:        {row['username']}")
    print(f"  Email:           {row['email']}")
    print(f"  Password Hash:   {row['password_hash']}")
    print(f"  Role:            {row['role']}")
    print(f"  Is Active:       {'Yes' if row['is_active'] else 'No'}")
    print("-" * 120)
    print()

conn.close()
