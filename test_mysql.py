from modules.ingestion import doc_bang_mysql

print("DANG DOC DU LIEU MYSQL...")

df = doc_bang_mysql("quality_rules")

print("\n5 DONG DAU TIEN:")
print(df.head())

print("\nSO DONG:", len(df))
print("SO COT:", len(df.columns))

from modules.profiling import phan_tich_du_lieu

print("\nDATA PROFILING MYSQL:")

ket_qua = phan_tich_du_lieu(df)

print(ket_qua)