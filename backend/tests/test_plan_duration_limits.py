from app.services.usage_limits import (
    max_duration_seconds_for_plan,
    monthly_upload_limit_for_plan,
)


def test_core_plan_duration_limits_match_product_policy(monkeypatch):
    monkeypatch.delenv("MEETIQ_STARTER_MAX_DURATION_SECONDS", raising=False)
    monkeypatch.delenv("MEETIQ_PRO_PILOT_MAX_DURATION_SECONDS", raising=False)
    monkeypatch.delenv("MEETIQ_BUSINESS_MAX_DURATION_SECONDS", raising=False)

    assert max_duration_seconds_for_plan("starter") == 60 * 60
    assert max_duration_seconds_for_plan("paid_pro") == 60 * 60
    assert max_duration_seconds_for_plan("pro_pilot") == 120 * 60
    assert max_duration_seconds_for_plan("business") == 180 * 60
    assert max_duration_seconds_for_plan("team") == 180 * 60
    assert max_duration_seconds_for_plan("premium") == 180 * 60
    assert max_duration_seconds_for_plan("custom") == 180 * 60
    assert max_duration_seconds_for_plan("enterprise") == 180 * 60


def test_business_manual_plan_upload_limit_has_safe_default(monkeypatch):
    monkeypatch.delenv("MEETIQ_BUSINESS_MONTHLY_UPLOAD_LIMIT", raising=False)

    assert monthly_upload_limit_for_plan("business") == 300
    assert monthly_upload_limit_for_plan("team") == 300
    assert monthly_upload_limit_for_plan("enterprise") == 300


def test_business_manual_plan_limits_can_be_overridden(monkeypatch):
    monkeypatch.setenv("MEETIQ_BUSINESS_MAX_DURATION_SECONDS", str(2 * 60 * 60))
    monkeypatch.setenv("MEETIQ_BUSINESS_MONTHLY_UPLOAD_LIMIT", "25")

    assert max_duration_seconds_for_plan("business") == 2 * 60 * 60
    assert monthly_upload_limit_for_plan("business") == 25
