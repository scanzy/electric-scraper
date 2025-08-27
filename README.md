# Electric scraper

This project provides tools for scraping data and files of electric components from the web.
The project includes a MCP server, to let AI perform the scraping.

**IMPORTANT**: before scraping data and files, ensure to have the authorization to do it.

**WARNING**: the library can download files from the web on your machine.
Include only trusted websites in scraping settings, to avoid downloading malicious files.


## Overview

The project allows to:
- **search for components** on the web, using DuckDuckGo or other search engines
- **autodetect scraping settings** from known websites, reading configuration file
- **scrape entire pages** in html, markdown or text format (as requested)
- **scrape specific data** from the page, using the provided CSS selectors
- **download files** from the page, using CSS selectors to find download links
- **analyze new websites** to find scraping settings (CSS selectors, url templates, etc.)
- **scrape multiple components** in a single call, using the same browser instance


## Requirements

- Python 3.13+
- Firefox browser installed
- The uv package manager


## Installation

- Clone the repository
- To use functions as a library, install dependencies and import functions
- To use the tools via MCP server, include this snippet in your configuration file:

```json
{
  "mcpServers": {
    "electric-scraper": {
      "command": "uv",
      "args": [
        "run",
        "--with", "fastmcp",
        "--with", "selenium",
        "--with", "html2text",
        "--with", "requests",
        "--with", "ddgs",
        "/path/to/server.py"
      ]
    },
    // other servers
  }
}
```


## Tools

Available tools:
- `ScrapeComponents`: scrapes data for components, starting from manifacturer codes
- `ReadConfigDocs`: returns the [DOCS.md](DOCS.md) file, as detailed instructions for AI
- `ReadConfig`: reads the configuration file, to check known websites and settings
- `WriteConfig`: writes the configuration file, to add new websites or update settings

See [DOCS.md](DOCS.md) for details about usage and configuration.


## Project structure

- [`src/`](/src/): source code
  - [`src/scraper.py`](/src/scraper.py): main scraper functions
  - [`src/files.py`](/src/files.py): file scraping functions (downloading)
  - [`src/config.py`](/src/config.py): configuration file operations (read, write, validate)
  - [`src/website.py`](/src/website.py): website utilities (hints, web search)
  - [`src/browser.py`](/src/browser.py): browser utilities (opening, closing, retrying)
  - [`src/type_hints.py`](/src/type_hints.py): type hints for config and scraped data

- [`tests/`](/tests/): tests to check functionality works properly
- [`scouting/`](/scouting/): preliminary code, used to investigate functionality
- [`server.py`](/server.py): MCP server, exposing tools to AI
- [`DOCS.md`](/DOCS.md): detailed instructions, for humans and AI


## Development

Currently, the project is in development.
However, basic field scraping works properly!

TODO (high priority):
- [x] replace manuCode pattern matching with hints/keywords system
- [x] add config validation
- [x] implement retry on other websites if scraping fails
- [x] add selector to recognize not found items
- [x] add websearch for url pattern matching
- [x] add support for subdomain matching, to support .co.jp domains
- [ ] add prompt to let AI analyze new sites and add them to config

TODO (low priority):
- [o] add tests for MCP server
- [ ] use optional fields in config: keywords, notFound, fields, files
- [ ] use jsonschema library for config validation
- [ ] add tests for config functions, using monkeypatching
- [ ] upload to PyPI
- [ ] improve and activate pdf scraping
- [ ] add support for images, not working yet
