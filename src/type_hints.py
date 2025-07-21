"""Types for the scraper."""

import typing as t


# CONFIGURATION TYPES
# ===================


class FileConfigEntry(t.TypedDict, total=False):
    """Configuration entry for a file to download."""
    selector: str
    url: str
    path: str


class ConfigEntry(t.TypedDict):
    """Configuration entry for a website and type."""
    url: str
    wait: str
    patterns: list[str]
    fields: dict[str, str]
    files: dict[str, FileConfigEntry]
    fallback: bool


# type alias for config dictionary (stored in config.json)
Config = dict[str, dict[str, ConfigEntry]]



# SCRAPED DATA TYPES
# ==================


class ScrapedFile(t.TypedDict, total=False):
    """Data of a scraped file, returned by the scraper."""
    result: str # "success" or "error: <error message>"
    url: str
    path: str
    size: int


class ScrapedComponentData(t.TypedDict, total=False):
    """Data of a scraped component, returned by the scraper.
    If some element is not found, the data field is set to None.
    """
    manuCode: str
    result: str # "success" or "error: <error message>"
    website: str
    type: str
    fields: dict[str, t.Optional[str]]
    files: dict[str, ScrapedFile]
