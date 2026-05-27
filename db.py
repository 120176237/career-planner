# 职路星途 - 数据库抽象层
# 支持 SQLite（本地开发）和 MySQL（抖音云部署）
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# 数据库类型：sqlite | mysql
DB_TYPE = os.getenv("DB_TYPE", "sqlite")

# SQLite 配置
DB_FILE = Path(__file__).parent / "career.db"

# MySQL 配置（从环境变量读取）
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "career_planner")

try:
    import pymysql
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

def get_connection():
    if DB_TYPE == "mysql" and HAS_MYSQL:
        return pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4'
        )
    else:
        conn = sqlite3.connect(str(DB_FILE))
        conn.row_factory = sqlite3.Row
        return conn

def db_execute(sql, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    if DB_TYPE == "mysql":
        sql = sql.replace("?", "%s")
    cursor.execute(sql, params or ())
    return conn, cursor

def _cursor_dict(cursor, row):
    if DB_TYPE == "mysql":
        return row
    else:
        return dict(zip([d[0] for d in cursor.description], row))

def execute_query(sql, params=None, fetch_one=False):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if DB_TYPE == "mysql":
            sql = sql.replace("?", "%s")
        cursor.execute(sql, params or ())
        if sql.strip().upper().startswith("SELECT"):
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
            if result and not isinstance(result, dict) and not isinstance(result[0], dict):
                cols = [d[0] for d in cursor.description]
                if fetch_one:
                    result = dict(zip(cols, result))
                else:
                    result = [dict(zip(cols, row)) for row in result]
            return result
        else:
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()

def execute_sqlite(sql, params=None, fetch_one=False):
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        if sql.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            return result[0] if fetch_one and result else (None if fetch_one else result)
        else:
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()

def init_db():
    if DB_TYPE == "mysql" and HAS_MYSQL:
        _init_mysql_tables()
    else:
        _init_sqlite_tables()

def _init_mysql_tables():
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        charset='utf8mb4'
    )
    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE `{MYSQL_DATABASE}`")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vip_consults (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(50),
                questions TEXT,
                answerTexts TEXT,
                userType VARCHAR(50),
                consultText TEXT,
                createdAt DOUBLE,
                status VARCHAR(50) DEFAULT 'pending'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                order_id VARCHAR(255) PRIMARY KEY,
                version VARCHAR(50) NOT NULL,
                amount DOUBLE NOT NULL,
                payment_method VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                device_id VARCHAR(255),
                user_type VARCHAR(50),
                created_at DOUBLE,
                paid_at DOUBLE,
                metadata TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invalid_answer_records (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                q_index INTEGER,
                q_text VARCHAR(500),
                original_value VARCHAR(500),
                corrected_value VARCHAR(500),
                user_type VARCHAR(50),
                created_at DOUBLE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        conn.commit()
        print(f"[DB] MySQL 表初始化完成: {MYSQL_DATABASE}")
    finally:
        conn.close()

def _init_sqlite_tables():
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vip_consults (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            questions TEXT,
            answerTexts TEXT,
            userType TEXT,
            consultText TEXT,
            createdAt REAL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            order_id TEXT PRIMARY KEY,
            version TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            device_id TEXT,
            user_type TEXT,
            created_at REAL,
            paid_at REAL,
            metadata TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invalid_answer_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            q_index INTEGER,
            q_text TEXT,
            original_value TEXT,
            corrected_value TEXT,
            user_type TEXT,
            created_at REAL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[DB] SQLite 表初始化完成")
    _migrate_json_to_sqlite()

def _migrate_json_to_sqlite():
    VIP_CONSULTS_FILE = Path(__file__).parent / "vip_consults.json"
    if not VIP_CONSULTS_FILE.exists():
        return
    try:
        with open(VIP_CONSULTS_FILE, 'r', encoding='utf-8') as f:
            consults = json.load(f)
        conn = sqlite3.connect(str(DB_FILE))
        cursor = conn.cursor()
        for consult in consults:
            cursor.execute(
                "SELECT id FROM vip_consults WHERE email = ? AND createdAt = ?",
                (consult.get('email'), consult.get('createdAt'))
            )
            if cursor.fetchone():
                continue
            cursor.execute('''
                INSERT INTO vip_consults 
                (id, name, email, phone, questions, answerTexts, userType, consultText, createdAt, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                consult.get('id'),
                consult.get('name', ''),
                consult.get('email', ''),
                consult.get('phone', ''),
                json.dumps(consult.get('answers', {})),
                json.dumps(consult.get('answerTexts', {})),
                str(consult.get('userType', '')),
                consult.get('consultText', ''),
                consult.get('createdAt', 0),
                consult.get('status', 'pending')
            ))
        conn.commit()
        conn.close()
        print(f"[DB] 已迁移 {len(consults)} 条VIP记录到SQLite")
    except Exception as e:
        print(f"[DB] 迁移失败: {e}")