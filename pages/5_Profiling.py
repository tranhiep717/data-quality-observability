
import streamlit as st
import pandas as pd
import plotly.express as px

from modules.ingestion import doc_file_csv
from modules.profiling import phan_tich_du_lieu


st.set_page_config(
    page_title="Data Profiling",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Data Profiling")
st.write("Phân tích cấu trúc và đặc điểm của bộ dữ liệu.")

uploaded_file = st.file_uploader(
    "Tải file CSV để phân tích",
    type=["csv"]
)

if uploaded_file is not None:

    try:
        # Đọc dữ liệu từ file CSV
        df = doc_file_csv(uploaded_file)

        # Phân tích bằng module Profiling
        profiling = phan_tich_du_lieu(df)

        st.success("Phân tích dữ liệu thành công!")

        # 1. Thông tin tổng quan
        st.subheader("Tổng quan dữ liệu")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Tổng số dòng",
            profiling["tong_so_dong"]
        )

        col2.metric(
            "Tổng số cột",
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

        # 2. Xem trước dữ liệu
        st.subheader("Xem trước dữ liệu")

        st.dataframe(
            df.head(20),
            width="stretch"
        )

        # 3. Thống kê từng cột
        st.subheader("Thống kê chi tiết từng cột")

        stats_df = pd.DataFrame(
            profiling["thong_ke_cot"]
        )

        stats_df = stats_df.rename(columns={
            "ten_cot": "Tên cột",
            "kieu_du_lieu": "Kiểu dữ liệu",
            "so_null": "Số NULL",
            "so_gia_tri_duy_nhat": "Giá trị duy nhất",
            "ty_le_null": "Tỷ lệ NULL (%)",
            "min": "Min",
            "max": "Max",
            "mean": "Mean"
        })

        st.dataframe(
            stats_df,
            width="stretch"
        )

        # 4. Biểu đồ NULL theo từng cột
        st.subheader("Biểu đồ tỷ lệ dữ liệu thiếu")

        fig_null = px.bar(
            stats_df,
            x="Tên cột",
            y="Tỷ lệ NULL (%)",
            color="Tỷ lệ NULL (%)",
            text="Tỷ lệ NULL (%)",
            title="Tỷ lệ NULL theo từng cột"
        )

        fig_null.update_layout(
            yaxis_range=[0, 100]
        )

        st.plotly_chart(
            fig_null,
            width="stretch"
        )

        # 5. Phân tích chi tiết một cột
        st.subheader("Phân tích từng cột")

        selected_column = st.selectbox(
            "Chọn cột muốn phân tích",
            options=list(df.columns)
        )

        column_data = df[selected_column]

        st.write(
            "Kiểu dữ liệu:",
            str(column_data.dtype)
        )

        st.write(
            "Số giá trị NULL:",
            int(column_data.isna().sum())
        )

        st.write(
            "Số giá trị duy nhất:",
            int(column_data.nunique())
        )

        st.write("Các giá trị xuất hiện nhiều nhất:")

        frequency = (
            column_data
            .astype("string")
            .fillna("(NULL)")
            .value_counts()
            .head(10)
            .reset_index()
        )

        frequency.columns = [
            "Giá trị",
            "Số lần xuất hiện"
        ]

        st.dataframe(
            frequency,
            width="stretch"
        )

    except Exception as e:
        st.error(f"Phân tích dữ liệu thất bại: {e}")

else:
    st.info("Hãy tải một file CSV để bắt đầu phân tích.")
