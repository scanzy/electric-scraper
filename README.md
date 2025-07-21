# Electric scraper

This project collects tools for scraping data of electric compoents from the web.
The project includes a MCP server, to let AI perform the scraping.

**WARNING**: before using this, ensure to have the authorization to scrape the data.


## Overview

The project allows to:
- **scrape entire pages** in html, markdown or text format (as configured)
- **scrape specific data** from the page, using CSS selectors
- **download files** from the page, using CSS selectors to find download links
- **scrape multiple components** in a single call

Scraping settings (websites, CSS selectors) are stored in a configuration file,
and can be autodetected based on parameters, or overridden in input, when using the tool.

Available tools (see below for details):
- `ScrapeComponents`: scrape data starting from manifacturer codes
- `ReadConfig`: read the configuration file
- `WriteConfig`: write the configuration file


## Requirements

- Python 3.13+
- Firefox browser installed
- The uv package manager


## Installation

- Clone the repository
- To use functions as a library, install dependencies and import functions
- To use the tools with MCP server, include this snippet in your configuration file:

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
        "/path/to/server.py"
      ]
    },
    // other servers
  }
}
```

## Scraping tool

The main function is `ScrapeComponents` (MCP tool `scrape_components`),
which scrape data starting from one or more manifacturer codes.
Input and output data structures are described below.

The tool internally uses `ScrapeComponent` to scrape data from a single component.
The documentation refers to the multiple components case,
but the single component case works exactly in the same way.


### Output

The function returns a list of dictionaries, with the following fields:
- `manuCode`: manifacturer code of the component
- `result`: "success" or "error: <error message>"
- `url`: url of the scraped website page
- `type`: type of the component (connector, cable, etc.)
- `data`: dictionary with the scraped data (basic info, details)
- `files`: dictionary with the files downloaded (datasheet, drawings, catalogs)

Structure of `files` dictionary, in output:
- `result`: "success" or "error: <error message>"
- `url`: url of the downloaded file
- `path`: path of the file, saved to disk
- `size`: size of the file in bytes


Example output:
```json
[
  {
    "manuCode": "1234567890",
    "result": "success",
    "url": "https://example.com/part-1234567890",
    "type": "connector",
    "data": {
      "description": "Connector description",
      "ways": "2",
      "color": "black"
    },
    "files": {
      "datasheet": {
        "url": "https://example.com/datasheet.pdf",
        "path": "/path/to/datasheet-1234567890-black.pdf",
        "size": 1000000
      },
      "drawing": {
        "url": "https://example.com/drawing.pdf",
        "path": "/path/to/drawing-1234567890-black.pdf",
        "size": 2000000
      },
      "image": {
        // this file was not found
        "result": "error: 404 Not Found",
        "url": "https://example.com/image.jpg",
      }
    },
  },
  {
    // this component was not found
    "manuCode": "1234567891",
    "result": "error: 404 Not Found",
  },
  // other components
]
```


### Input

The function takes the following parameters:
- `manuCodes`: list of manifacturer codes of the components (required)
- `type`: type of the component (connector, cable, etc.)
- `website`: the website to scrape the data from
- `fields`: dictionary with information to be scraped
- `files`: dictionary with the files to download
- `format`: "html", "md", "txt" (default = md)
- `closeBrowser`: whether to close the browser after scraping (default = True)

Structure of `data` dictionary, in input:
- key: field identifier, used as key of output `data` dictionary
- value: css selector to find the element

Structure of `files` dictionary, in input:
- key: file identifier, used as key of output `files` dictionary
- value: dictionary with the following fields:
    - `selector`: css selector to find the download link/button
    - `path`: path of the file, saved to disk

The `path` field supports placeholders:
- `{manuCode}`: manifacturer code
- `{type}`: type of the component
- `{ext}`: extension of the file
- scraped data fields, from `fields` dictionary

Example input:
```json
{
  "manuCodes": ["1234567890", "1234567891"],
  "type": "connector",
  "website": "example.com",
  "data": {
    "description": "#main > p.description",
    "ways": "#main > p.ways",
    "color": "#main > p.color",
  },
  "files": {
    "datasheet": {
      "selector": "#main > a.datasheet",
      "path": "/path/to/datasheet-{manuCode}-{color}.{ext}"
    }
  }
}
```

`manuCodes` is the only required input parameter, the other ones are optional (default = None)
`None` or missing parameters will be copied from the configuration file,
based on website, component type, and manifacturer code pattern (recognized as regex).

Use explicit empty dictionaries for `data` and `files` to disable autodetection.
Examples: 
- `data={}` disables autodetection of data settings
- `data={"description": None}` scrapes description field, reading settings from configuration file
- `files={}` disables autodetection of files settings
- `files={"datasheet": None}` scrapes datasheet file, reading settings from configuration file


## Configuration file

The configuration file is a json file, with the following structure:

```json
{
  "<website1>": {
    "<type1>": {

      // regex patterns to match manuCode
      "patterns": [
        "[0-9]{7}-[0-9]{2}",
        "[0-9]{5}-[0-9]{3}",
      ],

      // url template with {manuCode} placeholder
      "url": "<url_template_with_{manuCode}>",

      // css selector to wait for page to load
      "wait": "<css selector>",

      // data to scrape
      "data": {
        "<field1>": "<css selector>",
        "<field2>": "<css selector>",
        // other fields
      },

      // files to download
      "files": {
        "<file1>": {
          "selector": "<css selector>",
          "path": "<path>"
        },
        "<file2>": {
          "selector": "<css selector>",
          "path": "<path>"
        },
        // other files
      },

      // flag to use this configuration if no patterns match
      "fallback": true
    },
    // other types
  },

  "<website2>": {
    "<type1>": { /* ... */ },
    "<type2>": { /* ... */ },
    // other types
  },
  
  // other websites
}
```

The configuration file can be read and edited using `ReadConfig` and `WriteConfig` functions,
or MCP tools `read_config` and `write_config`.

ReadConfig returns the dictionary stored in the configuration file.
When specifying optional parameters `website` and `type`, the dictionary is filtered.
Example: `ReadConfig(website="example.com", type="connector")`

WriteConfig takes a dictionary as input, and writes it to the configuration file.
Example: `WriteConfig(config, website="example.com", type="connector")`


## Scraping process

When calling `ScrapeComponent`, the following steps are performed:
- the configuration file is read
- missing input parameters are filled from data in the configuration file
- website and type are detected based on the manifacturer code pattern
- Firefox browser is opened (if not already open), connected to automation library
- the url is opened, and the page is waited to load, using the "wait" CSS selector
- data fields are scraped, using the data CSS selectors, in the specified format
- urls of files are found, using url templates with data fields, or CSS selectors
- files are downloaded, using the "path" field of the file configuration
- the browser is closed (if configured)


# Development
Currently, the project is in development.

TODO:
- [ ] add support for images, not working yet
