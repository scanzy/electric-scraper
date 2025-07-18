# Electric scraper

This project collects tools for scraping data of electric compoents from the web.
The project includes a MCP server, to let AI perform the scraping.

WARNING: before using this, ensure to have the authorization to scrape the data.


## Overview

The project allows to:
- **scrape entire pages** in html, markdown or text format (as configured)
- **scrape specific data** from the page, using css selectors
- **download files** from the page, using css selectors to find download link/button

Css selectors can be specified in input, when using the tool,
or saved in the configuration file, to be autodetected based on parameters.

Available tools (see below for details):
- `ScrapeComponent`: scrape data starting from a manifacturer code
- `ReadConfig`: read the configuration file
- `WriteConfig`: write the configuration file


## Installation

- Clone the repository
- To use functions as a library, install dependencies and import function
- To use the tools with MCP server, include this snippet in your configuration file:

```json
{
  "mcpServers": {
    "electric-scraper": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "--with",
        "selenium",
        "/path/to/server.py"
      ]
    },
    // other servers
  }
}
```

## Scraping tool

The main function is `ScrapeComponent` (MCP tool `scrape_component`), which scrapes data starting from a manifacturer code.
Input and output data structures are described below.


### Output

The function returns a dictionary, with the following fields:
- `url`: url of the scraped website page
- `type`: type of the component (connector, cable, etc.)
- `data`: dictionary with the scraped data (basic info, details)
- `files`: dictionary with the files downloaded (datasheet, drawings, catalogs)

Structure of `files` dictionary, in output:
- `url`: url of the downloaded file
- `path`: path of the file, saved to disk
- `size`: size of the file in bytes


Example output:
```json
{
  "url": "https://example.com",
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
      "url": "https://example.com/image.jpg",
      "path": "/path/to/image-1234567890-black.jpg",
      "size": 500000
    }
  }
}
```

### Input

The function takes the following parameters:
- `manuCode`: the manifacturer code of the component (required)
- `type`: type of the component (connector, cable, etc.)
- `website`: the website to scrape the data from
- `data`: dictionary with information to be scraped
- `files`: dictionary with the files to download
- `format`: "html", "md", "txt" (default = md)

Structure of `data` dictionary, in input:
- key: field identifier, used as key of output `data` dictionary
- value: css selector to find the element

Structure of `files` dictionary, in input:
- key: file identifier, used as key of output `files` dictionary
- value: dictionary with the following fields:
    - `selector`: css selector to find the download link/button
    - `path`: path of the file, saved to disk

The `path` field supports placeholders, like `{manuCode}`, `{type}`, and data fields.

Example input:
```json
{
  "manuCode": "1234567890",
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
      "path": "/path/to/datasheet-{manuCode}-{color}.pdf"
    }
  }
}
```

`manuCode` is the only required input parameter, the other ones are optional (default = None)
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
