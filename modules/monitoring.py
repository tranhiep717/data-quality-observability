
import json
import pandas as pd

from modules.database import ket_noi_database


def lay_lich_su(dataset_id):
    """Lấy lịch sử các lần kiểm tra."""
    conn = ket_noi_database()

    try:
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    run_id,
                    dataset_id,
                    started_at,
                    finished_at,
                    status,
                    total_rows,
                    quality_score
                FROM pipeline_runs
                WHERE dataset_id = %s
                ORDER BY started_at ASC, run_id ASC
            """, (dataset_id,))

            rows = cursor.fetchall()
            return pd.DataFrame(rows)

        finally:
            cursor.close()

    finally:
        conn.close()


def so_sanh_lan_chay(dataset_id):
    """So sánh Quality Score giữa hai Run thành công."""
    df = lay_lich_su(dataset_id)

    if df.empty:
        return {"message": "Chưa có lịch sử kiểm tra"}

    df = df[df["status"] == "SUCCESS"].copy()

    if len(df) < 2:
        return {
            "message": "Cần ít nhất 2 lần chạy thành công để so sánh"
        }

    previous = df.iloc[-2]
    current = df.iloc[-1]

    old_score = float(previous["quality_score"])
    new_score = float(current["quality_score"])

    return {
        "previous_run": int(previous["run_id"]),
        "current_run": int(current["run_id"]),
        "previous_score": old_score,
        "current_score": new_score,
        "difference": round(new_score - old_score, 2)
    }


def so_sanh_metrics(dataset_id):
    """So sánh Volume, NULL, Duplicate và Schema."""
    conn = ket_noi_database()

    try:
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    dm.run_id,
                    dm.row_count,
                    dm.column_count,
                    dm.null_count,
                    dm.duplicate_count,
                    dm.schema_snapshot
                FROM dataset_metrics dm
                JOIN pipeline_runs pr
                    ON dm.run_id = pr.run_id
                WHERE dm.dataset_id = %s
                  AND pr.status = 'SUCCESS'
                ORDER BY pr.started_at DESC, pr.run_id DESC
                LIMIT 2
            """, (dataset_id,))

            rows = cursor.fetchall()

        finally:
            cursor.close()

    finally:
        conn.close()

    if len(rows) < 2:
        return {
            "message": "Cần ít nhất 2 lần chạy để so sánh"
        }

    current = rows[0]
    previous = rows[1]

    def parse_schema(value):
        if isinstance(value, str):
            return json.loads(value)
        return value or {}

    old_schema = parse_schema(previous["schema_snapshot"])
    new_schema = parse_schema(current["schema_snapshot"])

    old_columns = set(old_schema)
    new_columns = set(new_schema)

    changed_types = {
        col: {
            "old": old_schema[col],
            "new": new_schema[col]
        }
        for col in old_columns & new_columns
        if old_schema[col] != new_schema[col]
    }

    previous_rows = int(previous["row_count"])
    current_rows = int(current["row_count"])

    row_difference = current_rows - previous_rows

    # Tránh chia cho 0 khi Run trước có 0 dòng
    if previous_rows > 0:
        row_change_percent = round(
            row_difference / previous_rows * 100,
            2
        )
    else:
        row_change_percent = None

    return {
        "previous_run": int(previous["run_id"]),
        "current_run": int(current["run_id"]),

        "previous_row_count": previous_rows,
        "current_row_count": current_rows,
        "row_difference": row_difference,
        "row_change_percent": row_change_percent,

        "null_difference": (
            int(current["null_count"])
            - int(previous["null_count"])
        ),

        "duplicate_difference": (
            int(current["duplicate_count"])
            - int(previous["duplicate_count"])
        ),

        "column_difference": (
            int(current["column_count"])
            - int(previous["column_count"])
        ),

        "added_columns": sorted(
            new_columns - old_columns
        ),

        "removed_columns": sorted(
            old_columns - new_columns
        ),

        "changed_types": changed_types
    }
