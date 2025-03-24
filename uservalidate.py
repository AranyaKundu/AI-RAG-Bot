import sqlite3, bcrypt

# These three lines are to solve a problem with streamlit cloud
import pysqlite3 as sqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Create Users first
# Create Users.db if not exists already: import sqlite3
def create_users_table():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    query = """
        create table if not exists users (
            id integer primary key autoincrement,
            username text unique not null,
            password text not null, 
            total_cost REAL DEFAULT 0)
    """
    c.execute(query)
    conn.commit()
    conn.close()

# Add new user to the SQLite database: import sqlite3
def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        print("User added successfully!")
    except sqlite3.IntegrityError:
        print("Username already exists!")
    conn.close()

def update_user_cost(username, cost):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET total_cost = total_cost + ? WHERE username = ?", (cost, username))
    conn.commit()
    conn.close()

def get_user_cost(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT total_cost FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0.0

# verify existing user
def verify_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    fetch_pwd = "SELECT password FROM users WHERE username = ?"
    c.execute(fetch_pwd, (username,))
    result = c.fetchone()
    conn.close()

    if result:
        stored_hashed_password = result[0]
        return bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password)  
    return False