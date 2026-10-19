
from unittest.mock import patch

from modules.alerts import kiem_tra_canh_bao_monitoring


def test_volume_drop():
    metrics = {
        "current_run": 100,
        "previous_row_count": 1000,
        "current_row_count": 700,
        "row_change_percent": -30.0,
        "null_difference": 0,
        "added_columns": [],
        "removed_columns": [],
        "changed_types": {}
    }

    with patch(
        "modules.alerts.so_sanh_metrics",
        return_value=metrics
    ), patch("modules.alerts.tao_canh_bao") as save:
        messages = kiem_tra_canh_bao_monitoring(1)

        assert any("giảm bất thường" in m for m in messages)
        save.assert_called_once()

        args = save.call_args.args
        assert args[2] == "VOLUME_DROP"
        assert args[3] == "WARNING"

    print("PASS: VOLUME_DROP (-30%)")


def test_schema_critical():
    metrics = {
        "current_run": 101,
        "previous_row_count": 1000,
        "current_row_count": 1000,
        "row_change_percent": 0.0,
        "null_difference": 0,
        "added_columns": [],
        "removed_columns": ["phone"],
        "changed_types": {}
    }

    with patch(
        "modules.alerts.so_sanh_metrics",
        return_value=metrics
    ), patch("modules.alerts.tao_canh_bao") as save:
        messages = kiem_tra_canh_bao_monitoring(1)

        assert any("Schema Drift" in m for m in messages)
        save.assert_called_once()

        args = save.call_args.args
        assert args[2] == "SCHEMA_DRIFT"
        assert args[3] == "CRITICAL"

    print("PASS: SCHEMA_DRIFT CRITICAL")


if __name__ == "__main__":
    test_volume_drop()
    test_schema_critical()
    print("TAT CA KIEM THU MONITORING DEU DAT")
