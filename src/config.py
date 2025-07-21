"""Configuration file operations."""

import os
import json
import re
import typing as t

from src.type_hints import Config, ConfigEntry, FileConfigEntry


CONFIG_FILE = "electric-scraper-config.json"


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


def ReadConfig(website: t.Optional[str] = None, type: t.Optional[str] = None) -> Config:
    """Read the configuration file, filtering by website and type, if specified."""

    # reads config
    config = ReadJsonFromFile()

    # includes only the specified website, if present
    if website is not None:
        config = {website: config[website]} if website in config else {}
        
    # if type is not specified, no further filtering is required
    if type is None: return config

    # includes only the specified type for every website, if present
    return {
        _website: {type: websiteConfig[type]}
        for _website, websiteConfig in config.items()
        if type in websiteConfig
    }


def WriteConfig(entry: ConfigEntry, website: str, type: str) -> bool:
    """Overwrite an entry in the configuration file."""

    config = ReadJsonFromFile()
    config[website][type] = entry
    WriteJsonToFile(config)
    return True



# CONFIG ENTRY MATCHING AND FILLING
# ================================


def MatchPatterns(manuCode: str, config: Config) -> t.Tuple[str, str]:
    """Matches a manuCode to a pattern in the config.
    Returns the first matching website and type."""

    # for every website and type
    for website, websiteConfig in config.items():
        for type, typeConfig in websiteConfig.items():

            # check if the manuCode matches any pattern
            for pattern in typeConfig["patterns"]:
                if re.match(pattern, manuCode):
                    return website, type

    # if no match, return empty strings
    return "", ""


def FillMissingConfig(entry: ConfigEntry,
    data: t.Optional[dict], files: t.Optional[dict],
) -> t.Tuple[dict[str, str], dict[str, FileConfigEntry]]:
    """Fills missing config for data and files parameters. Returns filled data and files."""

    # fills missing parameters from config
    if data is None:
        data = entry.get("fields", {})
    if files is None:
        files = entry.get("files", {})

    # fills missing values in entries of "data" parameter
    # example: data = {"field1": None, ...} -> data = {"field1": "selector1", ...}
    for field, selector in data.items():
        if selector is None:
            data[field] = entry.get("fields", {}).get(field, None)

    # fills missing config for entries of "files" parameter
    # example: files = {"file1": None, ...} -> files = {"file1": { <data> }, ...}
    for file, fileConfig in files.items():

        # gets file entry from config
        filesEntry = entry.get("files", {}).get(file, {})

        # if file entry is None, use the one from config
        if fileConfig is None:
            files[file] = filesEntry
            continue

        # fills missing values in entries of file config
        # example: fileConfig = {"selector": None, ...} -> fileConfig = {"selector": "selector1", ...}
        for key, value in fileConfig.items():
            if value is None:
                fileConfig[key] = filesEntry.get(key, None)

    return data, files
