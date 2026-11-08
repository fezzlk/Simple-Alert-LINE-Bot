from src.services.HabitCalendarTokenService import generate_token, verify_token


def test_generate_and_verify_token_round_trip(monkeypatch):
    monkeypatch.setattr(
        "src.services.HabitCalendarTokenService.config.FLASK_SECRET_KEY",
        "test-secret-key",
    )
    token = generate_token(line_user_id="U1", week_start_date="2026-03-09", now=1000)

    result = verify_token(token, now=1000)

    assert result == ("U1", "2026-03-09")


def test_verify_token_rejects_tampered_payload(monkeypatch):
    monkeypatch.setattr(
        "src.services.HabitCalendarTokenService.config.FLASK_SECRET_KEY",
        "test-secret-key",
    )
    token = generate_token(line_user_id="U1", week_start_date="2026-03-09", now=1000)
    payload_b64, _, signature = token.partition(".")

    tampered_token = f"{payload_b64}tampered.{signature}"

    assert verify_token(tampered_token, now=1000) is None


def test_verify_token_rejects_wrong_signature(monkeypatch):
    monkeypatch.setattr(
        "src.services.HabitCalendarTokenService.config.FLASK_SECRET_KEY",
        "test-secret-key",
    )
    token = generate_token(line_user_id="U1", week_start_date="2026-03-09", now=1000)
    payload_b64, _, _signature = token.partition(".")

    forged_token = f"{payload_b64}.{'0' * 64}"

    assert verify_token(forged_token, now=1000) is None


def test_verify_token_rejects_expired_token(monkeypatch):
    monkeypatch.setattr(
        "src.services.HabitCalendarTokenService.config.FLASK_SECRET_KEY",
        "test-secret-key",
    )
    issued_at = 1_000_000
    token = generate_token(line_user_id="U1", week_start_date="2026-03-09", now=issued_at)

    ttl = 14 * 24 * 60 * 60
    just_before_expiry = issued_at + ttl
    just_after_expiry = issued_at + ttl + 1

    assert verify_token(token, now=just_before_expiry) == ("U1", "2026-03-09")
    assert verify_token(token, now=just_after_expiry) is None


def test_verify_token_rejects_malformed_token(monkeypatch):
    monkeypatch.setattr(
        "src.services.HabitCalendarTokenService.config.FLASK_SECRET_KEY",
        "test-secret-key",
    )
    assert verify_token("") is None
    assert verify_token("no-dot-here") is None
    assert verify_token("invalid-base64!!!.deadbeef") is None
