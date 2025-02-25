import pytest
from packaging.version import Version
from scrapy import __version__ as SCRAPY_VERSION

if Version(SCRAPY_VERSION) < Version("2.7"):
    pytest.skip("Skipping tests for Scrapy ≥ 2.7", allow_module_level=True)

from scrapy import Request
from scrapy.settings.default_settings import REQUEST_FINGERPRINTER_CLASS
from scrapy.utils.misc import create_instance, load_object
from scrapy.utils.test import get_crawler

from scrapy_zyte_api import ScrapyZyteAPIRequestFingerprinter


def test_cache():
    crawler = get_crawler()
    fingerprinter = create_instance(
        ScrapyZyteAPIRequestFingerprinter, settings=crawler.settings, crawler=crawler
    )
    request = Request("https://example.com", meta={"zyte_api": True})
    fingerprint = fingerprinter.fingerprint(request)
    assert fingerprint == fingerprinter._cache[request]


def test_fallback_custom():
    class CustomFingerprinter:
        def fingerprint(self, request):
            return b"foo"

    settings = {
        "ZYTE_API_FALLBACK_REQUEST_FINGERPRINTER_CLASS": CustomFingerprinter,
    }
    crawler = get_crawler(settings_dict=settings)
    fingerprinter = create_instance(
        ScrapyZyteAPIRequestFingerprinter, settings=crawler.settings, crawler=crawler
    )
    request = Request("https://example.com")
    assert fingerprinter.fingerprint(request) == b"foo"
    request = Request("https://example.com", meta={"zyte_api": True})
    assert fingerprinter.fingerprint(request) != b"foo"


def test_fallback_default():
    crawler = get_crawler()
    fingerprinter = create_instance(
        ScrapyZyteAPIRequestFingerprinter, settings=crawler.settings, crawler=crawler
    )
    fallback_fingerprinter = create_instance(
        load_object(REQUEST_FINGERPRINTER_CLASS),
        settings=crawler.settings,
        crawler=crawler,
    )
    request = Request("https://example.com")
    new_fingerprint = fingerprinter.fingerprint(request)
    old_fingerprint = fallback_fingerprinter.fingerprint(request)
    assert new_fingerprint == old_fingerprint

    request = Request("https://example.com", meta={"zyte_api_automap": True})
    new_fingerprint = fingerprinter.fingerprint(request)
    assert old_fingerprint == fallback_fingerprinter.fingerprint(request)
    assert new_fingerprint != old_fingerprint


def test_headers():
    crawler = get_crawler()
    fingerprinter = create_instance(
        ScrapyZyteAPIRequestFingerprinter, settings=crawler.settings, crawler=crawler
    )
    request1 = Request(
        "https://example.com",
        meta={
            "zyte_api": {
                "customHttpRequestHeaders": [{"name": "foo", "value": "bar"}],
                "requestHeaders": {"referer": "baz"},
            }
        },
    )
    request2 = Request("https://example.com", meta={"zyte_api": True})
    fingerprint1 = fingerprinter.fingerprint(request1)
    fingerprint2 = fingerprinter.fingerprint(request2)
    assert fingerprint1 == fingerprint2


