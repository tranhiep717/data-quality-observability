import re
import json

import mysql.connector
import pandas as pd

from modules.database import ket_noi_database


def doc_file_csv(file):
    """
    Đọc CSV thành DataFrame.
    Hỗ trợ đường dẫn hoặc file Streamlit upload.
    """
    try:
        df = pd.read_csv(file)

    except pd.errors.EmptyDataError as e:
        raise ValueError(
            "File CSV rỗng hoặc không có cột dữ liệu."
        ) from e

    except Exception as e:
        raise ValueError(
            f"Không thể đọc file CSV: {e}"
        ) from e

    if df.empty:
        raise ValueError(
            "File CSV không có dòng dữ liệu."
        )

    if df.columns.duplicated().any():
        raise ValueError(
            "File CSV có tên cột bị trùng."
        )

    return df


def doc_bang_mysql(ten_bang, gioi_han=10000):
    """
    Đọc dữ liệu từ bảng MySQL quản lý.

    Lưu ý: Chưa hỗ trợ MySQL nguồn ngoài.
    """

    if not re.fullmatch(r"[A-Za-z0-9_]+", ten_bang):
        raise ValueError("Tên bảng không hợp lệ.")

    if not isinstance(gioi_han, int) or not (
        1 <= gioi_han <= 100000
    ):
        raise ValueError(
            "Giới hạn phải từ 1 đến 100000."
        )

    conn = ket_noi_database()

    try:
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                f"SELECT * FROM `{ten_bang}` LIMIT %s",
                (gioi_han,)
            )

            rows = cursor.fetchall()
            columns = cursor.column_names

        finally:
            cursor.close()

        df = pd.DataFrame(
            rows,
            columns=columns
        )

        if df.empty:
            raise ValueError(
                f"Bảng '{ten_bang}' không có dữ liệu."
            )

        return df

    except ValueError:
        raise

    except Exception as e:
        raise ValueError(
            f"Không thể đọc bảng MySQL '{ten_bang}': {e}"
        ) from e

    finally:
        conn.close()


def ket_noi_mysql_nguon(
    host,
    port,
    database,
    username,
    password
):
    """
    Kết nối đến MySQL nguồn bên ngoài.
    Không thay đổi MySQL quản lý của dự án.
    """

    try:
        conn = mysql.connector.connect(
            host=host,
            port=int(port),
            database=database,
            user=username,
            password=password,
            connection_timeout=10
        )

        return conn

    except mysql.connector.Error as e:
        raise ConnectionError(
            f"Không kết nối được MySQL nguồn: {e}"
        ) from e


def lay_bang_mysql_nguon(conn):
    """Lấy danh sách bảng từ MySQL nguồn."""

    cursor = conn.cursor()

    try:
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")

        return [row[0] for row in cursor.fetchall()]

    finally:
        cursor.close()


def doc_mysql_nguon(conn, ten_bang, gioi_han=10000):
    """Đọc bảng MySQL nguồn thành DataFrame."""

    if not isinstance(ten_bang, str) or not re.fullmatch(
        r"[A-Za-z0-9_]+", ten_bang
    ):
        raise ValueError("Tên bảng không hợp lệ")

    if type(gioi_han) is not int or not 1 <= gioi_han <= 100000:
        raise ValueError("Giới hạn không hợp lệ")

    cursor = conn.cursor()

    try:
        # Xác nhận bảng thuộc danh sách mà tài khoản có thể đọc
        available_tables = lay_bang_mysql_nguon(conn)

        if ten_bang not in available_tables:
            raise ValueError(
                "Bảng không tồn tại hoặc không có quyền truy cập"
            )

        cursor.execute(
            f"SELECT * FROM `{ten_bang}` LIMIT %s",
            (gioi_han,)
        )

        rows = cursor.fetchall()
        columns = cursor.column_names

        return pd.DataFrame(rows, columns=columns)

    finally:
        cursor.close()

import re
import pandas as pd

from modules.database import ket_noi_database

def doc_bang_mysql_nguon(
    ten_database,
    ten_bang,
    gioi_han=10000
):
    """
    Đọc bảng MySQL nguồn từ database khác
    trên cùng MySQL Server.
    """

    import re
    import pandas as pd
    from modules.database import ket_noi_database

    # Kiểm tra tên database và bảng
    for ten in (ten_database, ten_bang):
        if not isinstance(ten, str) or not re.fullmatch(
            r"[A-Za-z0-9_]+", ten
        ):
            raise ValueError(
                "Tên database hoặc bảng không hợp lệ"
            )

    if type(gioi_han) is not int or not 1 <= gioi_han <= 100000:
        raise ValueError("Giới hạn không hợp lệ")

    conn = ket_noi_database()

    try:
        cursor = conn.cursor()

        try:
            query = (
                f"SELECT * FROM `{ten_database}`.`{ten_bang}` "
                "LIMIT %s"
            )

            cursor.execute(query, (gioi_han,))

            rows = cursor.fetchall()
            columns = cursor.column_names

            return pd.DataFrame(rows, columns=columns)

        finally:
            cursor.close()

    finally:
        conn.close()

