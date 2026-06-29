#!/usr/bin/env python
"""Check database schema"""
import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/automate')
cursor = conn.cursor()

# Check users table schema
cursor.execute("""SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position""")
columns = cursor.fetchall()
print('Users table columns:')
for col in columns:
    print(f'  {col[0]}: {col[1]} (nullable: {col[2]})')

# Check actual user data
cursor.execute('SELECT username, role_id FROM users LIMIT 3')
users = cursor.fetchall()
print(f'\nUsers with role_id:')
for u in users:
    print(f'  {u[0]}: role_id={u[1]}')

conn.close()