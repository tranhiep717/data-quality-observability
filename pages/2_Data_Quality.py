import streamlit as st
import pandas as pd

from modules.database import ket_noi_database
from modules.ingestion import doc_csv_da_dang_ky
from modules.quality import chay_kiem_tra
from modules.alerts import (
    kiem_tra_canh_bao,
    kiem_tra_canh_bao_monitoring,
)

st.title("Kiểm tra chất lượng dữ liệu")
st.write("Chọn dataset CSV đã đăng ký và chạy kiểm tra, không cần tải lại file.")


def lay_datasets_csv():
    """Chỉ lấy dataset CSV vì trang MySQL Source xử lý nguồn MySQL riêng."""
    conn = ket_noi_database()
    try:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT d.dataset_id, d.dataset_name, d.file_path
                FROM datasets AS d
                JOIN data_sources AS s ON d.source_id = s.source_id
                WHERE UPPER(s.source_type) = 'CSV'
                ORDER BY d.dataset_id
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        conn.close()


def dem_quy_tac_bat(dataset_id):
    conn = ket_noi_database()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM quality_rules
                WHERE dataset_id = %s AND is_active = 1
            """, (dataset_id,))
            return cursor.fetchone()[0]
        finally:
            cursor.close()
    finally:
        conn.close()


try:
    datasets = lay_datasets_csv()
except Exception as e:
    st.error(f"Không kết nối được MySQL: {e}")
    st.stop()

if not datasets:
    st.warning("Chưa có dataset CSV. Hãy đăng ký tại trang Datasets.")
    st.stop()

options = {
    f"{d['dataset_name']} (ID {d['dataset_id']})": d
    for d in datasets
}
selected = st.selectbox("Chọn dataset CSV", options=list(options.keys()))
dataset = options[selected]
dataset_id = dataset["dataset_id"]

st.subheader("Dữ liệu CSV đã đăng ký")
try:
    df = doc_csv_da_dang_ky(dataset["file_path"])
except Exception as e:
    st.error(f"Không đọc được CSV của dataset này: {e}")
    st.info(
        "Với dataset đăng ký theo phiên bản cũ, hãy kiểm tra file_path "
        "trong MySQL và gắn lại file nguồn đúng. Không chọn file khác "
        "để chạy dưới cùng dataset_id."
    )
    st.stop()

st.success("Đã đọc CSV từ nguồn đã đăng ký, không cần upload lại.")
c1, c2 = st.columns(2)
c1.metric("Số dòng", len(df))
c2.metric("Số cột", len(df.columns))
st.dataframe(df.head(20), use_container_width=True)
st.caption("Các cột: " + ", ".join(map(str, df.columns)))

try:
    active_rules = dem_quy_tac_bat(dataset_id)
except Exception as e:
    st.error(f"Không lấy được Quality Rules: {e}")
    st.stop()

if active_rules == 0:
    st.warning("Dataset chưa có quy tắc đang bật. Hãy tạo/bật rule ở trang Quality Rules.")

if st.button("Chạy kiểm tra chất lượng", type="primary", disabled=active_rules == 0):
    try:
        # Đọc lại lần nữa ngay tại thời điểm nhấn để không dùng dữ liệu cũ.
        df_to_check = doc_csv_da_dang_ky(dataset["file_path"])
        with st.spinner("Đang kiểm tra dữ liệu..."):
            result = chay_kiem_tra(df_to_check, dataset_id)
    except Exception as e:
        st.error(f"Kiểm tra thất bại: {e}")
        st.stop()

    st.success("Kiểm tra và lưu MySQL thành công!")
    st.metric("Quality Score", f"{result['quality_score']:.2f}%")
    st.write(f"Run ID: {result['run_id']}")
    st.subheader("Kết quả từng quy tắc")
    st.dataframe(pd.DataFrame(result["results"]), use_container_width=True)

    try:
        alerts = kiem_tra_canh_bao(dataset_id)
        st.subheader("Cảnh báo chất lượng")
        for message in alerts:
            if message == "Không phát hiện cảnh báo mới":
                st.success(message)
            else:
                st.warning(message)
    except Exception as e:
        st.error("Đã lưu kết quả nhưng tạo cảnh báo chất lượng thất bại: " + str(e))

    try:
        monitoring_alerts = kiem_tra_canh_bao_monitoring(dataset_id)
        st.subheader("Cảnh báo Monitoring")
        for message in monitoring_alerts:
            if message == "Không phát hiện bất thường Monitoring":
                st.success(message)
            elif message.startswith("Cần ít nhất"):
                st.info(message)
            else:
                st.warning(message)
    except Exception as e:
        st.error("Đã lưu kết quả nhưng tạo cảnh báo Monitoring thất bại: " + str(e))