@pytest.mark.parametrize(
    "url,params,fingerprint",
    (
        (
            "https://example.com",
            {},
            b"\xccz|-\x1c%\xc5\xa3\x813\x91\x1a\x1a<\x95\x91\xf91a\n",
        ),
        (
            "https://example.com/a",
            {},
            b"x!<\xc5\x88\x08#\x9e\xf0\x19J\xd4\x92\x88\xb9\xb9\xce}\xb5\xda",
        ),
        (
            "https://example.com?a",
            {},
            b'\x80D\xdag"E\x8d=\xc7\xd68\xe1\xfd\xfd\x91\xe8\xd2.\xe6\xe4',
        ),
        (
            "https://example.com?a=b",
            {},
            b"r\xa6\x93\xa59\xb8\xb0\x9a\x90`p\xbf8\xdbW\x0f%\x17@N",
        ),
        (
            "https://example.com?a=b&a",
            {},
            b"T\x88[O\x8f\x87\xc1\xbb\x0e\xa3\xfbg^s\xf9=\x92?\x17\xe8",
        ),
        (
            "https://example.com?a=b&a=c",
            {},
            b"\xff=\xc3\xe74`\x048\xecM\xa3\xe8&\xb9\x06\xdf\xb2\xb0\x96\x8e",
        ),
        (
            "https://example.com",
            {"httpRequestBody": "Zm9v"},
            b";*\xa9Wt\xcfcso2\x9e\xa5\xd9_\xcc~_\xf5\\\xcd",
        ),
        (
            "https://example.com",
            {"httpRequestMethod": "POST"},
            b"\xe1\xf3&2R%\x0c\x82mf\x88E\x11L\x05w+\xa6V\xcb",
        ),
        (
            "https://example.com",
            {"httpResponseBody": True},
            b"e\x1e\xd3J0ya_\xca\xc3\xa0\xbe'h\x0ff*\xa6b\xf2",
        ),
        (
            "https://example.com",
            {"httpResponseHeaders": True},
            b"\xcc^\x0e$\xa7\xe5\x97\xb8\xbf\x7f0\xa3\xec\xf5B\\\xe1h\x1c\xee",
        ),
        (
            "https://example.com",
            {"browserHtml": True},
            b"\xb2\x8e\x98\xa9\xa2\xf2\xa6\x96\x01\xf6\x1dYa\xf7\xdf\xc2\xe5>x\x11",
        ),
        (
            "https://example.com",
            {"screenshot": True},
            b"\x8a\xd1\x1fut\x99\xf1\xc4\xcc\xa8\xfd\xd9\x7f\x1fY\xf8\xdf/'\xb3",
        ),
        (
            "https://example.com",
            {"screenshotOptions": {"format": "png"}},
            b"\xe2\xba\xeb\x16\xb9\xd4\x117\x19\xac\x7f\xb3\x17\xf5\xf6\xfc\x9e\x94l\xcf",
        ),
        (
            "https://example.com",
            {"geolocation": "US"},
            b"#\xe2\\\xce\xb88\xf8\xb4\x19\xa09KL\xe4\x87\x80\x00\x00A7",
        ),
        (
            "https://example.com",
            {"javascript": False},
            b"\x1c!\x89\xfc\xadd\xb3\xbf-_\x97\xca\xc0g\xbdo\xee\xdc\xdfo",
        ),
        (
            "https://example.com",
            {"actions": [{"action": "click", "selector": ".button"}]},
            b"\x83\xfa\x04\xfal\xc6d(\xe1\x06\xf1>b\xed\xbe\xb1\xf2\xac5E",
        ),
    ),
)
def test_known_fingerprints(url, params, fingerprint):
    """Test that known fingerprints remain the same, i.e. make sure that we do
    not accidentally modify fingerprints with future implementation changes."""
    crawler = get_crawler()
    fingerprinter = create_instance(
        ScrapyZyteAPIRequestFingerprinter, settings=crawler.settings, crawler=crawler
    )
    request = Request(url, meta={"zyte_api": params})
    actual_fingerprint = fingerprinter.fingerprint(request)
    assert actual_fingerprint == fingerprint


def test_metadata():
    settings = {"JOB": "1/2/3"}
    crawler = get_crawler(settings_dict=settings)
    job_fingerprinter = create_instance(
        ScrapyZyteAPIRequestFingerprinter, settings=crawler.settings, crawler=crawler
    )

    crawler = get_crawler()
    no_job_fingerprinter = create_instance(
        ScrapyZyteAPIRequestFingerprinter, settings=crawler.settings, crawler=crawler
    )

    request1 = Request("https://example.com", meta={"zyte_api": {"echoData": "foo"}})
    request2 = Request("https://example.com", meta={"zyte_api": True})

    fingerprint1 = job_fingerprinter.fingerprint(request1)
    fingerprint2 = job_fingerprinter.fingerprint(request2)
    fingerprint3 = no_job_fingerprinter.fingerprint(request1)
    fingerprint4 = no_job_fingerprinter.fingerprint(request2)

    assert fingerprint1 == fingerprint2
    assert fingerprint3 == fingerprint4
    assert fingerprint1 == fingerprint3


