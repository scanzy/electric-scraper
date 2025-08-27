"""Tests for domain matching functions."""

import sys
import pathlib


# adds the parent directory to the path
# this allows to run tests with the IDE play button
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from src.website import MatchUrlToDomains, DomainFromUrl
from tests.utils import RunTests


KNOWN_DOMAINS = ["farnell.com", "mouser.com", "digikey.com", "sws.co.jp"]


# DomainFromUrl test cases: (url, expected_result)
CASES_DOMAIN_FROM_URL = [
    (["https://www.farnell.com/products"],    "farnell.com"),     # url with www
    (["https://it.farnell.com/products"],     "it.farnell.com"),  # simple subdomain
    (["http://mouser.com/test"],              "mouser.com"),      # url without www
    (["https://DIGIKEY.COM/search"],          "digikey.com"),     # uppercase url
    (["https://www.example.org/long/path/x"], "example.org"),     # url with long path
]

# MatchUrlToDomains success cases: (url, expected_result), using KNOWN_DOMAINS
CASES_MATCH_URL_TO_DOMAINS = [

    # success cases
    (["https://www.farnell.com/products"],    "farnell.com"),     # direct match
    (["https://it.farnell.com/products"],     "farnell.com"),     # simple subdomain
    (["https://shop.eu.farnell.com/catalog"], "farnell.com"),     # multiple subdomain
    (["https://test.sws.co.jp/products"],     "sws.co.jp"),       # japanese domain
    (["https://IT.FARNELL.COM/products"],     "farnell.com"),     # case insensitive
    (["https://mouser.com/products"],         "mouser.com"),      # url without www

    # error cases
    (["https://www.amazon.com/products"],      ValueError),       # unknown domain
    (["https://digikey.de/products"],          ValueError),       # slightly different domain
    (["https://nell.com/test"],                ValueError),       # part of domain
    (["https://digikey.it.suffix/test"],       ValueError),       # domain with suffix
]


def RunAllTests():
    """Runs all tests for the domain matching functions."""
    
    print("=== Automatic Tests for Domain Matching Functions ===")
    
    # test DomainFromUrl function
    success1 = RunTests("DomainFromUrl", DomainFromUrl, CASES_DOMAIN_FROM_URL)
    
    # test MatchUrlToDomains function (success and error cases combined)
    success2 = RunTests("MatchUrlToDomains",
        lambda url: MatchUrlToDomains(url, KNOWN_DOMAINS), CASES_MATCH_URL_TO_DOMAINS)
    
    # final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY:")
    print(f"✓ DomainFromUrl: {'PASS' if success1 else 'FAIL'}")
    print(f"✓ MatchUrlToDomains: {'PASS' if success2 else 'FAIL'}")
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! Functions work correctly.")
    else:
        print("\n❌ Some tests failed. Check implementation.")
    
    print(f"{'='*60}")


if __name__ == "__main__":
    RunAllTests()
