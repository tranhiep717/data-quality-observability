
import json

from modules.database import ket_noi_database


def chay_kiem_tra(df, dataset_id):
    """
    Điều phối kiểm tra chất lượng và lưu kết quả MySQL.

    Quality Engine: Người 1
    Database & Monitoring: Người 2
    """

    # Import tại đây để lỗi chỉ xuất hiện khi chạy kiểm tra,
    # không làm hỏng Dashboard nếu chưa ghép code Người 1.
    from modules.quality_engine import (
        chay_quality_engine,
        tinh_quality_score
    )

    conn = ket_noi_database()
    cursor = conn.cursor(dictionary=True)
    run_id = None

    try:
        # 1. Lấy quy tắc kiểm tra từ MySQL
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

        # Chuyển JSON sang dictionary cho Quality Engine
        for rule in rules:
            config = rule["rule_config"]

            if isinstance(config, str):
                config = json.loads(config)

            rule["rule_config"] = config or {}

        # 2. Tạo lịch sử lần chạy
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

        # 4. Lưu kết quả từng quy tắc vào MySQL
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

        # 5. Lưu Metrics phục vụ Monitoring
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

        # 6. Hoàn tất lần chạy
        cursor.execute("""
            UPDATE pipeline_runs
            SET
                status = 'SUCCESS',
                quality_score = %s,
                finished_at = CURRENT_TIMESTAMP
            WHERE run_id = %s
        """, (score, run_id))

        conn.commit()

        # 7. Trả kết quả cho giao diện Streamlit
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
