
"""
Kiểm thử tích hợp Người 1 và Người 2.

Người 1:
- Đọc dữ liệu CSV
- Kiểm tra Quality Rules
- Tính Quality Score

Người 2:
- Lưu Pipeline Runs
- Lưu Quality Results
- Lưu Dataset Metrics
- Monitoring và Alerts
"""

from modules.ingestion import doc_file_csv
from modules.quality import chay_kiem_tra
from modules.alerts import (
    kiem_tra_canh_bao,
    kiem_tra_canh_bao_monitoring
)


DATASET_ID = 1
FILE_PATH = "data/uploads/students.csv"


def main():
    # 1. Người 1: đọc dữ liệu CSV
    df = doc_file_csv(FILE_PATH)

    print("=== THONG TIN DU LIEU ===")
    print("So dong:", len(df))
    print("So cot:", len(df.columns))

    # 2. Chạy Quality Engine và lưu MySQL
    # chay_kiem_tra() đã gọi các hàm của Người 1:
    # - chay_quality_engine()
    # - tinh_quality_score()
    # Đồng thời lưu kết quả bằng phần Người 2.
    result = chay_kiem_tra(df, DATASET_ID)

    print("\n=== KET QUA KIEM TRA ===")
    print("Run ID:", result["run_id"])
    print("Quality Score:", result["quality_score"])

    for item in result["results"]:
        print(
            f"{item['column']} - {item['rule']}: "
            f"{item['failed_rows']} loi, "
            f"dat {item['pass_rate']}%"
        )

    print("\nDa luu ket qua vao MySQL!")

    # 3. Người 2: cảnh báo chất lượng
    try:
        alerts = kiem_tra_canh_bao(DATASET_ID)

        print("\n=== CANH BAO CHAT LUONG ===")

        for message in alerts:
            print(message)

    except Exception as error:
        print("Loi tao canh bao chat luong:", error)

    # 4. Người 2: cảnh báo Monitoring
    try:
        monitoring_alerts = kiem_tra_canh_bao_monitoring(
            DATASET_ID
        )

        print("\n=== CANH BAO MONITORING ===")

        for message in monitoring_alerts:
            print(message)

    except Exception as error:
        print("Loi tao canh bao Monitoring:", error)


if __name__ == "__main__":
    main()
