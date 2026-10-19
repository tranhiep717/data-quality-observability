import pandas as pd


def kiem_tra_quy_tac(df, column_name, rule_type, rule_config=None):
    """
    Kiểm tra một quy tắc chất lượng dữ liệu.

    Trả về:
        checked_rows
        failed_rows
        pass_rate
        result_status
    """

    if rule_config is None:
        rule_config = {}

    if column_name not in df.columns:
        raise ValueError(f"Cột '{column_name}' không tồn tại")

    series = df[column_name]

    if rule_type == "NOT_NULL":
        failed = series.isna()

    elif rule_type == "UNIQUE":
        failed = series.duplicated(keep="first")

    elif rule_type == "BETWEEN":
        min_value = rule_config["min"]
        max_value = rule_config["max"]

        values = pd.to_numeric(series, errors="coerce")

        failed = (
            values.isna()
            | (values < min_value)
            | (values > max_value)
        )

    elif rule_type == "MIN_VALUE":
        min_value = rule_config["min"]

        values = pd.to_numeric(series, errors="coerce")

        failed = values.isna() | (values < min_value)

    elif rule_type == "MAX_VALUE":
        max_value = rule_config["max"]

        values = pd.to_numeric(series, errors="coerce")

        failed = values.isna() | (values > max_value)

    elif rule_type == "ALLOWED_VALUES":
        allowed = rule_config["values"]

        failed = ~series.isin(allowed)

    elif rule_type == "REGEX":
        pattern = rule_config["pattern"]

        failed = ~series.astype("string").str.fullmatch(
            pattern,
            na=False
        )

    else:
        raise ValueError(f"Quy tắc không được hỗ trợ: {rule_type}")

    checked_rows = len(df)
    failed_rows = int(failed.sum())

    pass_rate = (
        round((checked_rows - failed_rows) / checked_rows * 100, 2)
        if checked_rows > 0
        else 100.0
    )

    return {
        "column_name": column_name,
        "rule_type": rule_type,
        "checked_rows": checked_rows,
        "failed_rows": failed_rows,
        "pass_rate": pass_rate,
        "result_status": "PASS" if failed_rows == 0 else "FAIL"
    }
def chay_quality_engine(df, rules):
    """
    Chạy tất cả Quality Rules đang hoạt động.
    """

    ket_qua = []

    for rule in rules:

        if not rule["is_active"]:
            continue

        result = kiem_tra_quy_tac(
            df=df,
            column_name=rule["column_name"],
            rule_type=rule["rule_type"],
            rule_config=rule["rule_config"]
        )

        result["rule_id"] = rule["rule_id"]

        ket_qua.append(result)

    return ket_qua


def tinh_quality_score(ket_qua):
    """
    Tính điểm chất lượng tổng thể
    bằng trung bình tỷ lệ đạt của các quy tắc.
    """

    if not ket_qua:
        return 0.0

    tong_diem = sum(
        result["pass_rate"]
        for result in ket_qua
    )

    return round(tong_diem / len(ket_qua), 2)