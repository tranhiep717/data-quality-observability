
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

from modules.database import ket_noi_database


# ==========================================
# 1. CẤU HÌNH
# ==========================================

st.title("Quản lý Dataset")

st.write(
    "Đăng ký và quản lý nhiều bộ dữ liệu CSV "
    "trong hệ thống Data Quality Platform."
)

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. HÀM LẤY DANH SÁCH DATASET
# ==========================================

def lay_datasets():
    conn = ket_noi_database()

    try:
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    d.dataset_id,
                    d.dataset_name,
                    d.file_path,
                    d.created_at,
                    s.source_name,
                    s.source_type
                FROM datasets d
                JOIN data_sources s
                    ON d.source_id = s.source_id
                ORDER BY d.dataset_id DESC
            """)

            return cursor.fetchall()

        finally:
            cursor.close()

    finally:
        conn.close()


# ==========================================
# 3. HÀM ĐĂNG KÝ DATASET
# ==========================================

def dang_ky_dataset(dataset_name, uploaded_file):

    dataset_name = dataset_name.strip()

    if not dataset_name:
        raise ValueError(
            "Tên dataset không được để trống."
        )

    conn = None
    cursor = None
    saved_path = None

    try:
        conn = ket_noi_database()
        cursor = conn.cursor()

        # Kiểm tra dataset trùng tên
        cursor.execute("""
            SELECT dataset_id
            FROM datasets
            WHERE dataset_name = %s
            LIMIT 1
        """, (dataset_name,))

        existing = cursor.fetchone()

        if existing:
            return {
                "success": False,
                "message": (
                    "Dataset này đã tồn tại! "
                    "Vui lòng chọn tên khác."
                )
            }

        # Kiểm tra định dạng file
        original_name = Path(uploaded_file.name).name

        if Path(original_name).suffix.lower() != ".csv":
            raise ValueError(
                "Chỉ hỗ trợ file CSV."
            )

        # Tạo tên file duy nhất để không ghi đè
        filename = f"{uuid4().hex}.csv"

        saved_path = UPLOAD_DIR / filename

        # Lưu CSV vào thư mục uploads
        saved_path.write_bytes(
            uploaded_file.getvalue()
        )

        # Tạo nguồn dữ liệu
        cursor.execute("""
            INSERT INTO data_sources
            (source_name, source_type)
            VALUES (%s, 'CSV')
        """, (dataset_name,))

        source_id = cursor.lastrowid

        # Lưu thông tin dataset
        cursor.execute("""
            INSERT INTO datasets
            (source_id, dataset_name, file_path)
            VALUES (%s, %s, %s)
        """, (
            source_id,
            dataset_name,
            saved_path.relative_to(BASE_DIR).as_posix()
        ))

        dataset_id = cursor.lastrowid

        conn.commit()

        return {
            "success": True,
            "message": "Đăng ký dataset thành công!",
            "dataset_id": dataset_id
        }

    except Exception:
        if conn is not None:
            conn.rollback()

        # Nếu lưu database lỗi, xóa file vừa tạo
        if saved_path is not None and saved_path.exists():
            saved_path.unlink()

        raise

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()


# ==========================================
# 4. HIỂN THỊ DANH SÁCH DATASET
# ==========================================

st.subheader("Danh sách Dataset")

try:
    datasets = lay_datasets()

    if datasets:
        df_datasets = pd.DataFrame(datasets)

        st.dataframe(
            df_datasets,
            width="stretch",
            hide_index=True
        )

        st.metric(
            "Tổng số Dataset",
            len(datasets)
        )

    else:
        st.info(
            "Chưa có dataset nào trong hệ thống."
        )

except Exception as e:
    st.error(
        f"Không thể tải danh sách dataset: {e}"
    )
    st.stop()


# ==========================================
# 5. GIAO DIỆN THÊM DATASET
# ==========================================

st.divider()

st.subheader("Đăng ký Dataset CSV mới")

uploaded = st.file_uploader(
    "Chọn file CSV từ máy tính",
    type=["csv"],
    key="dataset_upload"
)

if uploaded is not None:

    try:
        # Đọc dữ liệu
        df = pd.read_csv(uploaded)

    except Exception as e:
        st.error(
            f"Không đọc được file CSV: {e}"
        )
        st.stop()

    # Hiển thị thông tin file
    st.success(
        f"Đã đọc file: {uploaded.name}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Số dòng",
            len(df)
        )

    with col2:
        st.metric(
            "Số cột",
            len(df.columns)
        )

    with col3:
        st.metric(
            "Dung lượng",
            f"{uploaded.size / 1024:.2f} KB"
        )

    # Xem trước dữ liệu
    st.subheader("Xem trước dữ liệu")

    st.dataframe(
        df.head(20),
        width="stretch",
        hide_index=True
    )

    # Danh sách cột
    with st.expander("Xem cấu trúc cột"):
        st.write([
            {
                "column": column,
                "type": str(df[column].dtype)
            }
            for column in df.columns
        ])

    # Nhập tên dataset
    dataset_name = st.text_input(
        "Tên Dataset",
        value=uploaded.name,
        help=(
            "Tên dùng để phân biệt dataset "
            "trong hệ thống."
        )
    )

    # Nút đăng ký
    if st.button(
        "Đăng ký Dataset",
        type="primary"
    ):

        try:
            result = dang_ky_dataset(
                dataset_name,
                uploaded
            )

            if result["success"]:

                st.success(result["message"])

                st.info(
                    "Dataset ID mới: "
                    f"{result['dataset_id']}"
                )

                st.rerun()

            else:
                st.warning(result["message"])

        except Exception as e:
            st.error(
                f"Đăng ký dataset thất bại: {e}"
            )


# ==========================================
# 6. HƯỚNG DẪN
# ==========================================

st.divider()

st.subheader("Hướng dẫn sử dụng")

st.markdown("""
1. Chọn file CSV từ máy tính.
2. Xem trước dữ liệu và kiểm tra tên cột.
3. Nhập tên Dataset không trùng.
4. Nhấn **Đăng ký Dataset**.
5. Chuyển sang trang **Quality Rules** để cấu hình quy tắc.
6. Chuyển sang **Data Quality** để chạy kiểm tra.
7. Xem lịch sử và cảnh báo tại **Dashboard**.
""")
