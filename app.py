
import streamlit as st
from modules.database import kiem_tra_ket_noi

st.title("Data Quality & Observability Platform")

try:
    bang = kiem_tra_ket_noi()
    st.success("Kết nối MySQL thành công!")
    st.write("Các bảng trong database:")
    st.write([item[0] for item in bang])
except Exception as e:
    st.error(f"Kết nối thất bại: {e}")
