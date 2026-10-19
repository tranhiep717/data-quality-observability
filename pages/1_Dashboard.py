
import pandas as pd
import plotly.express as px
import streamlit as st

from modules.database import ket_noi_database


st.title("Data Quality Dashboard")
st.write("Giám sát chất lượng dữ liệu theo từng Dataset.")


# ==========================================
# 1. HÀM TRUY VẤN MYSQL
# ==========================================

def truy_van(sql, params=()):
    conn = ket_noi_database()

    try:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        conn.close()


# ==========================================
# 2. LẤY DANH SÁCH DATASET
# ==========================================

try:
    datasets = truy_van("""
        SELECT
            d.dataset_id,
            d.dataset_name,
            s.source_type
        FROM datasets d
        JOIN data_sources s
            ON d.source_id = s.source_id
        ORDER BY d.dataset_id
    """)
except Exception as e:
    st.error(f"Không thể kết nối MySQL: {e}")
    st.stop()

if not datasets:
    st.warning("Chưa có Dataset nào.")
    st.stop()


# ==========================================
# 3. CHỌN DATASET
# ==========================================

options = {
    f"{d['dataset_name']} (ID {d['dataset_id']})":
    d["dataset_id"]
    for d in datasets
}

selected = st.selectbox(
    "Chọn Dataset cần giám sát",
    list(options.keys())
)

dataset_id = options[selected]

if st.button("Làm mới dữ liệu"):
    st.rerun()


# ==========================================
# 4. LẤY KẾT QUẢ MYSQL
# ==========================================

try:
    runs = truy_van("""
        SELECT
            run_id,
            started_at,
            finished_at,
            status,
            total_rows,
            quality_score
        FROM pipeline_runs
        WHERE dataset_id = %s
        ORDER BY started_at ASC, run_id ASC
    """, (dataset_id,))

    alerts = truy_van("""
        SELECT
            alert_id,
            run_id,
            alert_type,
            severity,
            message,
            is_resolved,
            created_at
        FROM alerts
        WHERE dataset_id = %s
        ORDER BY created_at DESC, alert_id DESC
    """, (dataset_id,))

    rule_results = truy_van("""
        SELECT
            qr.run_id,
            r.column_name,
            r.rule_type,
            qr.checked_rows,
            qr.failed_rows,
            qr.pass_rate,
            qr.result_status
        FROM quality_results qr
        JOIN pipeline_runs pr
            ON qr.run_id = pr.run_id
        JOIN quality_rules r
            ON qr.rule_id = r.rule_id
        WHERE pr.dataset_id = %s
        ORDER BY qr.run_id DESC, qr.result_id DESC
    """, (dataset_id,))

except Exception as e:
    st.error(f"Lỗi tải dữ liệu: {e}")
    st.stop()


# ==========================================
# 5. THỐNG KÊ TỔNG QUAN
# ==========================================

df_runs = pd.DataFrame(runs)

if df_runs.empty:
    st.info(
        "Dataset này chưa có lần kiểm tra nào. "
        "Hãy vào trang Data Quality để chạy kiểm tra."
    )
    st.stop()

success_runs = df_runs[
    df_runs["status"] == "SUCCESS"
].copy()

if success_runs.empty:
    st.warning("Chưa có lần kiểm tra thành công.")
    st.dataframe(df_runs, width="stretch")
    st.stop()

latest = success_runs.iloc[-1]

score = float(latest["quality_score"])

previous_score = None

if len(success_runs) >= 2:
    previous_score = float(
        success_runs.iloc[-2]["quality_score"]
    )

st.subheader("Tổng quan chất lượng dữ liệu")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Quality Score",
        f"{score:.2f}%",
        delta=(
            f"{score - previous_score:+.2f} điểm %"
            if previous_score is not None
            else None
        )
    )

with col2:
    st.metric("Tổng lần chạy", len(df_runs))

with col3:
    st.metric("Số dòng dữ liệu", int(latest["total_rows"]))

with col4:
    active_alerts = sum(
        not bool(a["is_resolved"])
        for a in alerts
    )
    st.metric("Cảnh báo chưa xử lý", active_alerts)


# ==========================================
# 6. BIỂU ĐỒ QUALITY SCORE
# ==========================================

st.divider()
st.subheader("Lịch sử Quality Score")

chart_df = success_runs.copy()

chart_df["quality_score"] = pd.to_numeric(
    chart_df["quality_score"]
)

chart_df["run_label"] = (
    "Run " + chart_df["run_id"].astype(str)
)

fig = px.line(
    chart_df,
    x="run_label",
    y="quality_score",
    markers=True,
    labels={
        "run_label": "Lần kiểm tra",
        "quality_score": "Quality Score (%)"
    }
)

fig.update_yaxes(range=[0, 100])

fig.update_layout(
    hovermode="x unified"
)

st.plotly_chart(fig, width="stretch")


