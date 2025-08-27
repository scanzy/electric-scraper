# Scraping library

This library allows to scrape data and files of electric components from the web.
The library is designed to be easy to use, trying to autodetect scraping settings.
Upon scraping error, the library will try again, searching on other websites.


## Scraping process

When using the scrape tool to get data from a single component, the library follows these steps:
1. **reads** the config file to get known websites and their scraping settings
2. **finds** candidate websites among known ones, matching provided hints or searching on web
3. **starts** with the first candidate, hoping it will work
4. **gets the url** for the website, composing it from a template or matching search results
5. **navigates** to the candidate url, opening a new browser window if needed
6. **waits** for page to load, checking for not found page
7. **scrapes data** using the configured css selectors
8. **downloads files** using the configured settings
8. **closes** browser, if specified

Below a more detailed description of some of the steps.


### Website ranking and selection

The scraper chooses candidate websites in either of two ways:
- a. matching the provided **hints** to known websites or configured keywords
- b. using **web search** results, filtering only known websites

In option a, hints are matched against websites and keywords, to get a score:
- +5 if a hint exactly matches the website domain (e.g., `te.com`)
- +3 for each hint that exactly matches a configured keyword
Candidates are sorted by score, then used in order, until scraping succeeds.

You can specify the same hints multiple times, to increase the score.
Example: `["keyword1", "keyword1", "keyword2"]` gives x2 score to `keyword1` than `keyword2`.

The web search (option b) is performed if no hints matches any website (or no hints provided).
See the next sections for more details and examples about hints and keywords.


### Url composition

The scraper can be configured to compose the url in either of two ways:
- I. substituting the manifacturer code in a **url template**
- II. matching urls from search results to a **url pattern** (with * wildcard)

For websites with **static urls** (always the same url, except the manifacturer code),
the scraper composes the url by substituting the manifacturer code in the url template.

Example:
```text
URL template in config: "https://example.com/part-{manuCode}"
manuCode: "1234567890"
Composed URL: "https://example.com/part-1234567890"
```

For websites with **dynamic urls**, including in the url other dynamic information,
besides manifacturer code, the scraper gets the url by matching the pattern
with the web search results.

Example:

```text
URL pattern in config: "https://example.com/*/part-{manuCode}"
manuCode: "1234567890"
Composed URL: "https://example.com/manifacturer_xyz/part-1234567890"
```


### Error handling

If the scraping fails for a candidate website, the scraper will try again,
with the next candidate websites. If all candidates fail, the tool will return an error.


## Usage

The main function is `ScrapeComponents` (MCP tool `scrape_components`),
which scrapes data about one or more manifacturer codes.
Input and output data structures are described below.

The tool internally uses `ScrapeComponent` and `SearchComponent`
to search and scrape data from a single component.


### Output

The scraping function returns a list of dictionaries, with the following fields:
- `manuCode`: manifacturer code of the component
- `result`: "success" or "error: <error message>"
- `matchedHints`: list of hints that matched (domain first, then keywords)
- `url`: url of the scraped website page
- `fields`: dictionary with the scraped data (e.g. basic info, details)
- `files`: dictionary with the files downloaded (e.g. datasheet, drawings, catalogs)

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
    "matchedHints": ["example.com", "connector"],
    "url": "https://example.com/part-1234567890",
    "fields": {
      "description": "Connector description",
      "ways": "2",
      "color": "black"
    },
    "files": {
      "datasheet": {
        "url": "https://example.com/datasheet_1234567890.pdf",
        "path": "/path/to/datasheet-1234567890-black.pdf",
        "size": 1000000
      },
      "drawing": {
        "url": "https://example.com/drawing_1234567890.pdf",
        "path": "/path/to/drawing-1234567890-black.pdf",
        "size": 2000000
      },
      "image": {
        // this file was not found
        "result": "error: 404 Not Found",
        "url": "https://example.com/image_1234567890.jpg",
      }
    },
  },
  {
    // this component was not found
    "manuCode": "1234567891",
    "result": "error: scraping failed for all candidate websites (2)",
  },
  // other components
]
```


### Input

The function takes the following arguments:
- `manuCodes`: list of manifacturer codes of the components (required)
- `hints`: website domains or keywords to match the website to scrape from
- `files`: list of file tags to scrape (None = all configured files)
- `basePath`: base path to save the files to download
- `format`: "html", "md", "txt" (default = txt)
- `closeBrowser`: whether to close the browser after scraping (default = True)

The only required argument is `manuCodes`.

Example input:
```json
{
  "manuCodes": ["1234567890", "1234567891"],
  "hints": ["te.com", "AMP", "connector"],
  "files": ["datasheet", "drawing", "image"],
  "basePath": "/absolute/path/to/download/folder/",
  "format": "md",
  "closeBrowser": true,
}
```


## Configuration file

The configuration file is a json file, with the following structure:

```json
{
  "<website1>": {

    // keywords to match the website to scrape from, using hints parameter
    // providing one of these keywords in hints, will match the website
    "keywords": ["<keyword1>", "<keyword2>"],

    // url template with {manuCode} placeholder, for url generation
    // or url matching pattern, with {manuCode} placeholder and * wildcard
    "url": "<url_template_or_pattern_with_{manuCode}_and_*>",

    // css selectors to wait for page to load, or check for not found page
    "wait": "<css selector>",
    "notFound": "<css selector>",

    // data fields to scrape
    "fields": {
      "<field1>": "<css selector>",
      "<field2>": "<css selector>",
    // other fields
    },

    // files to download
    "files": {
      "<file1>": {
        "selector": "<css selector to download link>",
        "filename": "<filename_with_{manuCode}_and_{ext}_and_other_fields>"
      },
      "<file2>": {
        "selector": "<css selector to download link>",
        "filename": "<filename_with_{manuCode}_and_{ext}_and_other_fields>"
      },
      // other files
    },
  },

  "<website2>": {
    // scraping settings for other website
  },
  
  // other websites
}
```

The `url` field must contain the {manuCode} placeholder to be substituted with the manifacturer code.
If the url contains * wildcard, it will be used to match the url from search results.
Otherwise, the url will be used as is, simply substituting the manifacturer code.

The `filename` field of the file configuration supports placeholders:
- `{manuCode}`: manifacturer code
- `{ext}`: extension of the file
- scraped data fields, from `fields` output dictionary, e.g. `{description}` for field `description`


## Other tools

The configuration file can be read and edited using `ReadConfig` and `WriteConfig` functions,
or MCP tools `read_config` and `write_config`.

ReadConfig returns the dictionary stored in the configuration file.
When specifying optional parameter `domainOrUrl`, the dictionary is filtered.
Example: `ReadConfig(domainOrUrl="example.com")`

WriteConfig takes a dictionary as input, and writes it to the configuration file.
Example: `WriteConfig(config, domain="example.com")`

This documentation file can be read using `ReadDocs` function (MCP tool `read_docs`),
which returns the text of the file, to be read by AI.
