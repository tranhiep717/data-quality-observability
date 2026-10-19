
import streamlit as st
import pandas as pd

from modules.database import ket_noi_database
from modules.quality import chay_kiem_tra
from modules.alerts import (
    kiem_tra_canh_bao,
    kiem_tra_canh_bao_monitoring
)


# ==========================================
# 1. GIAO DIỆN
# ==========================================

st.title("Kiểm tra chất lượng dữ liệu")

st.write("Tải file CSV, chọn dataset và chạy kiểm tra.")


# ==========================================
# 2. LẤY DANH SÁCH DATASET
# ==========================================

def lay_datasets():
    conn = ket_noi_database()

    try:
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT dataset_id, dataset_name
                FROM datasets
                ORDER BY dataset_id
            """)

            return cursor.fetchall()

        finally:
            cursor.close()

    finally:
        conn.close()


try:
    datasets = lay_datasets()

except Exception as e:
    st.error(f"Không kết nối được MySQL: {e}")
    st.stop()


if not datasets:
    st.warning("Chưa có dataset trong MySQL.")
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
    "Chọn dataset",
    options=list(options.keys())
)

dataset_id = options[selected]


# ==========================================
# 4. UPLOAD CSV
# ==========================================

uploaded_file = st.file_uploader(
    "Chọn file CSV cần kiểm tra",
    type=["csv"]
)

if uploaded_file is not None:

    try:
        df = pd.read_csv(uploaded_file)

    except Exception as e:
        st.error(f"Không đọc được file CSV: {e}")
        st.stop()

    st.subheader("Xem trước dữ liệu")

    st.dataframe(
        df.head(20),
        width="stretch"
    )

    st.write(f"Số dòng: {len(df)}")
    st.write(f"Số cột: {len(df.columns)}")

    # ======================================
    # 5. CHẠY KIỂM TRA
    # ======================================

    if st.button(
        "Chạy kiểm tra chất lượng",
        type="primary"
    ):

        try:
            with st.spinner("Đang kiểm tra dữ liệu..."):
                result = chay_kiem_tra(
                    df,
                    dataset_id
                )

        except Exception as e:
            st.error(f"Kiểm tra thất bại: {e}")
            st.stop()

        st.success(
            "Kiểm tra và lưu MySQL thành công!"
        )

        st.metric(
            "Quality Score",
            f"{result['quality_score']:.2f}%"
        )

        st.write(f"Run ID: {result['run_id']}")

        st.subheader("Kết quả từng quy tắc")

        st.dataframe(
            pd.DataFrame(result["results"]),
            width="stretch"
        )

        # ==================================
        # 6. CẢNH BÁO CHẤT LƯỢNG
        # ==================================

        try:
            alerts = kiem_tra_canh_bao(dataset_id)

            st.subheader("Cảnh báo chất lượng")

            for message in alerts:

                if message == "Không phát hiện cảnh báo mới":
                    st.success(message)

                else:
                    st.warning(message)

        except Exception as e:
            st.error(
                "Đã lưu kết quả nhưng tạo cảnh báo "
                f"chất lượng thất bại: {e}"
            )

        # ==================================
        # 7. CẢNH BÁO MONITORING
        # ==================================

        try:
            monitoring_alerts = (
                kiem_tra_canh_bao_monitoring(
                    dataset_id
                )
            )

            st.subheader("Cảnh báo Monitoring")

            for message in monitoring_alerts:

                if message == "Không phát hiện bất thường Monitoring":
                    st.success(message)

                elif message.startswith("Cần ít nhất"):
                    st.info(message)

                else:
                    st.warning(message)

        except Exception as e:
            st.error(
                "Đã lưu kết quả nhưng tạo cảnh báo "
                f"Monitoring thất bại: {e}"
            )
