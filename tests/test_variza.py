import hashlib
import hmac

from app.payments.variza import verify_webhook_signature


def test_verify_webhook_signature_accepts_valid_raw_body():
    body = b'{"event":"payment.paid","slug":"abc123","base_amount":280000,"status":"paid"}'
    secret = "test-webhook-secret"
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(body, f"sha256={digest}", secret)


def test_verify_webhook_signature_rejects_modified_body():
    body = b'{"event":"payment.paid","slug":"abc123","base_amount":280000,"status":"paid"}'
    secret = "test-webhook-secret"
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert not verify_webhook_signature(body + b" ", f"sha256={digest}", secret)


def test_verify_webhook_signature_rejects_missing_secret_or_signature():
    assert not verify_webhook_signature(b"{}", "sha256=anything", "")
    assert not verify_webhook_signature(b"{}", "", "test-webhook-secret")
