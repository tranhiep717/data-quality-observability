
from mysql.connector import authentication
import streamlit as st
import pandas as pd
import time
from modules.database import ket_noi_database
from modules.ingestion import (
    doc_bang_mysql_nguon,
    dang_ky_dataset_mysql,
    tim_dataset_mysql
)
from modules.profiling import phan_tich_du_lieu
from modules.quality import chay_kiem_tra
from modules.alerts import (
    kiem_tra_canh_bao,
    kiem_tra_canh_bao_monitoring
)


st.title("MySQL Data Source")
st.write(
    "Đọc và kiểm tra chất lượng dữ liệu từ MySQL nguồn."
)

# ======================================
# 1. CHỌN DATABASE NGUỒN
# ======================================

database_name = st.selectbox(
    "Chọn database nguồn",
    ["school_management"]
)

# ======================================
# 2. LẤY DANH SÁCH BẢNG NGUỒN
# ======================================

def lay_bang_nguon(database):
    conn = ket_noi_database()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"SHOW TABLES FROM `{database}`"
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


try:
    tables = lay_bang_nguon(database_name)
except Exception as e:
    st.error(f"Không lấy được danh sách bảng: {e}")
    st.stop()

if not tables:
    st.warning("Database nguồn chưa có bảng dữ liệu.")
    st.stop()

selected_table = st.selectbox(
    "Chọn bảng dữ liệu",
    tables
)

# ======================================
# ĐĂNG KÝ MYSQL SOURCE / DATASET
# ======================================

st.subheader("Đăng ký Dataset MySQL")

with st.form("form_dang_ky_mysql"):

    ten_dataset_moi = st.text_input(
        "Tên dataset",
        value=f"{database_name}_{selected_table}"
    )

    submit_dang_ky = st.form_submit_button(
        "Đăng ký Dataset"
    )

if submit_dang_ky:
    try:
        ket_qua = dang_ky_dataset_mysql(
            ten_database=database_name,
            ten_bang=selected_table,
            ten_dataset=ten_dataset_moi
        )

        if ket_qua["created"]:
            st.success(
                "Đăng ký dataset thành công! "
                f"ID: {ket_qua['dataset_id']}"
            )
        else:
            st.info(
                "Bảng này đã được đăng ký với tên: "
                f"{ket_qua['dataset_name']} "
                f"(ID: {ket_qua['dataset_id']})"
            )

    except Exception as e:
        st.error(f"Đăng ký thất bại: {e}")

# ======================================
# 3. ĐỌC BẢNG MYSQL
# ======================================

if st.button("Đọc dữ liệu MySQL"):
    try:
        df = doc_bang_mysql_nguon(
            database_name,
            selected_table
        )

        st.session_state["mysql_source_df"] = df
        st.session_state["mysql_source_name"] = (
            database_name,
            selected_table
        )

    except Exception as e:
        st.error(f"Không đọc được dữ liệu: {e}")


source_name = (database_name, selected_table)

