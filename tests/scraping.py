"""Tests for the scraper."""

import sys
import json
import typing as t
import pathlib as pl

# adds the parent directory to the path
# this allows to run tests with the IDE play button
sys.path.append(str(pl.Path(__file__).parent.parent))

from server import ReadDocs, ReadNewWebsiteGuide
from src.config import ReadConfig, WriteConfig
from src.scraper import ScrapeComponents, ScrapeComponent, GetCandidatesFromHints


def TestReadDocs():
    """Tests the read docs functionality, ensuring it's not empty."""
    docs = ReadDocs()
    assert docs is not None and len(docs) > 0
    print(docs)


def TestReadNewWebsiteGuide():
    """Tests the read new website guide functionality, ensuring it's not empty."""

    steps = list(range(0, 7))
    for step in steps:

        # reads guide, ensuring it's not empty
        guide = ReadNewWebsiteGuide(step)
        assert guide is not None and len(guide) > 0

        # prints guide
        print(f"{'=' * 10} Step {step} {'=' * 10}")
        print(guide)
        print()


def PretryPrintDict(data: t.Mapping) -> None:
    """Pretty prints a dictionary."""
    print(json.dumps(data, indent=2))


def TestMatching():
    """Test the matching functionality."""
    
    hints = {
        "website": ["molex.com"],
        "keyword": ["te"],
        "both": ["molex", "molex.com"],
        "duplicate": ["te", "te", "molex.com"],
    }

    # tests different combinations of hints
    config = ReadConfig()
    for testName, keywords in hints.items():
        print(f"Matching test '{testName}' with hints {keywords}:")
        candidates = GetCandidatesFromHints(keywords, config)
        for candidate in candidates:
            print(f"- [{candidate.score}] {candidate.domain}: {candidate.matchedHints}")


def TestScraper():
    """Test the scraper."""

    # existing components
    codes = ["428160212", "428160612", "428180512", "02061101"]
    results = ScrapeComponents(manuCodes=codes, hints=["molex.com"], files = [], closeBrowser=True)
    for r in results:
        PretryPrintDict(r)


def TestScrapeFiles():
    """Test the file download functionality."""

    # existing components
    codes = ["DTP04-4P", "DTP06-4S", "DTM06-12SA"]
    results = ScrapeComponents(manuCodes=codes, hints=["te.com"], basePath="tests/downloads", closeBrowser=True)
    for r in results:
        PretryPrintDict(r)


def TestNotFound():
    """Test the not found functionality."""

    # missing component
    result = ScrapeComponent(manuCode="missing", hints=["molex.com"], files = [], closeBrowser=True)
    PretryPrintDict(result)


if __name__ == "__main__":

    #TestReadDocs()
    #TestReadNewWebsiteGuide()
    #PretryPrintDict(ReadConfig())
    #TestMatching()
    #TestScraper()
    TestScrapeFiles()
    #TestNotFound()
