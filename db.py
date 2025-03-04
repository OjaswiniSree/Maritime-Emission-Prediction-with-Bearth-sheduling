import sqlite3
# Function to create a connection to the database
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('ship_infoo.db')
        return conn
    except sqlite3.Error as e:
        print(e)
        return conn
    
def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ship_infoo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ship_type TEXT NOT NULL,
                ship_size INTEGER NOT NULL,
                vessel_age INTEGER NOT NULL,
                fuel_type TEXT NOT NULL,
                fuel_consumption TEXT NOT NULL,
                engine_type TEXT NOT NULL,
                emission_control_technologies TEXT NOT NULL,
                load_factor INTEGER NOT NULL,
                Emissions INTEGER DEFAULT NULL,
                Berth INTEGER DEFAULT 0,
                from_time TIMESTAMP DEFAULT NULL,
                to_time TIMESTAMP DEFAULT NULL
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(e)
   