# Chỉ dùng dữ liệu đã đọc từ đúng bảng đang chọn
if (
    "mysql_source_df" in st.session_state
    and st.session_state.get("mysql_source_name") == source_name
):

    df = st.session_state["mysql_source_df"]

    st.success("Đọc dữ liệu MySQL thành công!")

    # ==================================
    # 4. DATA PROFILING
    # ==================================

    profiling = phan_tich_du_lieu(df)

    st.subheader("Tổng quan dữ liệu")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Số dòng",
        profiling["tong_so_dong"]
    )

    col2.metric(
        "Số cột",
        profiling["tong_so_cot"]
    )

    col3.metric(
        "Giá trị NULL",
        profiling["tong_null"]
    )

    col4.metric(
        "Dòng trùng lặp",
        profiling["tong_trung_lap"]
    )

    st.subheader("Dữ liệu mẫu")
    st.dataframe(df.head(20), width="stretch")

    st.subheader("Thống kê từng cột")

    st.dataframe(
        pd.DataFrame(profiling["thong_ke_cot"]),
        width="stretch"
    )


    # ==================================
    # 5. TỰ ĐỘNG NHẬN DIỆN DATASET MYSQL
    # ==================================

    st.subheader("Kiểm tra chất lượng dữ liệu")

    try:
        dataset = tim_dataset_mysql(
            database_name,
            selected_table
        )
    except Exception as e:
        st.error(f"Không tìm được dataset: {e}")
        st.stop()

    if dataset is None:
        st.warning(
            "Bảng này chưa được đăng ký Dataset. "
            "Hãy đăng ký ở phần phía trên trước."
        )
        st.stop()

    dataset_id = dataset["dataset_id"]

    st.success(
        f"Dataset: {dataset['dataset_name']} "
        f"(ID: {dataset_id})"
    )

    st.info(
        "Hệ thống tự động sử dụng Dataset đã đăng ký. "
        "Không cần chọn thủ công."
    )

    # ==================================
    # 6. CHẠY QUALITY ENGINE
    # ==================================

    # Kiểm tra quy tắc trước khi chạy
    from modules.rules import lay_danh_sach_quy_tac

    try:
        rules = lay_danh_sach_quy_tac(dataset_id)
    except Exception as e:
        st.error(f"Không lấy được Quality Rules: {e}")
        st.stop()

    active_rules = [
        rule for rule in rules
        if rule.get("is_active", 1)
    ]

    if not active_rules:
        st.warning(
            "Dataset chưa có quy tắc đang hoạt động. "
            "Hãy vào Quality Rules để tạo quy tắc."
        )
        st.stop()

    missing_columns = [
        rule["column_name"]
        for rule in active_rules
        if rule["column_name"] not in df.columns
    ]

    if missing_columns:
        st.error(
            "Có quy tắc tham chiếu tới cột không tồn tại: "
            + ", ".join(sorted(set(missing_columns)))
        )
        st.stop()

    st.success(
        f"Đã sẵn sàng kiểm tra với {len(active_rules)} quy tắc."
    )

    
   
    # Hạn chế chạy liên tiếp trong cùng phiên Streamlit
    key_run = f"last_run_mysql_{dataset_id}"

    lan_chay_truoc = st.session_state.get(key_run, 0)
    thoi_gian_con_lai = 5 - (time.monotonic() - lan_chay_truoc)

    if thoi_gian_con_lai > 0:
        st.info(
            f"Vui lòng chờ khoảng "
            f"{thoi_gian_con_lai:.0f} giây trước khi chạy lại."
        )

    if st.button(
        "Chạy kiểm tra chất lượng MySQL",
        type="primary",
        disabled=thoi_gian_con_lai > 0
    ):
       
        try:
            # Đọc lại dữ liệu mới nhất từ MySQL
            df_moi = doc_bang_mysql_nguon(
                database_name,
                selected_table
            )

            # Không chạy với dữ liệu rỗng
            if df_moi.empty:
                st.warning(
                    "Bảng MySQL không có dữ liệu để kiểm tra."
                )
                st.stop()

            # Kiểm tra lại cột theo dữ liệu mới nhất
            missing_columns = [
                rule["column_name"]
                for rule in active_rules
                if rule["column_name"] not in df_moi.columns
            ]

            if missing_columns:
                st.error(
                    "Dữ liệu mới thiếu các cột có quy tắc: "
                    + ", ".join(
                        sorted(set(missing_columns))
                    )
                )
                st.stop()

            # Chạy Quality Engine
            result = chay_kiem_tra(
                df_moi,
                dataset_id
            )

            # Cập nhật DataFrame trong session
            st.session_state["mysql_source_df"] = df_moi

        except Exception as e:
            st.error(f"Kiểm tra thất bại: {e}")
        
        else:
            st.session_state[key_run] = time.monotonic()
            st.success(
                "Đã kiểm tra dữ liệu MySQL mới nhất!"
            )

            st.write(
                "Run ID:",
                result["run_id"]
            )

            st.metric(
                "Quality Score",
                f"{result['quality_score']:.2f}%"
            )

            st.dataframe(
                pd.DataFrame(result["results"]),
                width="stretch"
            )

            # Tạo cảnh báo
            try:
                kiem_tra_canh_bao(dataset_id)
                kiem_tra_canh_bao_monitoring(dataset_id)

                st.success("Đã cập nhật Monitoring và Alerts.")

            except Exception as e:
                st.warning(
                    "Đã lưu Quality Check nhưng cập nhật "
                    f"cảnh báo gặp lỗi: {e}"
                )