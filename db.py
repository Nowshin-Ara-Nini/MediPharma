import os
import mysql.connector
from mysql.connector import pooling

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "medipharma"),
    "auth_plugin": os.getenv("DB_AUTH_PLUGIN", "mysql_native_password"),
}

pool = pooling.MySQLConnectionPool(pool_name="mp_pool", pool_size=10, **DB_CONFIG)

class DB:
    def __enter__(self):
        self.conn = pool.get_connection()
        self.cur = self.conn.cursor(dictionary=True)
        return self.cur
    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.cur.close()
        self.conn.close()