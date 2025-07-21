"""Tests for the scraper."""

import json
from src.config import ReadConfig, WriteConfig
from src.scraper import ScrapeComponents


def PretryPrintDict(data: dict) -> None:
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
    assert len(ReadConfig(type="missing")) == 0
    assert len(ReadConfig(website="missing")) == 0
    assert len(ReadConfig(website="missing", type="missing")) == 0

    # reads only the first website
    firstWebsite = list(allConfig.keys())[0]
    config = ReadConfig(website=firstWebsite)
    print(f"Config for {firstWebsite}:")
    PretryPrintDict(config)

    # checks if config is empty
    if len(config) == 0:
        print(f"No types found for website {firstWebsite}.")
        return

    # reads only the first type
    firstType = list(config[firstWebsite].keys())[0]
    config = ReadConfig(type=firstType)
    print(f"Config for {firstType}:")
    PretryPrintDict(config)

    # reads only the first website and type
    config = ReadConfig(website=firstWebsite, type=firstType)
    print(f"Config for {firstWebsite} {firstType}:")
    PretryPrintDict(config)

    # writes config
    WriteConfig(config[firstWebsite][firstType], website=firstWebsite, type=firstType)
    print(f"Config for {firstWebsite} {firstType} written to file.")


def TestScraper():
    """Test the scraper."""

    # only for testing purposes
    codes = ["428160212", "428160612", "428180512", "02061101"]
    ScrapeComponents(manuCodes=codes, website="molex.com", closeBrowser=False)


if __name__ == "__main__":
    #TestConfigReadWrite()
    TestScraper()