def dang_ky_dataset_mysql(
    ten_database,
    ten_bang,
    ten_dataset
):
    """
    Đăng ký MySQL Source và Dataset.
    Nếu đã đăng ký cùng bảng thì trả lại dataset cũ.
    """

    import re
    import json
    from modules.database import ket_noi_database

    def hop_le(value):
        return (
            isinstance(value, str)
            and re.fullmatch(r"[A-Za-z0-9_]+", value)
        )

    if not all(hop_le(x) for x in (
        ten_database, ten_bang, ten_dataset
    )):
        raise ValueError(
            "Tên database, bảng và dataset chỉ gồm chữ, số, dấu _"
        )

    if ten_database == "data_quality_platform":
        raise ValueError(
            "Không được đăng ký database quản lý làm nguồn."
        )

    conn = ket_noi_database()
    
    # Tìm bảng MySQL đã đăng ký từ trước,
    # kể cả khi tên source khác nhau.
    cursor_check = conn.cursor(dictionary=True)

    try:
        cursor_check.execute(
            """
            SELECT d.dataset_id, d.dataset_name
            FROM datasets d
            JOIN data_sources s
                ON d.source_id = s.source_id
            WHERE s.source_type = 'MYSQL'
              AND d.table_name = %s
              AND JSON_UNQUOTE(
                  JSON_EXTRACT(
                      s.connection_config,
                      '$.database'
                  )
              ) = %s
            LIMIT 1
            """,
            (ten_bang, ten_database)
        )

        existing = cursor_check.fetchone()

        if existing:
            return {
                "dataset_id": existing["dataset_id"],
                "dataset_name": existing["dataset_name"],
                "created": False
            }

    finally:
        cursor_check.close()
        conn.close()

    # Mở lại kết nối để xử lý đăng ký mới
    conn = ket_noi_database()


    try:
        cursor = conn.cursor(dictionary=True)

        try:
            # Kiểm tra database và bảng có tồn tại
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM information_schema.tables
                WHERE table_schema = %s
                  AND table_name = %s
                  AND table_type = 'BASE TABLE'
                """,
                (ten_database, ten_bang)
            )

            if cursor.fetchone()["total"] == 0:
                raise ValueError(
                    "Bảng nguồn không tồn tại."
                )

            # Tìm nguồn đã đăng ký
            cursor.execute(
                """
                SELECT source_id
                FROM data_sources
                WHERE source_name = %s
                  AND source_type = 'MYSQL'
                LIMIT 1
                """,
                (f"MySQL: {ten_database}",)
            )

            source = cursor.fetchone()

            if source:
                source_id = source["source_id"]
            else:
                cursor.execute(
                    """
                    INSERT INTO data_sources
                        (source_name, source_type, connection_config)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        f"MySQL: {ten_database}",
                        "MYSQL",
                        json.dumps({
                            "host": "127.0.0.1",
                            "database": ten_database
                        })
                    )
                )

                source_id = cursor.lastrowid

            # Không đăng ký trùng cùng bảng
            cursor.execute(
                """
                SELECT dataset_id, dataset_name
                FROM datasets
                WHERE source_id = %s
                  AND table_name = %s
                LIMIT 1
                """,
                (source_id, ten_bang)
            )

            dataset = cursor.fetchone()

            if dataset:
                conn.commit()
                return {
                    "dataset_id": dataset["dataset_id"],
                    "dataset_name": dataset["dataset_name"],
                    "created": False
                }

            # Không dùng trùng tên với dataset khác
            cursor.execute(
                """
                SELECT dataset_id
                FROM datasets
                WHERE dataset_name = %s
                LIMIT 1
                """,
                (ten_dataset,)
            )

            if cursor.fetchone():
                raise ValueError(
                    "Tên dataset đã tồn tại. Hãy chọn tên khác."
                )

            cursor.execute(
                """
                INSERT INTO datasets
                    (source_id, dataset_name, table_name)
                VALUES (%s, %s, %s)
                """,
                (source_id, ten_dataset, ten_bang)
            )

            dataset_id = cursor.lastrowid
            conn.commit()

            return {
                "dataset_id": dataset_id,
                "dataset_name": ten_dataset,
                "created": True
            }

        finally:
            cursor.close()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def tim_dataset_mysql(ten_database, ten_bang):
    """Tìm dataset đã đăng ký theo database và bảng nguồn."""

    from modules.database import ket_noi_database

    conn = ket_noi_database()

    try:
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    d.dataset_id,
                    d.dataset_name
                FROM datasets d
                JOIN data_sources s
                    ON d.source_id = s.source_id
                WHERE s.source_type = 'MYSQL'
                  AND d.table_name = %s
                  AND JSON_UNQUOTE(
                      JSON_EXTRACT(
                          s.connection_config,
                          '$.database'
                      )
                  ) = %s
                ORDER BY d.dataset_id
                LIMIT 1
                """,
                (ten_bang, ten_database)
            )

            return cursor.fetchone()

        finally:
            cursor.close()

    finally:
        conn.close()
