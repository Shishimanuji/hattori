import sqlite3
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

conn = sqlite3.connect('prms.db')
cursor = conn.cursor()

# Update testuser
cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hash_password('PrmsTest@2026!'), 'testuser'))
# Update adminuser
cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hash_password('PrmsAdmin@2026!'), 'adminuser'))

conn.commit()
conn.close()

print("✅ Existing user passwords updated in the database.")
