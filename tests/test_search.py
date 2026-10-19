from src.lead_discovery.search import normalize_search_result_url


def test_normalize_absolute_url():
    assert normalize_search_result_url("https://example.com/about") == "https://example.com/about"


def test_normalize_duckduckgo_redirect_url():
    url = "https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fabout&rut=abc"
    assert normalize_search_result_url(url) == "https://example.com/about"


def test_normalize_protocol_relative_duckduckgo_redirect_url():
    url = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2F"
    assert normalize_search_result_url(url) == "https://example.org/"


def test_reject_non_http_url():
    assert normalize_search_result_url("javascript:void(0)") == ""
