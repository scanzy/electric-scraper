import re
import typing as t
import logging as log

from ddgs import DDGS

from src.type_hints import WebsiteEntry
if t.TYPE_CHECKING:
    from src.config import Config


# configures logging
logger = log.getLogger(__name__)
logger.setLevel(log.INFO)


# search engines used for web search
#SEARCH_BACKEND = "duckduckgo, bing, brave, google"

# BUG: duckduckgo search backend "is not available", ddgs switches to auto
# we remove duckduckgo from the list, to make ddgs use only desired backends
# TODO: check again when ddgs is updated
SEARCH_BACKEND = "bing, brave, google"


# URL AND DOMAIN UTILITIES
# ========================


def DomainFromUrl(url: str) -> str:
    """Extracts the lowercase domain from a url, removing www. and protocol.
    Example: https://WWW.MOLEX.COM/molex/products/family/10362 -> molex.com
    """

    # removes protocol
    if "://" in url:
        url = url.split("/")[2]

    # removes pages after the domain
    elif "/" in url:
        url = url.split("/")[0]

    # removes www.
    return url.replace("www.", "").lower()


def MatchUrlToDomains(url: str, domains: list[str]) -> str:
    """Matches the url against the domains, returning the first matching domain.
    Matches also subdomains, e.g. "IT.FARNELL.com" matches "farnell.COM".
    Raises ValueError if no domain matches. Matching is case-insensitive.
    """

    # extracts the domain from the url
    targetDomain = DomainFromUrl(url).lower()

    # checks if the domain matches any of the configured domains
    for domain in domains:
        if targetDomain.endswith(domain.lower()):
            return domain

    raise ValueError(f"No domain matches {targetDomain} in {domains}")



# HINTS (DOMAIN AND KEYWORDS) MATCHING
# ====================================


class CandidateWebsite(t.NamedTuple):
    """Candidate website for scraping, with score and matched hints."""
    domain: str
    score: int
    matchedHints: list[str]



def MatchWebsiteToHints(lowerHints: list[str], domain: str, entry: WebsiteEntry) -> CandidateWebsite:
    """Matches the hints against the website, calculating the score."""

    score = 0
    matchedHints = []
    for hint in lowerHints:

        # +5 if hint matches the website domain
        try:
            MatchUrlToDomains(domain, [hint])
            score += 5
            if hint not in matchedHints:
                matchedHints.append(hint)

        # +0 if hint does not match the website domain
        except ValueError:
            pass

        # +3 for each hint that exactly matches a configured keyword
        if hint in entry["keywords"]:
            score += 3
            if hint not in matchedHints:
                matchedHints.append(hint)

    logger.debug(f"Matched website '{domain}' to hints {matchedHints} with score {score}")
    return CandidateWebsite(domain, score, matchedHints)


def GetCandidatesFromHints(hints: list[str], config: "Config") -> list[CandidateWebsite]:
    """Matches the provided hints against the configured websites, sorting them by score."""

    # preprocess hints: lowercase
    # NOTE: we do not remove duplicate hints, to count them multiple times in score
    # the user can specify some hints multiple times to give them more score
    lowerHints = [hint.lower() for hint in hints]

    # matches hints against websites
    candidates = [MatchWebsiteToHints(lowerHints, domain, entry)
        for domain, entry in config.items()]

    # removes websites with no matched hints (0 score)
    candidates = [candidate for candidate in candidates if candidate.score > 0]

    # sorts websites by score
    return sorted(candidates, key=lambda x: x.score, reverse=True)



# WEB SEARCH (URL PATTERN) MATCHING
# =================================


def GetCandidatesFromWebSearch(manuCode: str, hints: list[str]) -> list[CandidateWebsite]:
    """Gets candidate websites for a component, searching online."""

    # composes the search query: exact match for manuCode, then hints
    query = f'"{manuCode}"'
    if hints: query += " " + " ".join(hints)

    # searches the web
    logger.info("Searching the web for %s...", query)
    results = DDGS().text(query, max_results=10, backend=SEARCH_BACKEND)
    for index, result in enumerate(results):
        logger.debug("Search result %d: %s", index, result["href"])

    # composes candidates
    candidates = []
    for result in results:

        # extracts domain from url 
        domain = DomainFromUrl(result["href"])

        # adds candidate, if not already in list
        if domain not in candidates:
            candidates.append(domain)

    # logs candidates
    logger.info(f"Found {len(candidates)} candidates from web search: "
        + ", ".join(candidates))

    # returns candidates, with score from N to 1
    return [CandidateWebsite(domain, len(candidates) - index, [])
        for index, domain in enumerate(candidates)]



def MatchUrlPatternToWebResults(urlPattern: str, manuCode: str, hints: list[str]) -> str:
    """Searches the web for the first url matching the pattern."""

    # composes the search query: exact match for manuCode, then hints
    query = f'"{manuCode}"'
    if hints: query += " " + " ".join(hints)

    # only on the specified website
    query += " " + "site:" + DomainFromUrl(urlPattern)

    # escapes special characters in the pattern
    regexPattern = urlPattern.replace("{manuCode}", manuCode)
    for char in [".", "[", "]", "(", ")", "+", "?", "^", "$"]:
        regexPattern = regexPattern.replace(char, "\\" + char)

    # replaces * with .* and evaluates as regex
    regex = re.compile(regexPattern.replace("*", ".*"))

    # searches on the web
    logger.debug("Searching the web for %s...", query)
    results = DDGS().text(query, max_results=10, backend=SEARCH_BACKEND)
    for index, result in enumerate(results):
        logger.debug("Search result %d: %s", index, result["href"])

    # gets the first url matching the regex
    for searchResult in results:
        if regex.match(searchResult["href"]):
            return searchResult["href"]

    return ""
