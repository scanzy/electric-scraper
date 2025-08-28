
# Development notes

Currently, the project is in development.
However, basic field scraping works properly!


TODO (high priority):
- [x] replace manuCode pattern matching with hints/keywords system
- [x] add config validation
- [x] implement retry on other websites if scraping fails
- [x] add selector to recognize not found items
- [x] add websearch for url pattern matching
- [x] add support for subdomain matching, to support .co.jp domains
- [x] add prompt to let AI analyze new sites and add them to config
- [ ] add support for images downloading, not working yet
- [ ] use jsonschema library for config validation
- [ ] use optional fields in config: keywords, notFound, fields, files, comment

TODO (low priority):
- [o] add tests for MCP server
- [ ] add tests for config functions, using monkeypatching
- [ ] find a solution to access page HTML with MCP server (see below)
- [ ] upload to PyPI
- [ ] improve and activate pdf scraping


## Problems and solutionsfor new websites scouting

The instructions for new websites scouting assume to have an existing MCP server to work with HTML.

angiejones/mcp-selenium seems good, but it does not provide tools to work with HTML:
- find_element returns only "Element found", no other information
- good: find_element can be used with :contains() selector

Possible solutions:
0. Contribute to angiejones/mcp-selenium, to add new tools, or enhance the existing ones:
  - con: need to use npm and test it locally

1. Rahulec08/mcp-selenium is a fork of the above, with extensive selenium tools, but:
  - con: it seems written by AI without any test, it may not work
  - con: it should be installed locally with npm

2. Use playwright, with other MCP servers:
  - con: tested microsoft/mcp-playwright, but it cannot install the browser

3. Use puppeteer, with other MCP servers:
  - con: it does not show tools to work with HTML

4. Use ketan27j/selenium_mcp_server, running it locally:
  - con: need to install it locally with virtualenv
  - pro: see config in .roo/mcp.json
  - pro: smart xpath generation function for selector

5. Implement custom tools to work with HTML, using the same MCP server of the scraper:
  - add get_page_html for the whole page
  - add find element and get its html
  - add smart xpath generation copying ketan27j
  - add sort of grep html and return the first match + some chars before and after


## Free reflection

After all, interface automation (web or native UI) is all about:
1. navigating a tree of elements, without reading all unnecessary text or code
2. understanding the structure and content of the elements, and how to use them
3. using tools to interact with the elements, checking the result and retrying if needed
