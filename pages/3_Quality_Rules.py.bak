
import json
import streamlit as st
import pandas as pd

from modules.database import ket_noi_database

st.title("Quản lý quy tắc kiểm tra")
st.write("Thêm, chỉnh sửa và bật/tắt quy tắc chất lượng dữ liệu.")

RULE_TYPES = [
    "NOT_NULL",
    "UNIQUE",
    "BETWEEN",
    "MIN_VALUE",
    "MAX_VALUE",
    "ALLOWED_VALUES",
    "REGEX"
]


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


def thuc_thi(sql, params):
    conn = ket_noi_database()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    finally:
        conn.close()


def lay_datasets():
    return truy_van("""
        SELECT dataset_id, dataset_name
        FROM datasets
        ORDER BY dataset_id
    """)


def lay_rules(dataset_id):
    return truy_van("""
        SELECT rule_id, column_name, rule_type,
               rule_config, is_active
        FROM quality_rules
        WHERE dataset_id = %s
        ORDER BY rule_id
    """, (dataset_id,))


def tao_config(
    rule_type,
    minimum=0.0,
    maximum=100.0,
    allowed_values="",
    regex_pattern=""
):
    """Tạo cấu hình JSON cho từng loại Quality Rule."""

    if rule_type == "BETWEEN":
        if minimum > maximum:
            raise ValueError(
                "Giá trị Min không được lớn hơn Max."
            )

        config = {
            "min": minimum,
            "max": maximum
        }

    elif rule_type == "MIN_VALUE":
        config = {
            "min": minimum
        }

    elif rule_type == "MAX_VALUE":
        config = {
            "max": maximum
        }

    elif rule_type == "ALLOWED_VALUES":
        values = [
            value.strip()
            for value in allowed_values.split(",")
            if value.strip()
        ]

        if not values:
            raise ValueError(
                "Bạn phải nhập ít nhất một giá trị cho phép."
            )

        config = {
            "values": values
        }

    elif rule_type == "REGEX":
        import re

        regex_pattern = regex_pattern.strip()

        if not regex_pattern:
            raise ValueError(
                "Bạn chưa nhập biểu thức REGEX."
            )

        try:
            re.compile(regex_pattern)
        except re.error as e:
            raise ValueError(
                f"Biểu thức REGEX không hợp lệ: {e}"
            )

        config = {
            "pattern": regex_pattern
        }

    else:
        config = {}

    return json.dumps(
        config,
        ensure_ascii=False
    )



