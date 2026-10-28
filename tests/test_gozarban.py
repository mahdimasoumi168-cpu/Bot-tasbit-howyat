from app.payments.gozarban import _subscription_link, vpn_username


def test_vpn_username_is_stable_per_payment_and_user():
    assert vpn_username(17, 12345) == "nyvpn12345_17"
    assert vpn_username(17, 12345) == vpn_username(17, 12345)
    assert vpn_username(18, 12345) != vpn_username(17, 12345)


def test_subscription_link_prefers_https_subscription_url():
    assert _subscription_link({
        "external_data": {
            "subscription_url": "https://gozarban.com/sub/abc",
            "links": ["vless://node"],
        }
    }) == "https://gozarban.com/sub/abc"


def test_subscription_link_falls_back_to_supported_connection_links():
    assert _subscription_link({
        "external_data": {"links": ["vless://node", "not-a-link"]}
    }) == "vless://node"


def test_subscription_link_does_not_return_untrusted_plain_http_url():
    assert _subscription_link({"subscription_url": "http://example.com/sub"}) is None
