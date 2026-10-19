import pandas as pd


def phan_tich_du_lieu(df):
    """
    Phân tích tổng quan chất lượng dữ liệu.

    Parameters:
        df: pandas DataFrame

    Returns:
        dict: Thông tin profiling
    """

    if not isinstance(df, pd.DataFrame):
        raise ValueError("Dữ liệu đầu vào phải là DataFrame")

    # Thống kê tổng quan
    tong_so_dong = len(df)
    tong_so_cot = len(df.columns)

    tong_null = int(df.isnull().sum().sum())
    tong_trung_lap = int(df.duplicated().sum())

    # Thống kê từng cột
    thong_ke_cot = []

    for cot in df.columns:
        thong_ke_cot.append({
            "ten_cot": cot,
            "kieu_du_lieu": str(df[cot].dtype),
            "so_null": int(df[cot].isnull().sum()),
            "so_gia_tri_duy_nhat": int(df[cot].nunique()),
            "ty_le_null": float(round(
                df[cot].isnull().mean() * 100, 2
            )) if tong_so_dong > 0 else 0
        })

    return {
        "tong_so_dong": tong_so_dong,
        "tong_so_cot": tong_so_cot,
        "tong_null": tong_null,
        "tong_trung_lap": tong_trung_lap,
        "thong_ke_cot": thong_ke_cot
    }