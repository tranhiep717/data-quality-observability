import pandas as pd

from modules.quality import kiem_tra_quy_tac

# Dữ liệu mẫu
df = pd.DataFrame({
    "id": [1, 2, 3, 4, 4],
    "name": ["An", "Binh", "Chi", "Dung", "Dung"],
    "age": [20, 21, None, 22, 22],
    "email": [
        "an@gmail.com",
        "binh@gmail.com",
        "chi@gmail.com",
        "dung@gmail.com",
        "dung@gmail.com"
    ]
})

# Danh sách quy tắc kiểm tra
rules = [
    {
        "column_name": "age",
        "rule_type": "NOT_NULL",
        "rule_config": {}
    },
    {
        "column_name": "id",
        "rule_type": "UNIQUE",
        "rule_config": {}
    },
    {
        "column_name": "age",
        "rule_type": "BETWEEN",
        "rule_config": {"min": 18, "max": 60}
    },
    {
        "column_name": "age",
        "rule_type": "MIN_VALUE",
        "rule_config": {"min": 18}
    },
    {
        "column_name": "age",
        "rule_type": "MAX_VALUE",
        "rule_config": {"max": 60}
    },
    {
        "column_name": "name",
        "rule_type": "ALLOWED_VALUES",
        "rule_config": {
            "values": ["An", "Binh", "Chi"]
        }
    },
    {
        "column_name": "email",
        "rule_type": "REGEX",
        "rule_config": {
            "pattern": r"[^@\s]+@[^@\s]+\.[^@\s]+"
        }
    }
]

print("KIEM THU 7 QUALITY RULES")
print("-" * 60)

for rule in rules:
    result = kiem_tra_quy_tac(
        df,
        rule["column_name"],
        rule["rule_type"],
        rule["rule_config"]
    )

    print(
        f"{result['rule_type']:15} | "
        f"Failed: {result['failed_rows']} | "
        f"Pass rate: {result['pass_rate']}% | "
        f"Status: {result['result_status']}"
    )