"""Types for the scraper."""

import typing as t


# CONFIGURATION TYPES
# ===================


class FileConfigEntry(t.TypedDict, total=False):
    """Configuration entry for a file to download."""
    selector: str  # CSS selector to find download link (alternative to url)
    url: str       # Direct URL template (alternative to selector)
    path: str      # Target file path (relative to basePath) with placeholders


class WebsiteEntry(t.TypedDict, total=False):
    """Configuration entry for a website."""
    keywords: list[str]
    url: str
    wait: str
    notFound: str
    fields: dict[str, str]
    files: dict[str, FileConfigEntry]


# type alias for config dictionary (stored in config.json)
Config = dict[str, WebsiteEntry]



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
    If some element is not found, the corresponding field is set to None.
    """
    manuCode: str
    result: str # "success" or "error: <error message>"
    matchedHints: list[str]
    url: str
    fields: dict[str, str | None]
    files: dict[str, ScrapedFile]
