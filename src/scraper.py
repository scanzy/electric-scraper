"""Main scraper functions."""

import re
import typing as t
import html2text as h2t
import logging as log

from ddgs import DDGS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from src.type_hints import ScrapedComponentData, Config, WebsiteEntry
from src.browser import GetBrowser, WaitElement, CloseBrowser
from src.config import ReadConfig
from src.files import ScrapeFiles


# configures logging
log.basicConfig(level=log.INFO, format='%(asctime)s - %(message)s')
logger = log.getLogger(__name__)




# CANDIDATE WEBSITES MATCHING
# ===========================


class CandidateWebsite(t.NamedTuple):
    """Candidate website for scraping, with score and matched hints."""
    website: str
    score: int
    matchedHints: list[str]


def WebsiteFromUrl(url: str) -> str:
    """Extracts the website from a url.
    Example: https://www.molex.com/molex/products/family/10362 -> molex.com
    """
    return url.split("/")[2].replace("www.", "")


def MatchWebsiteToHints(lowerHints: list[str], lowerWebsite: str, entry: WebsiteEntry) -> CandidateWebsite:
    """Matches the hints against the website, calculating the score."""

    score = 0
    matchedHints = []
    for hint in lowerHints:

        # +5 if hint exactly matches the website domain
        if hint == lowerWebsite:
            score += 5
            if hint not in matchedHints:
                matchedHints.append(hint)

        # +3 for each hint that exactly matches a configured keyword
        if hint in entry["keywords"]:
            score += 3
            if hint not in matchedHints:
                matchedHints.append(hint)

    logger.debug(f"Matched website '{lowerWebsite}' to hints {matchedHints} with score {score}")
    return CandidateWebsite(lowerWebsite, score, matchedHints)


def GetRankedCandidates(hints: list[str], config: Config) -> list[CandidateWebsite]:
    """Matches the provided hints against the configured websites, sorting them by score."""

    # preprocess hints: lowercase
    # NOTE: we do not remove duplicate hints, to count them multiple times in score
    # the user can specify some hints multiple times to give them more score
    lowerHints = [hint.lower() for hint in hints]

    # matches hints against websites
    candidates = [MatchWebsiteToHints(lowerHints, website, entry)
        for website, entry in config.items()]

    # removes websites with no matched hints (0 score)
    candidates = [candidate for candidate in candidates if candidate.score > 0]

    # sorts websites by score
    return sorted(candidates, key=lambda x: x.score, reverse=True)


def GetCandidatesFromWebSearch(manuCode: str, hints: list[str]) -> list[CandidateWebsite]:
    """Gets candidate websites for a component, searching online."""

    # composes the search query
    query = manuCode
    if hints: query += " " + " ".join(hints)

    # searches the web, composing candidates
    candidates = []
    for result in DDGS().text(query, max_results=5):

        # extracts website from url, removing protocol and www  
        # https://www.molex.com/... -> molex.com
        website = result["href"].split("/")[2]
        website = website.replace("www.", "")

        # adds candidate, if not already in list
        if website not in candidates:
            candidates.append(website)

    # logs candidates
    logger.info(f"Found {len(candidates)} candidates from web search: "
        + ", ".join(candidates))

    # returns candidates, with score from N to 1
    return [CandidateWebsite(website, len(candidates) - index, [])
        for index, website in enumerate(candidates)]



# SCRAPING FROM WEBSITE
# =====================

class ComponentNotFoundError(Exception):
    """Raised when a component is not found on the website."""
    pass


def RaiseOnNotFound(driver: webdriver.Firefox, notFoundSelector: str) -> None:
    """Raises ComponentNotFoundError if the not-found selector is present in the page."""
    try: 
        driver.find_element(By.CSS_SELECTOR, notFoundSelector)
        raise ComponentNotFoundError()
    except NoSuchElementException:
        pass


def MatchPatternToWebResults(pattern: str, manuCode: str, hints: list[str]) -> str:
    """Searches the web for the first url matching the pattern."""

    # escapes special characters in the pattern
    for char in [".", "[", "]", "(", ")", "+", "?", "^", "$"]:
        pattern = pattern.replace(char, "\\" + char)

    # replaces * with .* and evaluates as regex
    regex = re.compile(pattern.replace("*", ".*").replace("{manuCode}", manuCode))

    # composes the search query (only on the specified website)
    query = manuCode + " site:" + WebsiteFromUrl(pattern)
    if hints: query += " " + " ".join(hints)

    # searches on the web, getting the first url matching the regex
    for searchResult in DDGS().text(query, max_results=5):
        if regex.match(searchResult["href"]):
            return searchResult["href"]

    # if no match, returns error
    raise ComponentNotFoundError()


def ScrapeFromWebsite(
    manuCode: str,  
    entry: WebsiteEntry,
    files: t.Optional[list[str]],
    basePath: str,
    matchedHints: list[str], # included in result on success
    format: t.Literal["html", "md", "txt"],
    closeBrowser: bool,
) -> ScrapedComponentData:
    """Scrapes data of a component from a website."""

    # opens browser, or gets existing one
    driver = GetBrowser()

    # detects if url is a pattern (contains *)
    if "*" in entry["url"]:
        url = MatchPatternToWebResults(entry["url"], manuCode, matchedHints)

    # if the url is not a pattern, it is a template
    else:
        # formats url replacing {manuCode} with the provided manuCode
        url = entry["url"].format(manuCode=manuCode)

    # navigates to the found url
    logger.info(f"Navigating to URL: {url}")
    driver.get(url)
    
    # composes selector to wait for content or not found page
    waitSelector = entry["wait"]
    notFoundSelector = entry["notFound"]
    if notFoundSelector:
        waitSelector += ", " + notFoundSelector
    
    # waits for page to load
    WaitElement(driver, waitSelector)   
    RaiseOnNotFound(driver, notFoundSelector)

    # scrapes fields
    logger.debug("Scraping fields...")
    scrapedFields = ScrapeFields(driver, entry["fields"], format)
    
    # gets files config, filtering by files parameter
    filesConfig = entry["files"]
    if files is not None:
        filesConfig = {key: value for key, value in filesConfig.items() if key in files}

    # scrapes files
    logger.debug("Scraping files...")
    scrapedFiles = ScrapeFiles(driver, basePath, filesConfig,
        data = {**scrapedFields, "manuCode": manuCode, "ext": "{ext}"})

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
    candidates = GetRankedCandidates(hints, config)

    # if fails, try web search
    if len(candidates) == 0:
        logger.info(f"No known website matching hints {hints}, trying web search...")
        candidates = GetCandidatesFromWebSearch(manuCode, hints)

    # if still no candidates, return error
    if len(candidates) == 0:
        return {
            "manuCode": manuCode,
            "result": f"error: no known website found for '{manuCode}'",
        }

    # for each candidate website
    for candidate in candidates:
        try:
            # try to scrape from each one
            websiteEntry = config[candidate.website]
            return ScrapeFromWebsite(manuCode, websiteEntry, files, basePath,
                candidate.matchedHints, format, closeBrowser)

        # skip to next candidate if component not found
        except ComponentNotFoundError as e:
            logger.info(f"Component '{manuCode}' not found on '{candidate.website}'")
            continue
            
        # returns error if something goes wrong
        except Exception as e:
            logger.error(f"Error during scraping '{manuCode}' from '{candidate.website}': {e}")
            continue

    # if all fails, return error
    return {
        "manuCode": manuCode,
        "result": f"error: unable to scrape '{manuCode}' from any known website. "
            "Tried websites: " + ", ".join(candidate.website for candidate in candidates),
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
