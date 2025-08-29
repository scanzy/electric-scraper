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


### File download

The scraper uses 3 different methods to download files:
1. **direct download** from the url, with a simple HTTP request, without using the browser
2. **image extraction** from the page, using javascript to get the image as base64 string
3. **browser download** using a new browser tab to download the file

The scraper tries the direct download first, then uses the other methods if it fails.


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
- `method`: `direct`/`image`/`browser`, method used to download the file


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
      "image": {
        "url": "https://example.com/image_1234567890.jpg",
        "path": "/path/to/image-1234567890-black.pdf",
        "method": "image",
        "size": 2000000,
      },
      "datasheet": {
        "url": "https://example.com/datasheet_1234567890.pdf",
        "path": "/path/to/datasheet-1234567890-black.pdf",
        "size": 1000000,
        "method": "direct",
      },
      "drawing": {
        // this file was not found
        "result": "error: could not locate selector: [a[data-title='Drawing']]",
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

    // [OPTIONAL] comment for the website configuration
    // will be ignored by the scraper, but can be used as reference or notes
    "comment": "<comment>",

    // [OPTIONAL] keywords to match the website to scrape from, using hints parameter
    // providing one of these keywords in hints, will match the website
    "keywords": ["<keyword1>", "<keyword2>"],

    // [REQUIRED] url template with {manuCode} placeholder, for url generation
    // or url matching pattern, with {manuCode} placeholder and * wildcard
    "url": "<url_template_or_pattern_with_{manuCode}_and_*>",

    // [REQUIRED] css selector to wait for page to load
    "wait": "<css selector>",

    // [OPTIONAL] css selector to check for not found page
    "notFound": "<css selector>",

    // [OPTIONAL] data fields to scrape, with css selectors to find elements
    "fields": {
      "<field1>": "<css selector>",
      "<field2>": "<css selector>",
      // other fields
    },

    // [OPTIONAL] files to download
    // 2 format options, one with selector, one with url (alternative)
    "files": {
      "<file1>": {

        // [REQUIRED] css selector to find the download link
        // this is ALTERNATIVE to "url" field
        "selector": "<css selector>",

        // [REQUIRED] url template with {manuCode} and other fields placeholders
        // this is ALTERNATIVE to "selector" field
        "url": "<url_template_with_{manuCode}_and_other_fields>",

        // [REQUIRED] path filename template with {manuCode} and {ext} placeholders,
        // to be substituted with the scraped data, and actual file extension
        // and appended to basePath to get the actual path to save the file
        "path": "<filename_path_with_{manuCode}_and_{ext}_and_other_fields>",

        // [OPTIONAL] comment for debugging or notes for this file
        "comment": "<comment>",
      },
      // other files
    },

    // [OPTIONAL] whether to skip direct download (default = false)
    // useful to speed up scraping for sites with cookies or other restrictions
    "skipDirectDownload": true,
  },

  "<website2>": {
    // scraping settings for other website
  },
  
  // other websites
}
```

For every website entry, the only required fields are `url` and `wait`.
In files configuration, `path` is required, and either one of `selector` or `url` is required.

If the `url` contains * wildcard, it will be used to match the url from search results.
Otherwise, the url must contain the {manuCode} placeholder,
to be substituted with the manifacturer code to compose the url to scrape from.

The `path` field of the file configuration supports placeholders:
- `{manuCode}`: manifacturer code
- `{ext}`: extension of the file
- scraped data fields, from `fields` output dictionary, e.g. `{description}` for field `description`

For websites with cookies or other restrictions, the direct download of files will not work.
In such cases, set `skipDirectDownload` to true, to skip the direct download.
This will use the other methods to download the files, speeding up the scraping process.


## Other tools

The configuration file can be read and edited using `ReadConfig` and `WriteConfig` functions,
or MCP tools `read_config` and `write_config`.

ReadConfig returns the dictionary stored in the configuration file.
When specifying optional parameter `domainOrUrl`, the dictionary is filtered.
Example: `ReadConfig(domainOrUrl="example.com")`

WriteConfig takes a dictionary as input, and writes it to the configuration file.
Example: `WriteConfig(config, domain="example.com")`
To delete an entry, set the entry parameter to None.

This documentation file can be read using `ReadDocs` function (MCP tool `read_docs`),
which returns the text of the file, to be read by AI.

The AI can use the `read_new_website_guide` tool to get step-by-step instructions
to add a new website to the configuration file, cooperating with the user.
This requires additional MCP tools to inspect websites and read the HTML.
