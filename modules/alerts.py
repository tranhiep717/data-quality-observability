
from modules.database import ket_noi_database
from modules.monitoring import (
    so_sanh_lan_chay,
    so_sanh_metrics
)


# ==========================================
# 1. TẠO VÀ LƯU CẢNH BÁO
# ==========================================

def tao_canh_bao(
    run_id, dataset_id,
    alert_type, severity, message
):
    conn = ket_noi_database()
    cursor = conn.cursor()

    try:
        # Tránh trùng cảnh báo cùng loại trong một Run
        cursor.execute("""
            SELECT alert_id
            FROM alerts
            WHERE run_id = %s
              AND alert_type = %s
            LIMIT 1
        """, (run_id, alert_type))

        existing = cursor.fetchone()

        if existing:
            return existing[0]

        cursor.execute("""
            INSERT INTO alerts
                (run_id, dataset_id, alert_type,
                 severity, message)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            run_id,
            dataset_id,
            alert_type,
            severity,
            message
        ))

        conn.commit()
        return cursor.lastrowid

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


# ==========================================
# 2. CẢNH BÁO CHẤT LƯỢNG
# ==========================================

def kiem_tra_canh_bao(dataset_id):
    conn = ket_noi_database()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT run_id, quality_score
            FROM pipeline_runs
            WHERE dataset_id = %s
              AND status = 'SUCCESS'
            ORDER BY started_at DESC, run_id DESC
            LIMIT 1
        """, (dataset_id,))

        latest = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if latest is None or latest["quality_score"] is None:
        return ["Chưa có kết quả kiểm tra thành công"]

    run_id = latest["run_id"]
    score = float(latest["quality_score"])
    messages = []

    # Cảnh báo điểm chất lượng thấp
    if score < 70:
        severity = "CRITICAL"
    elif score < 90:
        severity = "WARNING"
    else:
        severity = None

    if severity:
        message = f"Quality Score thấp: {score}%"

        tao_canh_bao(
            run_id, dataset_id,
            "LOW_QUALITY", severity, message
        )

        messages.append(message)

    # Cảnh báo chất lượng giảm
    comparison = so_sanh_lan_chay(dataset_id)

    if "difference" in comparison:
        difference = comparison["difference"]

        if difference <= -10:
            message = (
                f"Chất lượng dữ liệu giảm "
                f"{abs(difference)} điểm phần trăm"
            )

            tao_canh_bao(
                run_id, dataset_id,
                "QUALITY_DROP", "WARNING", message
            )

            messages.append(message)

    if not messages:
        messages.append("Không phát hiện cảnh báo mới")

    return messages


# ==========================================
# 3. CẢNH BÁO MONITORING
# ==========================================

def kiem_tra_canh_bao_monitoring(dataset_id):
    metrics = so_sanh_metrics(dataset_id)

    if "message" in metrics:
        return [metrics["message"]]

    run_id = metrics["current_run"]
    messages = []

    # A. SCHEMA DRIFT
    added = metrics["added_columns"]
    removed = metrics["removed_columns"]
    changed = metrics["changed_types"]

    if added or removed or changed:
        # Mất cột là nghiêm trọng hơn thêm cột
        severity = (
            "CRITICAL" if removed else "WARNING"
        )

        message = (
            "Phát hiện Schema Drift. "
            f"Cột mới: {added}; "
            f"Cột bị xóa: {removed}; "
            f"Kiểu dữ liệu thay đổi: {changed}"
        )

        tao_canh_bao(
            run_id,
            dataset_id,
            "SCHEMA_DRIFT",
            severity,
            message
        )

        messages.append(message)

    # B. NULL INCREASE
    null_difference = metrics["null_difference"]

    if null_difference > 0:
        message = (
            f"Số giá trị NULL tăng "
            f"{null_difference} so với lần trước"
        )

        tao_canh_bao(
            run_id,
            dataset_id,
            "NULL_INCREASE",
            "WARNING",
            message
        )

        messages.append(message)

    # C. VOLUME DROP
    change_percent = metrics["row_change_percent"]

    # Cảnh báo khi số dòng giảm ít nhất 20%
    if (
        change_percent is not None
        and change_percent <= -20
    ):
        previous_rows = metrics["previous_row_count"]
        current_rows = metrics["current_row_count"]

        message = (
            "Số lượng bản ghi giảm bất thường. "
            f"Trước: {previous_rows} dòng; "
            f"Hiện tại: {current_rows} dòng; "
            f"Thay đổi: {change_percent}%"
        )

        tao_canh_bao(
            run_id,
            dataset_id,
            "VOLUME_DROP",
            "WARNING",
            message
        )

        messages.append(message)

    if not messages:
        messages.append(
            "Không phát hiện bất thường Monitoring"
        )

    return messages


# ==========================================
# 4. CẬP NHẬT TRẠNG THÁI CẢNH BÁO
# ==========================================

def cap_nhat_canh_bao(alert_id, is_resolved=True):
    conn = ket_noi_database()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT alert_id, is_resolved
            FROM alerts
            WHERE alert_id = %s
        """, (alert_id,))

        alert = cursor.fetchone()

        if alert is None:
            raise ValueError(
                f"Không tìm thấy cảnh báo ID {alert_id}"
            )

        cursor.execute("""
            UPDATE alerts
            SET is_resolved = %s
            WHERE alert_id = %s
        """, (bool(is_resolved), alert_id))

        conn.commit()
        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()
