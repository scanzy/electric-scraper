"""Main scraper functions."""

import logging as log
import typing as t
import html2text as h2t

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, InvalidSessionIdException

from src.config import ReadConfig
from src.browser import GetBrowser, WaitElement, CloseBrowser, RetryOnException, ResetBrowser
from src.files import ScrapeFiles
from src.website import MatchUrlPatternToWebResults, GetCandidatesFromHints, GetCandidatesFromWebSearch, MatchUrlToDomains
from src.type_hints import ScrapedComponentData, WebsiteEntry


logger = log.getLogger(__name__)
logger.setLevel(log.INFO)


# SCRAPING FROM WEBSITE
# =====================


class ComponentNotFoundError(Exception):
    """Raised when a component is not found on the website."""
    pass


@RetryOnException(on=InvalidSessionIdException, init=ResetBrowser)
def ScrapeFromWebsite(
    manuCode: str,  
    entry: WebsiteEntry,
    files: t.Optional[list[str]],
    basePath: str,
    matchedHints: list[str], # included in result on success
    format: t.Literal["html", "md", "txt"],
    closeBrowser: bool,
) -> ScrapedComponentData:
    """Scrapes data of a component from a website, retrying on session expiration."""

    # detects if url is a pattern (contains *)
    urlConfig = entry["url"] # type: ignore  # required field
    if "*" in urlConfig:
        url = MatchUrlPatternToWebResults(urlConfig, manuCode, matchedHints)
        if url == "":
            raise ComponentNotFoundError("Unable to match url pattern to web search results")

    # if the url is not a pattern, it is a template
    else:
        # formats url replacing {manuCode} with the provided manuCode
        url = urlConfig.format(manuCode=manuCode)

    # opens browser, or gets existing one
    driver = GetBrowser()

    # navigates to the found url
    logger.info(f"Navigating to URL: {url}")
    driver.get(url)
    
    # composes selector to wait for content or not found page
    waitSelector = entry["wait"] # type: ignore  # required field
    notFoundSelector = entry.get("notFound", "") # optional field
    if notFoundSelector:
        waitSelector += ", " + notFoundSelector
    
    # waits for page to load
    try:
        WaitElement(driver, waitSelector) 
    except RuntimeError as e:

        # raises error if no known element is found
        # this indicates website not properly configured
        if notFoundSelector:
            raise RuntimeError(
                f"Could not find 'wait' nor 'notFound' element in page: {e}")
        
        # if no notFound selector is configured, the timeout indicates page not found
        # this is not a configuration error, but an invalid component code
        else:
            raise ComponentNotFoundError from e

    # detects not-found page, if configured
    if notFoundSelector:
        try: 
            driver.find_element(By.CSS_SELECTOR, notFoundSelector)
            raise ComponentNotFoundError("Detected component-not-found page")
        except NoSuchElementException:
            pass

    # scrapes fields, if any configured
    fieldsConfig = entry.get("fields", {})
    logger.debug(f"Scraping {len(fieldsConfig)} fields...")
    scrapedFields = ScrapeFields(driver, fieldsConfig, format)
    
    # gets files config, filtering by files parameter
    filesConfig = entry.get("files", {})
    if files is not None:
        # TODO: detect if some file tags are not configured, and show warning
        filesConfig = {key: value for key, value in filesConfig.items() if key in files}

    # scrapes files, as configured
    logger.debug(f"Scraping {len(filesConfig)} files...")
    scrapedFiles = ScrapeFiles(driver, basePath, filesConfig,
        data = {**scrapedFields, "manuCode": manuCode, "ext": "{ext}"},
        skipDirectDownload = entry.get("skipDirectDownload", False),
    )

    # closes browser, if configured
    if closeBrowser:
        CloseBrowser()
    
    result: ScrapedComponentData = {
        "manuCode": manuCode,
        "matchedHints": matchedHints,
        "url": url,
        "fields": scrapedFields,
        "files": scrapedFiles,
    }
    logger.info(f"Scraping for '{manuCode}' completed successfully")
    return result


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



# SCRAPING TOOLS
# ==============


def ScrapeComponent(
    manuCode: str,
    hints: list[str] = [],
    files: t.Optional[list[str]] = None,
    basePath: str = "",
    format:  t.Literal["html", "md", "txt"] = "txt",
    closeBrowser: bool = True,
) -> ScrapedComponentData:
    """Scrapes data of a component from a website. See ScrapeComponents for more info."""

    # reads configuration (website -> entry)
    config = ReadConfig()

    # matches websites against hints, and sorts them by score
    candidates = GetCandidatesFromHints(hints, config)

    # if fails, try web search
    if len(candidates) == 0:
        logger.info(f"No known website matching hints {hints}, trying web search...")
        candidates = GetCandidatesFromWebSearch(manuCode, hints)

    # if still no candidates, return error
    if len(candidates) == 0:
        return {
            "manuCode": manuCode,
            "result": f"error: no known website found for '{manuCode}'. " + 
                "Try using different hints, or add a new website to the config file.",
        }

    # saves errors for each candidate website
    attempts: dict[str, str] = {} # website -> error message

    # for each candidate website
    for candidate in candidates:

        # only for known websites (in config file)
        try:
            domain = MatchUrlToDomains(candidate.domain, list(config.keys()))
            websiteEntry = config[domain]
        except ValueError:
            logger.warning(f"Unknown candidate website '{candidate.domain}', skipping...")
            attempts[candidate.domain] = "Unknown candidate website"
            continue
    
        # try to scrape from each one
        try:
            return ScrapeFromWebsite(manuCode, websiteEntry, files, basePath,
                candidate.matchedHints, format, closeBrowser)

        # skip to next candidate if component not found
        except ComponentNotFoundError as e:
            logger.info(f"Component '{manuCode}' not found on '{candidate.domain}'")
            attempts[candidate.domain] = type(e).__name__ + ": " + str(e)
            continue
            
        # returns error if something goes wrong
        except Exception as e:
            logger.error(f"Error during scraping '{manuCode}' from '{candidate.domain}': {e}")
            attempts[candidate.domain] = type(e).__name__ + ": " + str(e)
            continue

    # closes browser, if configured
    if closeBrowser:
        CloseBrowser()
    
    # if all fails, return error
    return {
        "manuCode": manuCode,
        "result": f"error: unable to scrape '{manuCode}' from any known website. " +
            " | ".join(f"[{domain}]: {error}" for domain, error in attempts.items()),
    }


def ScrapeComponents(
    manuCodes: list[str],
    hints: list[str] = [],
    files: t.Optional[list[str]] = None,
    basePath: str = "",
    format: t.Literal["html", "md", "txt"] = "txt",
    closeBrowser: bool = True,
) -> list[ScrapedComponentData]:
    """Scrapes data of components from configured websites.
    Parameters:
    - manuCodes: list of manufacturer codes (required)
    - hints: websites or keywords to match the website to scrape from (see below)
    - files: list of file tags to scrape (None = all configured files)
    - basePath: base path to save the files
    - format: format of the data to scrape (html, md, txt)
    - closeBrowser: whether to close the browser after scraping (default = True)

    In hints, you can specify a (mixed) list of:
    - websites: e.g. example.com, do not include www. or http:// or https://
    - keywords: entries to search in config file, e.g. component brands
    """
    return [
        ScrapeComponent(manuCode, hints, files, basePath, format,
            # if configured, closes browser only after all components are scraped
            closeBrowser=closeBrowser and codeIndex == len(manuCodes) - 1)
        for codeIndex, manuCode in enumerate(manuCodes)
    ]
