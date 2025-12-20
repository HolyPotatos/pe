import sqlite3
import security



login = "admin"
password = "123"

p_hash, p_salt = security.password_hash(password)
conn = sqlite3.connect("autoparts_shop.db")
cur = conn.cursor()
cur.execute("SELECT password_hash, salt FROM UserAuthData")
print(cur.fetchall())
conn.close()
#cur.execute("INSERT INTO UserAuthData (user_id, login, password_hash, salt, is_active) VALUES (?, ?, ?, ?, ?)", (1, login, p_hash, p_salt, 1))
#conn.commit()
