
import pandas as pd

from modules.quality import (
    kiem_tra_quy_tac,
    chay_quality_engine,
    tinh_quality_score
)


df = pd.DataFrame({
    "id": ["A01", "A02", "A02", "A04"],
    "name": ["An", None, "Binh", "Cuong"],
    "age": [20, 15, 35, 25],
    "score": [8, 4, 12, 6],
    "status": ["Active", "Inactive", "Unknown", "Active"],
    "email": [
        "an@gmail.com",
        "invalid-email",
        "binh@gmail.com",
        "cuong@gmail.com"
    ]
})

rules = [
    {
        "rule_id": 1,
        "column_name": "name",
        "rule_type": "NOT_NULL",
        "rule_config": {},
        "is_active": 1
    },
    {
        "rule_id": 2,
        "column_name": "id",
        "rule_type": "UNIQUE",
        "rule_config": {},
        "is_active": 1
    },
    {
        "rule_id": 3,
        "column_name": "age",
        "rule_type": "BETWEEN",
        "rule_config": {"min": 18, "max": 30},
        "is_active": 1
    },
    {
        "rule_id": 4,
        "column_name": "score",
        "rule_type": "MIN_VALUE",
        "rule_config": {"min": 5},
        "is_active": 1
    },
    {
        "rule_id": 5,
        "column_name": "score",
        "rule_type": "MAX_VALUE",
        "rule_config": {"max": 10},
        "is_active": 1
    },
    {
        "rule_id": 6,
        "column_name": "status",
        "rule_type": "ALLOWED_VALUES",
        "rule_config": {
            "values": ["Active", "Inactive"]
        },
        "is_active": 1
    },
    {
        "rule_id": 7,
        "column_name": "email",
        "rule_type": "REGEX",
        "rule_config": {
            "pattern": r"[^@\s]+@[^@\s]+\.[^@\s]+"
        },
        "is_active": 1
    }
]

results = chay_quality_engine(df, rules)
score = tinh_quality_score(results)

expected_failed = {
    "NOT_NULL": 1,
    "UNIQUE": 1,
    "BETWEEN": 2,
    "MIN_VALUE": 1,
    "MAX_VALUE": 1,
    "ALLOWED_VALUES": 1,
    "REGEX": 1
}

print("=== KIEM THU 7 QUALITY RULES ===")

assert len(results) == 7, "Không chạy đủ 7 quy tắc"

for result in results:
    rule_type = result["rule_type"]
    actual = result["failed_rows"]
    expected = expected_failed[rule_type]

    print(
        f"{rule_type}: {actual} loi "
        f"(mong doi {expected})"
    )

    assert actual == expected, (
        f"{rule_type}: mong doi {expected}, "
        f"nhung nhan {actual}"
    )

print(f"\nQUALITY SCORE: {score}%")
print("TAT CA 7 QUALITY RULES DEU DAT KIEM THU")
