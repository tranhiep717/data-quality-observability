
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def ket_noi_database():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def kiem_tra_ket_noi():
    conn = ket_noi_database()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    bang = cursor.fetchall()
    cursor.close()
    conn.close()
    return bang
