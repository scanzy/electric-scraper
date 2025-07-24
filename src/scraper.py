"""Main scraper functions."""

import typing as t
import html2text as h2t
import logging as log

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from src.type_hints import ScrapedComponentData
from src.browser import GetBrowser, WaitElement, CloseBrowser
from src.config import ReadConfig, MatchPatterns, FillMissingConfig
from src.files import ScrapeFiles


# configures logging
log.basicConfig(level=log.INFO, format='%(asctime)s - %(message)s')
logger = log.getLogger(__name__)


def ScrapeComponent(
    manuCode: str,
    website: t.Optional[str] = None,
    type:    t.Optional[str] = None,
    fields:    t.Optional[dict[str, t.Optional[str]]] = None,
    files:   t.Optional[dict[str, dict[str, t.Optional[str]]]] = None,
    format:  t.Literal["html", "md", "txt"] = "txt",
    closeBrowser: bool = True,
) -> ScrapedComponentData:
    """Scrapes data of a component from a website. See ScrapeComponents for more info."""

    # reads configuration, filtering by website and type, if specified
    config = ReadConfig(website=website, type=type)

    # matches manuCode patterns, if needed
    if website is None or type is None:
        website, type = MatchPatterns(manuCode, config)
        logger.info(f"Pattern matched - website: {website}, type: {type}")

    # gets config entry
    entry = config.get(website, {}).get(type, None)
    if entry is None:
        raise ValueError(f"No config entry found for website: {website}, type: {type}")

    # fills missing parameters
    filledFields, filledFiles = FillMissingConfig(entry, fields, files)

    try:
        # opens browser, or gets existing one
        driver = GetBrowser()

        # opens url
        url = entry["url"].format(manuCode=manuCode)
        logger.info(f"Navigating to URL: {url}")
        driver.get(url)
        
        # waits for page to load
        WaitElement(driver, entry["wait"])   

        # scrapes fields
        logger.info("Scraping fields...")
        scrapedFields = ScrapeFields(driver, filledFields, format)
        
        # scrapes files
        logger.info("Scraping files...")
        scrapedFiles = ScrapeFiles(driver, filledFiles,
            data = {**scrapedFields, "manuCode": manuCode, "ext": "{ext}"})

        result: ScrapedComponentData = {
            "manuCode": manuCode,
            "website": website,
            "type": type,
            "fields": scrapedFields,
            "files": scrapedFiles,
        }
        logger.info(f"Scraping completed successfully for {manuCode}")
        return result

    # returns error if something goes wrong
    except Exception as e:
        logger.error(f"Error during scraping {manuCode}: {e}")
        return {
            "manuCode": manuCode,
            "result": f"error: {e}",
            "website": website,
            "type": type,
        }
    
    # closes browser if needed
    finally:    
        if closeBrowser:
            CloseBrowser()


def ScrapeFields(driver: webdriver.Firefox,
    fields: dict[str, str],
    format: t.Literal["html", "md", "txt"],
) -> dict[str, t.Optional[str]]:
    """Scrape text data from the current page, using the specified css selectors.
    Input parameter "fields": dictionary with key=<field name>, value=<css selector>.
    Returns: dictionary with key=<field name>, value=<scraped data>
    If some element is not found, field value is set to None.
    """

    # processes every field
    scrapedData = {}
    for key, selector in fields.items():

        # tries to find element
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            logger.info(f"Element for '{key}' field not found: {selector}")
            scrapedData[key] = None
            continue

        # gets data in the specified format
        if format in ["html", "md"]:
            html = element.get_attribute("innerHTML") or ""
            scrapedData[key] = html if format == "html" else h2t.html2text(html)

        # plain text (gets url if element has no text)
        elif format == "txt":
            scrapedData[key] = element.text or element.get_attribute("href")
        else:
            raise ValueError(f"Invalid format: {format}")
        
        logger.info(f"Scraped data for '{key}': {scrapedData[key]}")

    return scrapedData


def ScrapeComponents(
    manuCodes: list[str],
    website: t.Optional[str] = None,
    type:    t.Optional[str] = None,
    fields:  t.Optional[dict[str, t.Optional[str]]] = None,
    files:   t.Optional[dict[str, dict[str, t.Optional[str]]]] = None,
    format:  t.Literal["html", "md", "txt"] = "txt",
    closeBrowser: bool = True,
) -> list[ScrapedComponentData]:
    """Scrapes data of components from configured websites.
    Parameters:
    - manuCodes: list of manufacturer codes (required)
    - website: website to scrape (example.com), do not include www. or http:// or https://
    - type: type of component (connector, resistor, etc.)
    - fields: dictionary of data to scrape (key: field name, value: css selector)
    - files: dictionary of files to scrape (see below)
    - format: format of the data to scrape (html, md, txt)
    - closeBrowser: whether to close the browser after scraping (default = True)

    Files dictionary:
    - key: file identifier (e.g. "datasheet")
    - value: dictionary with:
        - "selector": css selector to find the file
        - "path": absolute path to save the file

    NOTE: set parameters to None to read them from config file.
    Recommended for css selectors and file paths.
    """
    return [
        ScrapeComponent(manuCode, website, type, fields, files, format,
            # if configured, closes browser only after all components are scraped
            closeBrowser=closeBrowser and codeIndex == len(manuCodes) - 1)
        for codeIndex, manuCode in enumerate(manuCodes)
    ]
