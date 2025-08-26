"""File url scraper and downloader."""

import os
import time
import typing as t
import logging as log
from pathlib import Path
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By

from src.browser import GetDownloadPath
from src.type_hints import FileConfigEntry, ScrapedFile


DOWNLOAD_TIMEOUT = 10     # timeout for waiting for file to download
DOWNLOAD_INTERVAL = 0.5   # interval for checking for new files
DOWNLOAD_DELAY = 0.5      # delay for moving file to target path


def GetFileUrl(driver: webdriver.Firefox,
    config: FileConfigEntry, data: dict[str, t.Optional[str]]) -> str:
    """Gets the url of a file from the current page, using either the specified css selector
    or the provided url, with placeholders replaced by data.
    """

    # gets info to scrape file
    selector = config.get("selector", None)
    url = config.get("url", None)

    # checks only one parameter is set
    if (selector is None and url is None) or \
        (selector is not None and url is not None):
        raise ValueError(f"Specify either 'selector' or 'url'")

    # uses url if specified, replacing placeholders with data
    if url is not None: return url.format(**data)

    # finds file url using css selector
    assert selector is not None
    element = driver.find_element(By.CSS_SELECTOR, selector)

    # gets url in element (link or image)
    fileUrl = element.get_attribute("href") or element.get_attribute("src")
    if fileUrl is None:
        raise ValueError(f"File url not found for selector: {selector}")
    return fileUrl


def DownloadDirect(url: str, targetPath: str) -> ScrapedFile:
    """Downloads a file from the specified url to the specified path."""

    # downloads the image
    response = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
    if response.status_code != 200:
        return {
            "result": f"error: HTTP {response.status_code}",
            "url": url,
        }

    # writes image to file
    ext = Path(url).suffix.lower().strip(".")
    with open(targetPath.format(ext=ext), 'wb') as file:
        file.write(response.content)

    return {
        "result": "success",
        "url": url,
        "path": targetPath,
        "size": os.path.getsize(targetPath),
    }


def DownloadImage(driver: webdriver.Firefox, selector: str) -> None:
    """Downloads the image opened in the current tab to the specified path."""

    # downloads the image
    js = f"var img = document.querySelector('{selector}');" + """
    if (img) {
        // Creates a canvas to convert the image
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');
        
        // Sets the canvas dimensions
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        
        // Draws the image on the canvas
        ctx.drawImage(img, 0, 0);
        
        // Converts to blob
        canvas.toBlob(function(blob) {
            // Creates an URL for the blob
            var url = URL.createObjectURL(blob);
            
            // Creates a link for download
            var a = document.createElement('a');
            a.href = url;
            a.download = 'image.png';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            // Cleans the URL
            URL.revokeObjectURL(url);
        }, 'image/png');
    }
    """
    driver.execute_script(js)


def DownloadFile(driver: webdriver.Firefox, url: str, targetPath: str) -> ScrapedFile:
    """Downloads a file using the specified url to the specified path."""

    # for images, uses direct download
    # BUG: this doesn't work since firefox doesn't download the image
    if Path(url).suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]:
        raise NotImplementedError("Image download is not implemented yet")
        return DownloadDirect(url, targetPath)

    # gets download path and existing files
    downloadPath = GetDownloadPath()
    initialFiles = set(os.listdir(downloadPath))

    # checks existing part files, that may block the download
    for file in initialFiles:
        if file.endswith(".part"):
            log.warning(f"Part file found: {file}")

    # opens a new tab with the file url
    # the tab will close after the file is downloaded
    driver.execute_script(f"window.open('{url}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    log.info(f"Opened new tab with url: {url}, waiting for file to download...")

    # for images, downloads the image using javascript
    # NOTE: this is needed because firefox doesn't download the image
    # if Path(url).suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]:
    # TODO: add option in config to choose the desired download method
    #    DownloadImage(driver, selector)

    # waits for file to download, detecting new files in the download path
    downloadedFile = ""
    startTime = time.time()
    while time.time() - startTime < DOWNLOAD_TIMEOUT:

        # detects new files
        currentFiles = set(os.listdir(downloadPath))
        newFiles = currentFiles - initialFiles

        # checks completed files
        for newFile in newFiles:
            # waits that any .part files are removed
            if newFile.endswith(".part"): break

            # checks file size
            downloadedFile = os.path.join(downloadPath, newFile)
            if os.path.getsize(downloadedFile) == 0: continue
            break # file found, exit loop
        
        # exits outer loop if file is found
        if downloadedFile != "": break

        # waits for next iteration
        time.sleep(DOWNLOAD_INTERVAL)

    # timeout reached
    if downloadedFile == "":
        raise TimeoutError(f"File not found in {downloadPath} after {DOWNLOAD_TIMEOUT} seconds")

    log.info(f"File downloaded to: {downloadedFile}")

    # creates target directory if it doesn't exist
    os.makedirs(os.path.dirname(targetPath), exist_ok=True)

    # replaces extension placeholder with the actual extension
    targetPath = targetPath.format(ext=Path(downloadedFile).suffix.strip("."))

    # removes files if already exists
    if os.path.exists(targetPath):
        os.remove(targetPath)

    # moves file to the target path
    os.rename(downloadedFile, targetPath)
    log.info(f"File moved to: {targetPath}")

    # adds file to the scraped files
    return {
        "result": "success",
        "url": url,
        "path": targetPath,
        "size": os.path.getsize(targetPath),
    }


def ScrapeFiles(
    driver: webdriver.Firefox,
    basePath: str,
    files: dict[str, FileConfigEntry],
    data:  dict[str, t.Optional[str]],
) -> dict[str, ScrapedFile]:
    """Scrapes files from the current page, using the specified file config."""

    scrapedFiles = {}
    for tag, fileConfig in files.items():
        log.info(f"Scraping file: {tag}")

        # focuses the first tab
        # this is needed because the browser may have opened multiple tabs
        driver.switch_to.window(driver.window_handles[0])

        # tries to get file url
        try:
            url = GetFileUrl(driver, fileConfig, data)
        except Exception as e:
            log.error(f"Error getting file url for '{tag}': {e}")
            scrapedFiles[tag] = {"result": f"error: {e}"}
            continue

        try:
            # composes relative target path
            targetPath = fileConfig.get("path", None)
            if targetPath is None:
                raise ValueError("'path' is not set for file {tag}")
            
            # replaces placeholders with data, and composes absolute path
            targetPath = targetPath.format(**data)
            targetPath = os.path.join(basePath, targetPath)

            # tries to download file
            scrapedFiles[tag] = DownloadFile(driver, url, targetPath)

        # returns error if something goes wrong
        except Exception as e:
            log.error(f"Error downloading file '{tag}': {e}")
            scrapedFiles[tag] = {"url": url, "result": f"error: {e}"}
            continue

    return scrapedFiles
