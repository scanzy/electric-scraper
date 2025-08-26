"""Configuration file operations."""

import os
import json
import typing as t
import pathlib as pl

from src.type_hints import Config, WebsiteEntry


# config file in the root of the project
CONFIG_FILE = pl.Path(__file__).parent.parent / "electric-scraper-config.json"


# JSON FILE OPERATIONS
# ====================


def WriteJsonToFile(jsonData: dict) -> None:
    """Write a dictionary to a json file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(jsonData, f, indent=2)


def ReadJsonFromFile() -> dict:
    """Read a json file and return a dictionary."""

    # if file does not exist, create it
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({}, f, indent=2)

    # read file
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)



# CONFIG READING AND WRITING
# ==========================


def ReadConfig(website: str = "") -> Config:
    """Read the configuration file, filtering by website domain, if specified."""

    # reads config
    config = ReadJsonFromFile()

    # includes only the specified website, if present
    if website != "":
        config = {website: config[website]} if website in config else {}

    # checks validity of config
    for website, entry in config.items():
        try:
            CheckEntryValid(website, entry)

        # if error, add to entry
        except ValueError as e:
            entry["error"] = str(e)

    return config


def WriteConfig(entry: WebsiteEntry, website: str) -> bool:
    """Overwrite an entry in the configuration file.
    As website, use the domain of the website, not the full URL.
    """

    # checks validity of entry
    CheckEntryValid(website, entry)

    # writes entry to config
    config = ReadJsonFromFile()
    config[website] = entry
    WriteJsonToFile(config)
    return True



# CONFIG VALIDATION
# =================


def CheckObjectStructure(obj: t.Any, required: dict[str, type], name: str) -> None:
    """Checks if an object has the required structure.
    Raises an error for invalid keys or types.
    """

    # processed keys are removed from this list, so that unknown keys will remain
    entryKeys = list(obj.keys())

    # checks required keys
    for key, type in required.items():

        # checks if the key is present
        if key not in obj:
            raise ValueError(f"Invalid {name}: key '{key}' is required, but not present")

        # checks if the value is of the correct type
        if not isinstance(obj[key], type):
            raise ValueError(f"Invalid value '{obj[key]}' for key '{key}' of {name}: "
                f"must be of type '{type.__name__}', not {type(obj[key]).__name__}")

        # removes checked key from the list
        entryKeys.remove(key)

    # checks remaining keys, which are unknown
    if entryKeys:
        raise ValueError(f"Invalid config: unknown keys {entryKeys} of {name}")


def CheckEntryValid(website: str, entry: WebsiteEntry) -> None:
    """Checks if a configuration entry for a website is valid.
    Raises an error for invalid keys or types.
    """

    # checks structure of entry
    required = {
        "keywords": list,
        "url": str,
        "wait": str,
        "notFound": str,
        "fields": dict,
        "files": dict,
    }
    CheckObjectStructure(entry, required, f"website '{website}'")

    # checks keywords are strings
    for keyword in entry["keywords"]:
        if not isinstance(keyword, str):
            raise ValueError(f"Invalid keyword '{keyword}' (type: {type(keyword).__name__}) "
                f"for website '{website}': must be string")

    # check structure of fields
    for field, selector in entry["fields"].items():

        if not isinstance(field, str):
            raise ValueError(f"Invalid field name '{field}' (type: {type(field).__name__}) "
                f"for website '{website}': must be string")
        
        if not isinstance(selector, str):
            raise ValueError(f"Invalid selector '{selector}' (type: {type(selector).__name__}) "
                f"for website '{website}': selectors must be strings")

    # check structure of files
    for file, fileConfig in entry["files"].items():

        if "path" not in fileConfig:
            raise ValueError(f"File '{file}' of website '{website}' must have 'path' field")

        hasSelector = "selector" in fileConfig
        hasUrl = "url" in fileConfig
            
        # check that either 'selector' or 'url' is present (but not both)
        if not (hasSelector or hasUrl) or (hasSelector and hasUrl):
            raise ValueError(f"File '{file}' of website '{website}' must have either 'selector' "
                "or 'url' field, but not both")
            
        # check types
        if hasSelector and not isinstance(fileConfig["selector"], str):
            raise ValueError(f"Invalid selector for file '{file}' of website '{website}': must be string")
        if hasUrl and not isinstance(fileConfig["url"], str):
            raise ValueError(f"Invalid url for file '{file}' of website '{website}': must be string")
        if not isinstance(fileConfig["path"], str):
            raise ValueError(f"Invalid path for file '{file}' of website '{website}': must be string")
