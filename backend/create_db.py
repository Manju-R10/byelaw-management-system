import pymysql
import sys
import os

# Add backend folder to sys.path to load app.config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.config import settings
except ImportError:
    # Fallback to local import if run from a different Cwd
    sys.path.insert(0, r"C:\Users\Mahalakshmi\AppData\Local\Programs\Python\Python313\lib\site-packages")
    sys.path.insert(0, r"C:\Users\Mahalakshmi\.gemini\antigravity\scratch\byelaw_management_system\backend")
    from app.config import settings

def create_db():
    print(f"Connecting to MySQL at {settings.DB_HOST}:{settings.DB_PORT} as {settings.DB_USER}...")
    try:
        connection = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            charset="utf8mb4"
        )
        cursor = connection.cursor()
        sql = f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        cursor.execute(sql)
        print(f"Database `{settings.DB_NAME}` successfully verified/created.")
        connection.close()
    except Exception as e:
        print(f"Failed to create database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    create_db()
