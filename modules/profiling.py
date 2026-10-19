
import pandas as pd
from pandas.api.types import is_numeric_dtype


def phan_tich_du_lieu(df):
    """
    Phân tích thống kê dữ liệu bằng Pandas.

    Trả về:
    - Tổng số dòng, cột, NULL, trùng lặp
    - Thống kê theo từng cột
    - Min, Max, Mean cho cột số
    """

    if not isinstance(df, pd.DataFrame):
        raise ValueError(
            "Dữ liệu đầu vào phải là DataFrame"
        )

    tong_so_dong = len(df)
    tong_so_cot = len(df.columns)

    tong_null = int(df.isna().sum().sum())
    tong_trung_lap = int(df.duplicated().sum())

    thong_ke_cot = []

    for cot in df.columns:
        series = df[cot]

        so_null = int(series.isna().sum())

        ty_le_null = (
            round(so_null / tong_so_dong * 100, 2)
            if tong_so_dong > 0
            else 0.0
        )

        thong_ke = {
            "ten_cot": cot,
            "kieu_du_lieu": str(series.dtype),
            "so_null": so_null,
            "so_gia_tri_duy_nhat": int(
                series.nunique()
            ),
            "ty_le_null": float(ty_le_null),
            "min": None,
            "max": None,
            "mean": None
        }

        # Chỉ tính thống kê số cho cột kiểu numeric
        if is_numeric_dtype(series):
            values = pd.to_numeric(
                series,
                errors="coerce"
            ).dropna()

            if not values.empty:
                thong_ke["min"] = float(values.min())
                thong_ke["max"] = float(values.max())
                thong_ke["mean"] = round(
                    float(values.mean()), 2
                )

        thong_ke_cot.append(thong_ke)

    return {
        "tong_so_dong": tong_so_dong,
        "tong_so_cot": tong_so_cot,
        "tong_null": tong_null,
        "tong_trung_lap": tong_trung_lap,
        "thong_ke_cot": thong_ke_cot
    }
