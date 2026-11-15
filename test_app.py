from app import calculate_alert_threshold


def test_calculates_difference_from_configured_limit():
    assert calculate_alert_threshold(1000.0, "250.0") == 750.0
