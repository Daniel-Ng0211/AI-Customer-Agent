
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

DB_PATH = Path(__file__).with_name("customers.db")


# =================================
# 1. KET NOI DATABASE
# =================================

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def current_time():
    return datetime.now().astimezone().isoformat(
        timespec="seconds"
    )


# =================================
# 2. KHOI TAO DATABASE
# =================================

def init_db():

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                purpose TEXT,
                check_in TEXT NOT NULL,
                check_out TEXT,
                FOREIGN KEY(customer_id)
                REFERENCES customers(id)
            )
        """)


# =================================
# 3. CREATE - THEM KHACH HANG
# =================================

def add_customer(customer_code, full_name):

    customer_code = customer_code.strip()
    full_name = full_name.strip()

    if not customer_code or not full_name:
        raise ValueError("Không được để trống thông tin.")

    with get_connection() as conn:

        cursor = conn.execute("""
            INSERT INTO customers
            (customer_code, full_name, created_at)
            VALUES (?, ?, ?)
        """, (
            customer_code,
            full_name,
            current_time()
        ))

        return cursor.lastrowid


# =================================
# 4. READ - DANH SACH KHACH HANG
# =================================

def list_customers(keyword=""):

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT *
            FROM customers
            WHERE customer_code LIKE ?
               OR full_name LIKE ?
            ORDER BY id DESC
        """, (
            f"%{keyword}%",
            f"%{keyword}%"
        )).fetchall()

        return [dict(row) for row in rows]


# =================================
# 5. UPDATE - SUA KHACH HANG
# =================================

def update_customer(customer_id, customer_code, full_name):

    customer_code = customer_code.strip()
    full_name = full_name.strip()

    if not customer_code or not full_name:
        raise ValueError("Không được để trống thông tin.")

    with get_connection() as conn:

        cursor = conn.execute("""
            UPDATE customers
            SET customer_code = ?,
                full_name = ?
            WHERE id = ?
        """, (
            customer_code,
            full_name,
            customer_id
        ))

        if cursor.rowcount == 0:
            raise ValueError("Không tìm thấy khách hàng.")


# =================================
# 6. DELETE - XOA KHACH HANG
# =================================

def delete_customer(customer_id):

    with get_connection() as conn:

        # Không xóa nếu khách đã có lịch sử ra vào
        visits = conn.execute("""
            SELECT COUNT(*)
            FROM visits
            WHERE customer_id = ?
        """, (customer_id,)).fetchone()[0]

        if visits > 0:
            raise ValueError(
                "Không thể xóa khách hàng đã có lịch sử ra vào. "
                "Hãy giữ hồ sơ để bảo toàn dữ liệu."
            )

        cursor = conn.execute("""
            DELETE FROM customers
            WHERE id = ?
        """, (customer_id,))

        if cursor.rowcount == 0:
            raise ValueError("Không tìm thấy khách hàng.")


# =================================
# 7. CHECK-IN
# =================================

def check_in(customer_id, purpose=""):

    with get_connection() as conn:

        active = conn.execute("""
            SELECT id
            FROM visits
            WHERE customer_id = ?
              AND check_out IS NULL
        """, (customer_id,)).fetchone()

        if active:
            raise ValueError(
                "Khách hàng hiện đang ở trong phòng."
            )

        cursor = conn.execute("""
            INSERT INTO visits
            (customer_id, purpose, check_in)
            VALUES (?, ?, ?)
        """, (
            customer_id,
            purpose.strip(),
            current_time()
        ))

        return cursor.lastrowid


# =================================
# 8. CHECK-OUT
# =================================

def check_out(visit_id):

    with get_connection() as conn:

        cursor = conn.execute("""
            UPDATE visits
            SET check_out = ?
            WHERE id = ?
              AND check_out IS NULL
        """, (
            current_time(),
            visit_id
        ))

        if cursor.rowcount == 0:
            raise ValueError(
                "Không tìm thấy lượt vào đang hoạt động."
            )


# =================================
# 9. KHACH DANG TRONG PHONG
# =================================

def active_visits():

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT
                v.id AS visit_id,
                c.customer_code,
                c.full_name,
                v.purpose,
                v.check_in
            FROM visits v
            JOIN customers c
                ON v.customer_id = c.id
            WHERE v.check_out IS NULL
            ORDER BY v.check_in DESC
        """).fetchall()

        return [dict(row) for row in rows]


# =================================
# 10. LICH SU RA VAO
# =================================

def visit_history(limit=100):

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT
                v.id,
                c.customer_code,
                c.full_name,
                v.purpose,
                v.check_in,
                v.check_out
            FROM visits v
            JOIN customers c
                ON v.customer_id = c.id
            ORDER BY v.id DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]


# =================================
# 11. THONG KE TONG QUAN
# =================================

def get_stats():

    today = datetime.now().astimezone().date().isoformat()

    with get_connection() as conn:

        total_customers = conn.execute("""
            SELECT COUNT(*) FROM customers
        """).fetchone()[0]

        today_visits = conn.execute("""
            SELECT COUNT(*)
            FROM visits
            WHERE substr(check_in, 1, 10) = ?
        """, (today,)).fetchone()[0]

        current_visitors = conn.execute("""
            SELECT COUNT(*)
            FROM visits
            WHERE check_out IS NULL
        """).fetchone()[0]

        return {
            "total_customers": total_customers,
            "today_visits": today_visits,
            "current_visitors": current_visitors
        }


# =================================
# 12. THONG KE THEO NGAY
# =================================

def daily_visit_stats(days=7):

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT
                substr(check_in, 1, 10) AS visit_date,
                COUNT(*) AS total_visits
            FROM visits
            WHERE date(check_in) >=
                  date('now', 'localtime', ?)
            GROUP BY substr(check_in, 1, 10)
            ORDER BY visit_date
        """, (f"-{days - 1} days",)).fetchall()

        return [dict(row) for row in rows]
