"""Configuration file operations."""

import os
import logging as log
import pathlib as pl
import json

from src.website import MatchUrlToDomains, DomainFromUrl
from src.type_hints import Config, WebsiteEntry
from src.validation import GetConfigErrors


# config file in the root of the project
CONFIG_FILE = pl.Path(__file__).parent.parent / "electric-scraper-config.json"
SCHEMA_FILE = pl.Path(__file__).parent.parent / "config-schema.json"

# configures logging
log.basicConfig(format="%(name)s: %(message)s")


# JSON FILE OPERATIONS
# ====================


def WriteJsonToFile(jsonData: dict, file: pl.Path) -> None:
    """Writes a dictionary to a json file."""
    with open(file, "w") as f:
        json.dump(jsonData, f, indent=2)


def ReadJsonFromFile(file: pl.Path) -> dict:
    """Reads a json file and return a dictionary."""

    # if file does not exist, creates it
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f, indent=2)

    # reads file and loads json
    with open(file, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {file}: {e}")



# CONFIG READING AND WRITING
# ==========================


def ReadConfigSafe(domainOrUrl: str = "") -> Config:
    """Read the configuration file, filtering by website domain, if specified.
    Writes eventual errors into the returned config, in the "errors" key.
    """

    # reads config
    config = ReadJsonFromFile(CONFIG_FILE)

    # includes only the specified website, if present
    if domainOrUrl:
        try:
            domain = MatchUrlToDomains(domainOrUrl, list(config.keys()))
            config = {domain: config[domain]}
        except ValueError:
            return {}

    # detects errors, adding them to the returned config
    errors = GetConfigErrors(config)
    if errors:
        config["errors"] = errors

    return config


def ReadConfig(domainOrUrl: str = "") -> Config:
    """Reads the configuration file, filtering by website domain, if specified.
    Throws an exception if the configuration is invalid.
    """

    # reads config and returns if no errors
    config = ReadConfigSafe(domainOrUrl)
    if "errors" not in config:
        return config
    
    # raises an exception with the errors
    raise ValueError(f"Invalid configuration. {len(config['errors'])} errors: "
        "\n".join(config['errors']))


def WriteConfig(entry: WebsiteEntry | None, domain: str) -> list[str]:
    """Writes (or overwrites) an entry in the configuration file.
    Returns a list of errors, if any. Returns empty list if no errors.
    To delete an entry, set the entry parameter to None.
    Specify the domain of the website excluding subdomains and www.
    For example, use "farnell.com" instead of "it.farnell.com".
    """

    # extracts domain from URL
    domain = DomainFromUrl(domain)

    # if entry is None, deletes the entry
    if entry is None:
        config = ReadJsonFromFile(CONFIG_FILE)

        # deletes entry
        try:
            del config[domain]
        except KeyError as e:
            return [f"Website {domain} not found in config"]
        
        # writes updatedconfig
        WriteJsonToFile(config, CONFIG_FILE)
        return []

    # checks validity of entry
    errors = GetConfigErrors({domain: entry})
    if errors:
        return errors

    # writes entry to config
    config = ReadJsonFromFile(CONFIG_FILE)
    config[domain] = entry
    WriteJsonToFile(config, CONFIG_FILE)
    return []
