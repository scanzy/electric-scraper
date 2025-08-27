from ddgs import DDGS


knownSites = ["te.com", "molex.com", "aptiv.com"]
MANUCODES = ["DTP06-2S"]


# type alias for the search results
SearchResults = list[dict[str, str]]

def WebSearch(manuCode: str, type: str = "", website: str = "") -> SearchResults:
    """Search for results on the web, using DuckDuckGo or other search engines."""

    # composes the search query
    search_query = manuCode
    if type: search_query += f" {type}"
    if website: search_query += f" site:{website}"

    # search for the manuCode
    return DDGS().text(search_query, max_results=5)


def FilterResults(results: SearchResults, sites: list[str]) -> SearchResults:
    """Filter the results to only include the sites."""
    return [result for result in results if any(site in result["href"] for site in sites)]


def PrintResults(results: SearchResults):
    """Print the provided web search results."""
    for index, result in enumerate(results):
        print(f"{index+1}. URL: {result['href']}")
        print(f"   Title: {result['title']}")
    print(" ")


if __name__ == "__main__":
    for manuCode in MANUCODES:

        # search for the manuCode, filtering for the known sites
        print(f"Searching for {manuCode}...")
        results = WebSearch(manuCode, website="te.com")
        filteredResults = FilterResults(results, knownSites)

        # print the results (all)
        print(f"Found {len(results)} results:")
        PrintResults(results)

        # print the results (filtered)
        print(f"Filtered {len(filteredResults)} results:")
        PrintResults(filteredResults)
