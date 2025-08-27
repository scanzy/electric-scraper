"""Tests for the scraper."""

import sys
import json
import typing as t
import pathlib as pl

# adds the parent directory to the path
# this allows to run tests with the IDE play button
sys.path.append(str(pl.Path(__file__).parent.parent))
from src.config import ReadConfig, WriteConfig
from src.scraper import ScrapeComponents, ScrapeComponent, GetCandidatesFromHints


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
    assert len(ReadConfig(domainOrUrl="missing")) == 0

    # reads only the first website
    firstWebsite = list(allConfig.keys())[0]
    config = ReadConfig(domainOrUrl=firstWebsite)
    print(f"Config for {firstWebsite}:")
    PretryPrintDict(config)

    # checks if config is empty
    if len(config) == 0:
        print(f"No types found for website {firstWebsite}.")
        return

    # writes config
    WriteConfig(config[firstWebsite], domain=firstWebsite)
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


def TestNotFound():
    """Test the not found functionality."""

    # missing component
    result = ScrapeComponent(manuCode="missing", hints=["molex.com"], files = [], closeBrowser=True)
    PretryPrintDict(result)


if __name__ == "__main__":
    pass

    #PretryPrintDict(ReadConfig())
    #TestConfigReadWrite()
    #TestMatching()
    #TestScraper()
    #TestNotFound()
