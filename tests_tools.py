"""Tests for the scraper."""

import json
import typing as t
from src.config import ReadConfig, WriteConfig
from src.scraper import ScrapeComponents, ScrapeComponent, GetRankedCandidates


def PretryPrintDict(data: t.Mapping) -> None:
    """Pretty prints a dictionary."""
    print(json.dumps(data, indent=2))


def TestConfigReadWrite():
    """Test the config read/write functions."""

    # reads all config
    allConfig = ReadConfig()
    print("All config:")
    PretryPrintDict(allConfig)

    # checks if config is empty
    if len(allConfig) == 0:
        print("No websites found in config.")
        return

    # reads missing type and/or website
    assert len(ReadConfig(website="missing")) == 0

    # reads only the first website
    firstWebsite = list(allConfig.keys())[0]
    config = ReadConfig(website=firstWebsite)
    print(f"Config for {firstWebsite}:")
    PretryPrintDict(config)

    # checks if config is empty
    if len(config) == 0:
        print(f"No types found for website {firstWebsite}.")
        return

    # writes config
    WriteConfig(config[firstWebsite], website=firstWebsite)
    print(f"Config for {firstWebsite} written to file.")


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
        candidates = GetRankedCandidates(keywords, config)
        for candidate in candidates:
            print(f"- [{candidate.score}] {candidate.website}: {candidate.matchedHints}")


def TestScraper():
    """Test the scraper."""

    # existing components
    codes = ["428160212", "428160612", "428180512", "02061101"]
    results = ScrapeComponents(manuCodes=codes, hints=["molex.com"], files = [], closeBrowser=True)
    for r in results:
        PretryPrintDict(r)


def TestNotFound():
    """Test the not found functionality."""

    # missing component
    result = ScrapeComponent(manuCode="missing", hints=["molex.com"], files = [], closeBrowser=True)
    PretryPrintDict(result)


if __name__ == "__main__":
    #print(ReadConfig())
    #TestConfigReadWrite()
    #TestMatching()
    #TestScraper()
    #TestNotFound()
