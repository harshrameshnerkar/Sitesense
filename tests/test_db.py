
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        os.getenv("DATABASE_URL")
    )

    cursor = conn.cursor()

    cursor.execute("SELECT current_database(), version();")

    result = cursor.fetchone()

    print("Database connected successfully!")
    print("Database:", result[0])
    print("PostgreSQL:", result[1])

    cursor.close()
    conn.close()

except Exception as e:
    print("Connection failed:", e)
