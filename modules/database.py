
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def ket_noi_database():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "data_quality_platform")
    )

def kiem_tra_ket_noi():
    conn = ket_noi_database()

    try:
        cursor = conn.cursor()
        try:
            cursor.execute("SHOW TABLES")
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
    finally:
        conn.close()
def tao_lan_chay(dataset_id):
    conn = ket_noi_database()
    cursor = conn.cursor()

    try:
        sql = """
            INSERT INTO pipeline_runs (dataset_id, status)
            VALUES (%s, 'RUNNING')
        """
        cursor.execute(sql, (dataset_id,))
        conn.commit()

        return cursor.lastrowid

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def hoan_thanh_lan_chay(run_id, total_rows, quality_score):
    conn = ket_noi_database()
    cursor = conn.cursor()

    try:
        sql = """
            UPDATE pipeline_runs
            SET finished_at = CURRENT_TIMESTAMP,
                status = 'SUCCESS',
                total_rows = %s,
                quality_score = %s
            WHERE run_id = %s
        """
        cursor.execute(sql, (total_rows, quality_score, run_id))
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def luu_ket_qua(run_id, rule_id, checked_rows, failed_rows):
    conn = ket_noi_database()
    cursor = conn.cursor()

    try:
        pass_rate = (
            (checked_rows - failed_rows) / checked_rows * 100
            if checked_rows > 0 else 100
        )

        status = "PASS" if failed_rows == 0 else "FAIL"

        sql = """
            INSERT INTO quality_results
            (run_id, rule_id, checked_rows,
             failed_rows, pass_rate, result_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            run_id, rule_id, checked_rows,
            failed_rows, round(pass_rate, 2), status
        ))

        conn.commit()
        return cursor.lastrowid

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

