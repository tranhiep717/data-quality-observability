import pandas as pd


def doc_file_csv(file):
    """
    Đọc dữ liệu từ file CSV.
    Trả về DataFrame.
    """
    try:
        df = pd.read_csv(file)

        return df

    except Exception as e:
        raise ValueError(f"Không thể đọc file CSV: {e}") from e


import re

from modules.database import ket_noi_database


def doc_bang_mysql(ten_bang):
    """
    Đọc dữ liệu từ một bảng MySQL.
    Trả về DataFrame.
    """

    if not re.fullmatch(r"[A-Za-z0-9_]+", ten_bang):
        raise ValueError("Tên bảng không hợp lệ")

    conn = ket_noi_database()

    try:
        query = f"SELECT * FROM `{ten_bang}`"

        df = pd.read_sql_query(query, conn)

        return df

    finally:
        conn.close()