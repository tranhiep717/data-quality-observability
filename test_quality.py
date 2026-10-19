from modules.ingestion import doc_file_csv
from modules.rules import lay_danh_sach_quy_tac
from modules.quality import chay_quality_engine, tinh_quality_score

# 1. Đọc dữ liệu CSV
df = doc_file_csv("test_data.csv")

# 2. Lấy Quality Rules từ MySQL
rules = lay_danh_sach_quy_tac(
    dataset_id=1,
    chi_lay_active=True
)

print("SO QUY TAC:", len(rules))

# 3. Chạy Quality Engine
ket_qua = chay_quality_engine(df, rules)

for result in ket_qua:
    print(result)

# 4. Tính Quality Score
score = tinh_quality_score(ket_qua)

print("------------------------")
print("QUALITY SCORE:", score)