try:
    datasets = lay_datasets()

    if not datasets:
        st.warning("Chưa có dataset trong MySQL.")
        st.stop()

    # 1. Chọn dataset
    options = {
        f"{d['dataset_name']} (ID {d['dataset_id']})":
        d["dataset_id"]
        for d in datasets
    }

    selected = st.selectbox(
        "Chọn dataset",
        list(options.keys())
    )

    dataset_id = options[selected]
    
    # Đọc cấu trúc cột từ file CSV
    import os

    st.subheader("Nhận diện cột dữ liệu")

    uploaded_csv = st.file_uploader(
        "Tải file CSV để lấy danh sách cột",
        type=["csv"],
        key="rules_csv"
    )

    columns = []

    if uploaded_csv is not None:
        try:
            preview_df = pd.read_csv(uploaded_csv)
            columns = preview_df.columns.tolist()

            st.success(
                f"Đã nhận diện {len(columns)} cột dữ liệu"
            )

            st.write("Các cột:", columns)

        except Exception as e:
            st.error(f"Không đọc được CSV: {e}")


    # 2. Hiển thị quy tắc hiện tại
    st.subheader("Danh sách quy tắc")

    rules = lay_rules(dataset_id)

    if rules:
        table_data = []
        for rule in rules:
            table_data.append({
                "ID": rule["rule_id"],
                "Cột": rule["column_name"],
                "Quy tắc": rule["rule_type"],
                "Cấu hình": json.dumps(
                    rule["rule_config"],
                    ensure_ascii=False
                ) if not isinstance(
                    rule["rule_config"], str
                ) else rule["rule_config"],
                "Kích hoạt": bool(rule["is_active"])
            })

        st.dataframe(
            pd.DataFrame(table_data),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Dataset chưa có quy tắc.")

    st.divider()

    # 3. Thêm quy tắc
    st.subheader("Thêm quy tắc mới")

    with st.form("add_rule_form"):
        
        if columns:
            column_name = st.selectbox(
                "Chọn cột dữ liệu",
                options=columns
            )
        else:
            column_name = st.text_input(
                "Tên cột dữ liệu",
                placeholder="Tải file CSV để chọn cột"
            )

        rule_type = st.selectbox(
            "Loại quy tắc",
            RULE_TYPES
        )

        
        minimum = 0.0
        maximum = 100.0
        allowed_values = ""
        regex_pattern = ""

        if rule_type == "BETWEEN":
            minimum = st.number_input(
                "Giá trị nhỏ nhất (Min)",
                value=18.0
            )

            maximum = st.number_input(
                "Giá trị lớn nhất (Max)",
                value=30.0
            )

        elif rule_type == "MIN_VALUE":
            minimum = st.number_input(
                "Giá trị tối thiểu",
                value=18.0
            )

        elif rule_type == "MAX_VALUE":
            maximum = st.number_input(
                "Giá trị tối đa",
                value=60.0
            )

        elif rule_type == "ALLOWED_VALUES":
            allowed_values = st.text_input(
                "Các giá trị cho phép",
                placeholder="Nam, Nữ, Khác"
            )

        elif rule_type == "REGEX":
            regex_pattern = st.text_input(
                "Biểu thức REGEX",
                placeholder=r"^[0-9]{10}$"
            )


        is_active = st.checkbox(
            "Kích hoạt ngay",
            value=True
        )

        submitted = st.form_submit_button(
            "Lưu quy tắc",
            type="primary"
        )

    if submitted:
        try:
            column_name = column_name.strip()

            if not column_name:
                st.error("Bạn chưa nhập tên cột.")
            else:
                config = tao_config(
                    rule_type=rule_type,
                    minimum=minimum,
                    maximum=maximum,
                    allowed_values=allowed_values,
                    regex_pattern=regex_pattern
                )
                
                # Kiểm tra cột tồn tại trong CSV
                if columns and column_name not in columns:
                    raise ValueError(
                        f"Cột '{column_name}' không tồn tại trong CSV"
                    )

                # Kiểm tra quy tắc BETWEEN chỉ áp dụng cho dữ liệu số
                if (
                    rule_type in {"BETWEEN", "MIN_VALUE", "MAX_VALUE"}
                    and uploaded_csv is not None
                ):
                    values = preview_df[column_name].dropna()

                    if not pd.api.types.is_numeric_dtype(
                        preview_df[column_name]
                    ):
                        raise ValueError(
                            "BETWEEN chỉ áp dụng cho cột dữ liệu số"
                        )

                
                # Kiểm tra quy tắc đã tồn tại chưa
                existing = truy_van("""
                    SELECT rule_id
                    FROM quality_rules
                    WHERE dataset_id = %s
                      AND column_name = %s
                      AND rule_type = %s
                    LIMIT 1
                """, (
                    dataset_id,
                    column_name,
                    rule_type
                ))

                if existing:
                    st.error(
                        "Quy tắc này đã tồn tại! "
                        "Hãy chỉnh sửa quy tắc cũ."
                    )
                    st.stop()


                thuc_thi("""
                    INSERT INTO quality_rules
                    (dataset_id, column_name, rule_type,
                     rule_config, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    dataset_id, column_name,
                    rule_type, config, is_active
                ))

                st.success("Đã thêm quy tắc!")
                st.rerun()

        except Exception as e:
            st.error(f"Không thể lưu quy tắc: {e}")

    st.divider()

    # 4. Sửa hoặc bật/tắt quy tắc
    st.subheader("Chỉnh sửa quy tắc")

    if rules:
        rule_map = {
            f"ID {r['rule_id']} - "
            f"{r['column_name']} ({r['rule_type']})": r
            for r in rules
        }

        selected_rule = st.selectbox(
            "Chọn quy tắc cần sửa",
            list(rule_map.keys())
        )

        current = rule_map[selected_rule]

        raw_config = current["rule_config"]
        if isinstance(raw_config, str):
            current_config = json.loads(raw_config or "{}")
        else:
            current_config = raw_config or {}

        with st.form(
            f"edit_rule_{current['rule_id']}"
        ):
            new_column = st.text_input(
                "Tên cột",
                value=current["column_name"]
            )

            new_type = st.selectbox(
                "Quy tắc",
                RULE_TYPES,
                index=RULE_TYPES.index(
                    current["rule_type"]
                ) if current["rule_type"] in RULE_TYPES else 0
            )

            
            new_min = 0.0
            new_max = 100.0
            new_allowed_values = ""
            new_regex_pattern = ""

            if new_type == "BETWEEN":
                new_min = st.number_input(
                    "Min",
                    value=float(
                        current_config.get("min", 18)
                    )
                )

                new_max = st.number_input(
                    "Max",
                    value=float(
                        current_config.get("max", 30)
                    )
                )

            elif new_type == "MIN_VALUE":
                new_min = st.number_input(
                    "Giá trị tối thiểu",
                    value=float(
                        current_config.get("min", 18)
                    )
                )

            elif new_type == "MAX_VALUE":
                new_max = st.number_input(
                    "Giá trị tối đa",
                    value=float(
                        current_config.get("max", 60)
                    )
                )

            elif new_type == "ALLOWED_VALUES":
                values = current_config.get(
                    "values", []
                )

                new_allowed_values = st.text_input(
                    "Các giá trị cho phép",
                    value=", ".join(
                        str(v) for v in values
                    )
                )

            elif new_type == "REGEX":
                new_regex_pattern = st.text_input(
                    "Biểu thức REGEX",
                    value=current_config.get(
                        "pattern", ""
                    )
                )

                new_min = st.number_input(
                    "Min",
                    value=float(
                        current_config.get("min", 18)
                    )
                )

                new_max = st.number_input(
                    "Max",
                    value=float(
                        current_config.get("max", 30)
                    )
                )

            new_active = st.checkbox(
                "Kích hoạt",
                value=bool(current["is_active"])
            )

            update = st.form_submit_button(
                "Cập nhật quy tắc"
            )

        if update:
            try:
                if not new_column.strip():
                    raise ValueError("Tên cột không được trống")

                config = tao_config(
                    rule_type=new_type,
                    minimum=new_min,
                    maximum=new_max,
                    allowed_values=new_allowed_values,
                    regex_pattern=new_regex_pattern
                )

                thuc_thi("""
                    UPDATE quality_rules
                    SET column_name = %s,
                        rule_type = %s,
                        rule_config = %s,
                        is_active = %s
                    WHERE rule_id = %s
                      AND dataset_id = %s
                """, (
                    new_column.strip(), new_type,
                    config, new_active,
                    current["rule_id"], dataset_id
                ))

                st.success("Đã cập nhật quy tắc!")
                st.rerun()

            except Exception as e:
                st.error(f"Cập nhật thất bại: {e}")

    st.divider()

    st.caption(
        "Các thay đổi được lưu trực tiếp vào MySQL. "
        "Lần kiểm tra tiếp theo sẽ sử dụng các quy tắc "
        "đang được kích hoạt."
    )

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
