"""Tests for the configuration file operations."""

import sys
import json
import typing as t
import pathlib as pl
import copy

# adds the parent directory to the path
# this allows to run tests with the IDE play button
sys.path.append(str(pl.Path(__file__).parent.parent))
import src.config as config
from src.config import ReadConfig, WriteConfig
from src.type_hints import WebsiteEntry

# patches the config file path to a test file
CONFIG_FILE = config.CONFIG_FILE = pl.Path(__file__).parent.parent / "config-test.json"


# sample items, for testing
website1 = "molex.com"
entry1: WebsiteEntry = {
    "url": "https://www.molex.com/molex/products/part-detail/{manuCode}",
    "wait": "#part-details",
    "notFound": "img[alt='404 Error']",
    "fields": {
        "description": "h1",
        "fileUL": "td[data-key='ul']"
    },
    "files": { }
}

website2 = "te.com"
entry2: WebsiteEntry = {
    "keywords": [
      "te",
      "amp",
      "deutsch",
      "connector"
    ],
    "url": "https://www.te.com/en/*-{manuCode}.html", # wildcard inserted for testing
    "wait": "h1",
    "notFound": ".full-page-error",
    "fields": {
      "description": ".pdp-friendly-part-description h2",
      "fileUL": "[href*='UL_CERT']"
    },
    "files": {
      "drawing": {
        "selector": "a[data-doc-title='Customer Drawing']",
        "path": "te.com\\{manuCode}_drawing.pdf"
      },
      "image": {
        "selector": ".main-image img",
        "path": "te.com\\{manuCode}_image.{ext}"
      }
    }
}


def TestConfigReadWrite():
    """Test the config read/write functions."""

    # delete old test config file
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()

    # new config (should be empty)
    assert ReadConfig() == {}

    # try to write config (for first website)
    errors = WriteConfig(entry1, website1)
    assert errors == []

    # config should contain the first website
    assert ReadConfig() == {website1: entry1}

    # try to write config (for second website)
    errors = WriteConfig(entry2, website2)
    assert errors == []

    # config should contain both websites
    assert ReadConfig() == {website1: entry1, website2: entry2}

    # try to read config with domain filter
    assert ReadConfig(website1) == {website1: entry1}
    assert ReadConfig(website2) == {website2: entry2}

    # try to read config with domain filter (missing website)
    assert ReadConfig("missing.com") == {}

    # try to write config (for first website, deleting it)
    errors = WriteConfig(None, website1)
    assert errors == []

    # config should not contain the first website
    assert ReadConfig() == {website2: entry2}

    # try to write config (for first website, deleting it)
    errors = WriteConfig(None, website1)
    assert errors == [f"Website {website1} not found in config"]

    # config should still not contain the first website
    assert ReadConfig() == {website2: entry2}

    # try to write config (for second website, deleting it)
    errors = WriteConfig(None, website2)
    assert errors == []

    # config should be empty
    assert ReadConfig() == {}

    # delete test config file
    CONFIG_FILE.unlink()

    print("✅ Test Config Read/Write passed")


def TestConfigValidation():
    """Test the config validation functions."""

    # creates an empty config file
    ReadConfig()

    # generate invalid entries, in different ways

    # missing required properties
    requiredFields = ["url", "wait"]
    for key in requiredFields:
        wrongEntry = copy.deepcopy(entry1)
        del wrongEntry[key]
        assert WriteConfig(wrongEntry, website1) != []

    # additional invalid properties in entry
    wrongEntry = copy.deepcopy(entry1)
    wrongEntry["extra"] = "extra" # type: ignore
    assert WriteConfig(wrongEntry, website1) != []

    # invalid url: missing {manuCode} or *
    wrongEntry = copy.deepcopy(entry1)
    wrongEntry["url"] = "invalid"
    assert WriteConfig(wrongEntry, website1) != []

    # invalid types
    for key, correctType in [
        ("url", str),
        ("wait", str),
        ("notFound", str),
        ("fields", dict),
        ("files", dict),
        ("skipDirectDownload", bool),
    ]:
        wrongValue = next(x for x in ["invalid", 3] if type(x) != correctType)
        wrongEntry = copy.deepcopy(entry1)
        wrongEntry[key] = wrongValue # type: ignore
        assert WriteConfig(wrongEntry, website1) != []

    # missing required properties in files
    for key in ["path", "selector"]:
        wrongEntry = copy.deepcopy(entry2)
        del wrongEntry["files"]["drawing"][key] # type: ignore
        assert WriteConfig(wrongEntry, website1) != []

    # invalid additional properties in files
    wrongEntry = copy.deepcopy(entry2)
    wrongEntry["files"]["drawing"]["extra"] = "invalid" # type: ignore
    assert WriteConfig(wrongEntry, website1) != []

    # invalid types in files
    for key, correctType in [
        ("path", str),
        ("selector", str),
    ]:
        wrongEntry = copy.deepcopy(entry2)
        wrongEntry["files"]["drawing"][key] = 1 # type: ignore
        assert WriteConfig(wrongEntry, website1) != []

    # removes test config file
    CONFIG_FILE.unlink()

    print("✅ Test Config Validation passed")


if __name__ == "__main__":
    TestConfigReadWrite()
    TestConfigValidation()