# ==========================================
# 7. KẾT QUẢ THEO QUY TẮC
# ==========================================

st.divider()
st.subheader("Kết quả kiểm tra theo quy tắc")

latest_run_id = int(latest["run_id"])

latest_rules = [
    r for r in rule_results
    if r["run_id"] == latest_run_id
]

if latest_rules:
    df_rules = pd.DataFrame(latest_rules)

    st.dataframe(
        df_rules,
        width="stretch",
        hide_index=True
    )

    fig_rules = px.bar(
        df_rules,
        x="column_name",
        y="failed_rows",
        color="rule_type",
        barmode="group",
        labels={
            "column_name": "Cột dữ liệu",
            "failed_rows": "Số lỗi",
            "rule_type": "Quy tắc"
        },
        title="Số lỗi theo từng quy tắc"
    )

    st.plotly_chart(
        fig_rules,
        width="stretch"
    )
else:
    st.info("Chưa có kết quả quy tắc.")


# ==========================================
# 8. LỊCH SỬ KIỂM TRA
# ==========================================

st.divider()
st.subheader("Lịch sử các lần kiểm tra")

st.dataframe(
    df_runs.sort_values("run_id", ascending=False),
    width="stretch",
    hide_index=True
)


# ==========================================
# 9. DANH SÁCH CẢNH BÁO
# ==========================================

st.divider()
st.subheader("Danh sách cảnh báo")

if alerts:
    df_alerts = pd.DataFrame(alerts)

    severity = st.multiselect(
        "Lọc theo mức độ",
        ["INFO", "WARNING", "CRITICAL"],
        default=["INFO", "WARNING", "CRITICAL"]
    )

    filtered = df_alerts[
        df_alerts["severity"].isin(severity)
    ]

    st.dataframe(
        filtered,
        width="stretch",
        hide_index=True
    )

else:
    st.success("Dataset chưa có cảnh báo.")


st.divider()
st.caption(
    "Data Quality & Observability Platform "
    "| MySQL + Streamlit + Plotly"
)

# ==========================================
# QUẢN LÝ TRẠNG THÁI CẢNH BÁO
# ==========================================

from modules.alerts import cap_nhat_canh_bao

st.divider()
st.subheader("Xử lý cảnh báo")

if alerts:
    alert_options = {
        f"ID {a['alert_id']} - {a['severity']} - "
        f"{a['message']}": a
        for a in alerts
    }

    selected_alert = st.selectbox(
        "Chọn cảnh báo",
        list(alert_options.keys())
    )

    current_alert = alert_options[selected_alert]

    st.write(
        "Trạng thái hiện tại:",
        "Đã xử lý" if current_alert["is_resolved"]
        else "Chưa xử lý"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Đánh dấu đã xử lý"):
            try:
                cap_nhat_canh_bao(
                    current_alert["alert_id"], True
                )
                st.success("Đã cập nhật cảnh báo!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    with col2:
        if st.button("Mở lại cảnh báo"):
            try:
                cap_nhat_canh_bao(
                    current_alert["alert_id"], False
                )
                st.success("Đã mở lại cảnh báo!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

else:
    st.info("Không có cảnh báo để xử lý.")

# ==========================================
# MONITORING NÂNG CAO
# ==========================================

from modules.monitoring import so_sanh_metrics

st.divider()
st.subheader("Giám sát biến động dữ liệu")

try:
    metrics = so_sanh_metrics(dataset_id)

    if "message" in metrics:
        st.info(metrics["message"])

    else:
        st.caption(
            f"So sánh Run {metrics['previous_run']} "
            f"và Run {metrics['current_run']}"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Thay đổi số dòng",
                metrics["row_difference"]
            )

        with col2:
            st.metric(
                "Thay đổi NULL",
                metrics["null_difference"]
            )

        with col3:
            st.metric(
                "Thay đổi trùng lặp",
                metrics["duplicate_difference"]
            )

        with col4:
            st.metric(
                "Thay đổi số cột",
                metrics["column_difference"]
            )

        st.subheader("Phát hiện Schema Drift")

        if (
            metrics["added_columns"]
            or metrics["removed_columns"]
            or metrics["changed_types"]
        ):
            st.warning("Phát hiện thay đổi cấu trúc dữ liệu!")

            if metrics["added_columns"]:
                st.write(
                    "Cột mới:",
                    metrics["added_columns"]
                )

            if metrics["removed_columns"]:
                st.write(
                    "Cột bị xóa:",
                    metrics["removed_columns"]
                )

            if metrics["changed_types"]:
                st.write(
                    "Kiểu dữ liệu thay đổi:",
                    metrics["changed_types"]
                )

        else:
            st.success(
                "Không phát hiện thay đổi cấu trúc dữ liệu."
            )

except Exception as e:
    st.error(f"Lỗi Monitoring: {e}")

