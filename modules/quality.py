
import json
import pandas as pd

from modules.database import ket_noi_database


# ==========================================
# NGƯỜI 1 - QUALITY ENGINE
# ==========================================

def kiem_tra_quy_tac(
    df, column_name, rule_type, rule_config=None
):
    """Kiểm tra một quy tắc chất lượng dữ liệu."""

    if rule_config is None:
        rule_config = {}

    if column_name not in df.columns:
        raise ValueError(
            f"Cột '{column_name}' không tồn tại"
        )

    series = df[column_name]

    if rule_type == "NOT_NULL":
        failed = series.isna()

    elif rule_type == "UNIQUE":
        failed = series.duplicated(keep="first")

    elif rule_type == "BETWEEN":
        min_value = rule_config["min"]
        max_value = rule_config["max"]

        values = pd.to_numeric(
            series, errors="coerce"
        )

        failed = (
            values.isna()
            | (values < min_value)
            | (values > max_value)
        )

    elif rule_type == "MIN_VALUE":
        min_value = rule_config["min"]

        values = pd.to_numeric(
            series, errors="coerce"
        )

        failed = values.isna() | (values < min_value)

    elif rule_type == "MAX_VALUE":
        max_value = rule_config["max"]

        values = pd.to_numeric(
            series, errors="coerce"
        )

        failed = values.isna() | (values > max_value)

    elif rule_type == "ALLOWED_VALUES":
        allowed = rule_config["values"]

        failed = ~series.isin(allowed)

    elif rule_type == "REGEX":
        pattern = rule_config["pattern"]

        failed = ~series.astype(
            "string"
        ).str.fullmatch(
            pattern,
            na=False
        )

    else:
        raise ValueError(
            f"Quy tắc không được hỗ trợ: {rule_type}"
        )

    checked_rows = len(df)
    failed_rows = int(failed.sum())

    pass_rate = (
        round(
            (checked_rows - failed_rows)
            / checked_rows * 100,
            2
        )
        if checked_rows > 0
        else 100.0
    )

    return {
        "column_name": column_name,
        "rule_type": rule_type,
        "checked_rows": checked_rows,
        "failed_rows": failed_rows,
        "pass_rate": pass_rate,
        "result_status": (
            "PASS" if failed_rows == 0 else "FAIL"
        )
    }


def chay_quality_engine(df, rules):
    """Chạy tất cả quy tắc đang hoạt động."""

    ket_qua = []

    for rule in rules:

        if not rule["is_active"]:
            continue

        result = kiem_tra_quy_tac(
            df=df,
            column_name=rule["column_name"],
            rule_type=rule["rule_type"],
            rule_config=rule["rule_config"]
        )

        result["rule_id"] = rule["rule_id"]

        ket_qua.append(result)

    return ket_qua


def tinh_quality_score(ket_qua):
    """Tính trung bình tỷ lệ đạt các quy tắc."""

    if not ket_qua:
        return 0.0

    tong_diem = sum(
        result["pass_rate"]
        for result in ket_qua
    )

    return round(tong_diem / len(ket_qua), 2)


# ==========================================
# NGƯỜI 2 - DATABASE & MONITORING
# ==========================================

def chay_kiem_tra(df, dataset_id):
    """
    Điều phối Quality Engine của Người 1
    và lưu kết quả vào MySQL của Người 2.
    """

    conn = ket_noi_database()
    cursor = conn.cursor(dictionary=True)
    run_id = None

    try:
        # 1. Lấy quy tắc từ MySQL
        cursor.execute("""
            SELECT
                rule_id,
                column_name,
                rule_type,
                rule_config,
                is_active
            FROM quality_rules
            WHERE dataset_id = %s
              AND is_active = 1
            ORDER BY rule_id
        """, (dataset_id,))

        rules = cursor.fetchall()

        if not rules:
            raise ValueError(
                "Dataset chưa có quy tắc kiểm tra"
            )

        # Chuyển cấu hình JSON sang dictionary
        for rule in rules:
            config = rule["rule_config"]

            if isinstance(config, str):
                config = json.loads(config)

            rule["rule_config"] = config or {}

        # 2. Tạo Pipeline Run
        cursor.execute("""
            INSERT INTO pipeline_runs
                (dataset_id, status, total_rows)
            VALUES (%s, 'RUNNING', %s)
        """, (dataset_id, len(df)))

        run_id = cursor.lastrowid
        conn.commit()

        # 3. Gọi Quality Engine của Người 1
        results = chay_quality_engine(df, rules)

        score = tinh_quality_score(results)

        # 4. Lưu kết quả từng quy tắc
        for result in results:
            cursor.execute("""
                INSERT INTO quality_results
                (
                    run_id,
                    rule_id,
                    checked_rows,
                    failed_rows,
                    pass_rate,
                    result_status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                run_id,
                result["rule_id"],
                result["checked_rows"],
                result["failed_rows"],
                result["pass_rate"],
                result["result_status"]
            ))

        # 5. Lưu Dataset Metrics
        schema_snapshot = {
            column: str(dtype)
            for column, dtype in df.dtypes.items()
        }

        cursor.execute("""
            INSERT INTO dataset_metrics
            (
                run_id,
                dataset_id,
                row_count,
                column_count,
                schema_snapshot,
                null_count,
                duplicate_count
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            run_id,
            dataset_id,
            len(df),
            len(df.columns),
            json.dumps(schema_snapshot),
            int(df.isna().sum().sum()),
            int(df.duplicated().sum())
        ))

        # 6. Cập nhật trạng thái SUCCESS
        cursor.execute("""
            UPDATE pipeline_runs
            SET
                status = 'SUCCESS',
                quality_score = %s,
                finished_at = CURRENT_TIMESTAMP
            WHERE run_id = %s
        """, (score, run_id))

        conn.commit()

        # 7. Trả dữ liệu cho Streamlit
        display_results = [
            {
                "column": result["column_name"],
                "rule": result["rule_type"],
                "failed_rows": result["failed_rows"],
                "pass_rate": result["pass_rate"]
            }
            for result in results
        ]

        return {
            "run_id": run_id,
            "dataset_id": dataset_id,
            "quality_score": score,
            "total_rows": len(df),
            "results": display_results
        }

    except Exception as error:
        conn.rollback()

        if run_id is not None:
            try:
                cursor.execute("""
                    UPDATE pipeline_runs
                    SET
                        status = 'FAILED',
                        finished_at = CURRENT_TIMESTAMP,
                        error_message = %s
                    WHERE run_id = %s
                """, (str(error), run_id))

                conn.commit()

            except Exception:
                conn.rollback()

        raise

    finally:
        cursor.close()
        conn.close()