def test_only_end_parameters_matter():
    """Test that it does not matter how a request comes to use some Zyte API
    parameters, that the fingerprint is the same if the parameters actually
    sent to Zyte API are the same."""

    settings = {
        "ZYTE_API_TRANSPARENT_MODE": True,
    }
    crawler = get_crawler(settings_dict=settings)
    transparent_fingerprinter = create_instance(
        ScrapyZyteAPIRequestFingerprinter, settings=crawler.settings, crawler=crawler
    )

    crawler = get_crawler()
    default_fingerprinter = create_instance(
        ScrapyZyteAPIRequestFingerprinter, settings=crawler.settings, crawler=crawler
    )

    request = Request("https://example.com")
    fingerprint1 = transparent_fingerprinter.fingerprint(request)
    fingerprint2 = default_fingerprinter.fingerprint(request)

    raw_request = Request(
        "https://example.com",
        meta={"zyte_api": {"httpResponseBody": True, "httpResponseHeaders": True}},
    )
    fingerprint3 = transparent_fingerprinter.fingerprint(raw_request)
    fingerprint4 = default_fingerprinter.fingerprint(raw_request)

    auto_request = Request("https://example.com", meta={"zyte_api_automap": True})
    fingerprint5 = transparent_fingerprinter.fingerprint(auto_request)
    fingerprint6 = default_fingerprinter.fingerprint(auto_request)

    assert fingerprint1 != fingerprint2

    assert fingerprint3 == fingerprint4
    assert fingerprint5 == fingerprint6

    assert fingerprint1 == fingerprint3
    assert fingerprint1 == fingerprint5


@pytest.mark.parametrize(
    "url1,url2,match",
    (
        (
            "https://example.com",
            "https://example.com",
            True,
        ),
        (
            "https://example.com",
            "https://example.com/",
            True,
        ),
        (
            "https://example.com/a",
            "https://example.com/b",
            False,
        ),
        (
            "https://example.com/?1",
            "https://example.com/?2",
            False,
        ),
        (
            "https://example.com/?a=1&b=2",
            "https://example.com/?b=2&a=1",
            True,
        ),
        (
            "https://example.com",
            "https://example.com#",
            True,
        ),
        (
            "https://example.com#",
            "https://example.com#1",
            True,
        ),
        (
            "https://example.com#1",
            "https://example.com#2",
            True,
        ),
    ),
)
def test_url(url1, url2, match):
    crawler = get_crawler()
    fingerprinter = create_instance(
        ScrapyZyteAPIRequestFingerprinter, settings=crawler.settings, crawler=crawler
    )
    request1 = Request(url1, meta={"zyte_api_automap": True})
    fingerprint1 = fingerprinter.fingerprint(request1)
    request2 = Request(url2, meta={"zyte_api_automap": True})
    fingerprint2 = fingerprinter.fingerprint(request2)
    if match:
        assert fingerprint1 == fingerprint2
    else:
        assert fingerprint1 != fingerprint2


def merge_dicts(*dicts):
    return {k: v for d in dicts for k, v in d.items()}


@pytest.mark.parametrize(
    "params,match",
    (
        # As long as browserHtml or screenshot are True, different fragments
        # make for different fingerprints, regardless of other parameters.
        *(
            (
                merge_dicts(body, headers, unknown, browser),
                False,
            )
            for body in (
                {},
                {"httpResponseBody": False},
                {"httpResponseBody": True},
            )
            for headers in (
                {},
                {"httpResponseHeaders": False},
                {"httpResponseHeaders": True},
            )
            for unknown in (
                {},
                {"unknown": False},
                {"unknown": True},
            )
            for browser in (
                {"browserHtml": True},
                {"screenshot": True},
                {"browserHtml": True, "screenshot": False},
                {"browserHtml": False, "screenshot": True},
                {"browserHtml": True, "screenshot": True},
            )
        ),
        # If neither browserHtml nor screenshot are enabled, different
        # fragments do *not* make for different fingerprints.
        *(
            (
                merge_dicts(body, headers, unknown, browser),
                True,
            )
            for body in (
                {},
                {"httpResponseBody": False},
                {"httpResponseBody": True},
            )
            for headers in (
                {},
                {"httpResponseHeaders": False},
                {"httpResponseHeaders": True},
            )
            for unknown in (
                {},
                {"unknown": False},
                {"unknown": True},
            )
            for browser in (
                {},
                {"browserHtml": False},
                {"screenshot": False},
                {"browserHtml": False, "screenshot": False},
            )
        ),
    ),
)
def test_url_fragments(params, match):
    crawler = get_crawler()
    fingerprinter = create_instance(
        ScrapyZyteAPIRequestFingerprinter, settings=crawler.settings, crawler=crawler
    )
    request1 = Request("https://toscrape.com#1", meta={"zyte_api": params})
    fingerprint1 = fingerprinter.fingerprint(request1)
    request2 = Request("https://toscrape.com#2", meta={"zyte_api": params})
    fingerprint2 = fingerprinter.fingerprint(request2)
    if match:
        assert fingerprint1 == fingerprint2
    else:
        assert fingerprint1 != fingerprint2
