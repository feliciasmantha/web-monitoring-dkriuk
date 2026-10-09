import psycopg2
from config import *

def get_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            sslmode="require"
        )
        return conn

    except Exception as e:
        print("Database Error:", e)
        return None