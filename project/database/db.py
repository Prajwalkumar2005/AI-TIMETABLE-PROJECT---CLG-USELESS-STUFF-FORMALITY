import mysql.connector
from mysql.connector import Error
import os

class Database:
    def __init__(self):
        # Configuration - move to environment variables in production
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''), # set DB_PASSWORD env for safety
            'database': os.getenv('DB_NAME', 'timetable_ai')
        }

    def get_connection(self):
        try:
            connection = mysql.connector.connect(**self.config)
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None

    def execute_query(self, query, params=None):
        connection = self.get_connection()
        if not connection: return None
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            connection.commit()
            return cursor
        except Error as e:
            print(f"Error executing query: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

    def fetch_all(self, query, params=None):
        connection = self.get_connection()
        if not connection: return []
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Error fetching data: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if connection: connection.close()

db = Database()
