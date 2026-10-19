import json

from modules.database import ket_noi_database


RULE_TYPES = {
    "NOT_NULL",
    "UNIQUE",
    "BETWEEN",
    "MIN_VALUE",
    "MAX_VALUE",
    "ALLOWED_VALUES",
    "REGEX",
}


def them_quy_tac(dataset_id, column_name, rule_type, rule_config=None):
    """Thêm một quy tắc kiểm tra dữ liệu."""

    rule_type = rule_type.upper()

    if rule_type not in RULE_TYPES:
        raise ValueError(f"Loại quy tắc không hợp lệ: {rule_type}")

    if not column_name:
        raise ValueError("Tên cột không được để trống")

    if rule_config is None:
        rule_config = {}

    conn = ket_noi_database()
    cursor = conn.cursor()

    try:
        sql = """
            INSERT INTO quality_rules
                (dataset_id, column_name, rule_type, rule_config, is_active)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            sql,
            (
                dataset_id,
                column_name,
                rule_type,
                json.dumps(rule_config, ensure_ascii=False),
                1,
            ),
        )

        conn.commit()
        return cursor.lastrowid

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def lay_danh_sach_quy_tac(dataset_id, chi_lay_active=False):
    """Lấy các quy tắc thuộc một dataset."""

    conn = ket_noi_database()
    cursor = conn.cursor(dictionary=True)

    try:
        sql = """
            SELECT rule_id, dataset_id, column_name,
                   rule_type, rule_config, is_active
            FROM quality_rules
            WHERE dataset_id = %s
        """

        if chi_lay_active:
            sql += " AND is_active = 1"

        sql += " ORDER BY rule_id"

        cursor.execute(sql, (dataset_id,))
        rules = cursor.fetchall()

        for rule in rules:
            config = rule["rule_config"]

            if isinstance(config, str):
                rule["rule_config"] = json.loads(config)

        return rules

    finally:
        cursor.close()
        conn.close()


def cap_nhat_trang_thai_quy_tac(rule_id, is_active):
    """Bật hoặc tắt một quy tắc."""

    conn = ket_noi_database()
    cursor = conn.cursor()

    try:
        sql = """
            UPDATE quality_rules
            SET is_active = %s
            WHERE rule_id = %s
        """

        cursor.execute(sql, (int(bool(is_active)), rule_id))
        conn.commit()

        return cursor.rowcount > 0

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

