"""File downloader, using different methods depending on the file type."""

# Methods to download files
# 1. direct: directly from url, using requests. Simple but no header or cookies.
# 2. image: injecting javascript into the page, to get base64 string of the image.
# 3. browser: using selenium to open a new tab with the file url.
#    The browser must be properly configured to download files automatically.

# File scraping process:
# 1. Get file url from element selector, or compose from url template
# 2. Try direct download, unless disabled in config
# 3. If direct fails, use fallback method: image (for images), browser (other files)

import os
import time
import json
import requests
import base64

import typing as t
import logging as log
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from src.browser import GetDownloadPath
from src.type_hints import FileConfigEntry, ScrapedFile


logger = log.getLogger(__name__)
logger.setLevel(log.INFO)


DOWNLOAD_TIMEOUT = 10     # timeout for waiting for file to download
DOWNLOAD_INTERVAL = 0.5   # interval for checking for new files


# Methods to download files
# 1. DownloadDirect: directly from url, using requests. Simple but no header or cookies.
# 2. DownloadImage: using javascript injected in the page. To be tested.
# 3. DownloadFile: using selenium to open a new tab with the file url.
#    Works only if the browser is properly configured to download files automatically.
#
# TODO: use option 1 if it works, otherwise use option 2 for images and option 3 for other files.
# TODO: add option in config to choose the desired method, since method 1 hangs on some websites.


def GetFileUrlAndTagName(driver: webdriver.Firefox,
    config: FileConfigEntry, data: dict[str, t.Optional[str]]) -> tuple[str, str]:
    """Gets the url of the file to scrape, together with the HTML tag name of the element that contains it.
    Uses either the specified css selector or the provided url template, with placeholders replaced by data.
    """

    # uses url if specified, replacing placeholders with data
    url = config.get("url", "")
    if url: return url.format(**data), "" # no element

    # NOTE: we already perform config validation during loading
    selector = config["selector"] # type: ignore

    # finds file element using css selector
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        tagName = element.tag_name
    except NoSuchElementException:
        raise ValueError(f"Cannot locate element with selector: {selector}")

    # gets url in element (link or image)
    fileUrl = element.get_attribute("href") or element.get_attribute("src")
    if fileUrl is None:
        raise ValueError(f"'href' or 'src' not found for element {tagName} with selector: {selector}")
    if fileUrl == "":
        raise ValueError(f"Empty 'href' or 'src' found for element {tagName} with selector: {selector}")

    return fileUrl, tagName


def DownloadDirect(url: str, targetPath: str) -> ScrapedFile:
    """Downloads a file from the specified url to the specified path."""

    try:
        # downloads data from url, returning error if it fails
        response = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
        response.raise_for_status()
    except Exception as e:
        return {
            "result": f"error: {e}",
            "url": url,
        }

    # replaces extension placeholder with the actual extension
    # TODO: read extension from Content-Disposition HTTP header
    ext = Path(url).suffix.lower().strip(".")
    targetPath = targetPath.format(ext=ext)

    # creates target directory tree if it doesn't exist
    os.makedirs(os.path.dirname(targetPath), exist_ok=True)

    # writes data to file
    with open(targetPath, 'wb') as file:
        file.write(response.content)

    return {
        "result": "success",
        "url": url,
        "path": targetPath,
        "size": os.path.getsize(targetPath),
    }


def DownloadImage(driver: webdriver.Firefox, selector: str, targetPath: str) -> ScrapedFile:
    """Downloads an image opened in the current tab to the specified target path.
    The target path must contain the {ext} placeholder, replaced with image extension.
    Returns a tuple with target path and size of the downloaded image.
    """

    # destination image extension
    ext: t.Literal["png", "jpeg"] = "png"
    js = f"const ext = '{ext}';"

    # injects js to get image element
    # NOTE: json.dumps is used to escape the selector and avoid malicious code injection
    js += f"const img = document.querySelector({json.dumps(selector)});"

    # injects js to get base64 string of the image
    js += """
    // creates a canvas to convert the image
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;

    // draws image on canvas
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight);

    // converts canvas to base64
    return canvas.toDataURL(ext);
    """

    # executes composed js, getting the base64 string, with prefix
    imgBase64 = driver.execute_script(js)
    logger.info(f"Got base64 with length: {len(imgBase64)} of image with selector: {selector}")

    # substitutes extension placeholder with the actual extension
    targetPath = targetPath.format(ext=ext)

    # saves image to file, decoding base64
    # (removing the data:image/png;base64, prefix)
    with open(targetPath, "wb") as f:
        imgBytes = base64.b64decode(imgBase64.split(",")[1])
        f.write(imgBytes)
    logger.info(f"Image downloaded to: {targetPath}, size: {len(imgBytes)}")

    # gets the url of the image, if it's not "data:image/..."
    url = driver.find_element(By.CSS_SELECTOR, selector).get_attribute("src") or ""
    if url.startswith("data:image/"): url = ""

    return {
        "result": "success",
        "url": url,
        "path": targetPath,
        "size": len(imgBytes),
    }


def DownloadWithBrowser(driver: webdriver.Firefox, url: str, targetPath: str) -> ScrapedFile:
    """Downloads a file opening a new browser tab with the specified url.
    It works with PDF files and other non-media files with supported browser preview.
    """

    # gets browser download path and existing files
    downloadPath = GetDownloadPath()
    initialFiles = set(os.listdir(downloadPath))

    # checks existing part files, that may block the download
    for file in initialFiles:
        if file.endswith(".part"):
            logger.warning(f"Part file found: {file}")

    # opens a new tab with the file url
    # NOTE: url is sanitized using json.dumps to prevent injection of malicious code
    # the tab will close after the file is downloaded
    driver.execute_script(f"window.open({json.dumps(url)}, '_blank');")
    logger.info(f"Opened new tab with url: {url}, waiting for file to download...")

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
            if os.path.getsize(downloadedFile) != 0:
                break # file found, exit loop

            # no valid file found, until now
            downloadedFile = ""
        
        # exits outer loop if file is found
        if downloadedFile != "": break

        # waits for next iteration
        time.sleep(DOWNLOAD_INTERVAL)

    # timeout reached
    if downloadedFile == "":
        raise TimeoutError(f"File not found in {downloadPath} after {DOWNLOAD_TIMEOUT} seconds")

    logger.info(f"File downloaded to: {downloadedFile}")

    # creates target directory if it doesn't exist
    os.makedirs(os.path.dirname(targetPath), exist_ok=True)

    # replaces extension placeholder with the actual extension
    targetPath = targetPath.format(ext=Path(downloadedFile).suffix.strip("."))

    # removes files if already exists
    if os.path.exists(targetPath):
        os.remove(targetPath)

    # moves file to the target path
    os.rename(downloadedFile, targetPath)
    logger.info(f"File moved to: {targetPath}")

    # adds file to the scraped files
    return {
        "result": "success",
        "url": url,
        "path": targetPath,
        "size": os.path.getsize(targetPath),
    }


def DownloadFile(driver: webdriver.Firefox, url: str, tagName: str, selector: str, targetPath: str) -> ScrapedFile:
    """Downloads a file from the specified url to the specified path.
    Uses different methods depending on the case: image or other file.
    """

    # tries direct download
    # TODO: add option to skip this where it doesn't work
    logger.info(f"Trying direct download from url: {url}")
    result = DownloadDirect(url, targetPath)

    # if successful, returns the result
    if result.get("result") == "success":
        return result

    # if not successful, uses the fallback method
    logger.info(f"Direct download failed: {result.get('result')}")
    
    # images extracxtion using javascript
    if tagName == "img":
        logger.info(f"Trying image extraction from selector: {selector}")
        return DownloadImage(driver, selector, targetPath)

    # downloads using browser
    logger.info(f"Trying browser download from url: {url}")
    return DownloadWithBrowser(driver, url, targetPath)


def ScrapeFiles(
    driver: webdriver.Firefox,
    basePath: str,
    files: dict[str, FileConfigEntry],
    data:  dict[str, t.Optional[str]],
) -> dict[str, ScrapedFile]:
    """Scrapes files from the current page, using the specified config.
    Tries different methods to download the file, depending on the file type.
    """

    scrapedFiles = {}
    for tag, fileConfig in files.items():
        logger.info(f"Scraping file: {tag}")

        # focuses the first tab
        # this is needed because the browser may have opened multiple tabs to download files
        driver.switch_to.window(driver.window_handles[0])

        # tries to get file url and, if selector is specified, the tag name of the element
        try:
            url, tagName = GetFileUrlAndTagName(driver, fileConfig, data)
        except Exception as e:
            logger.error(f"Error getting file url for '{tag}': {e}")
            scrapedFiles[tag] = {"result": f"error: {e}"}
            continue

        # NOTE: we already perform config validation during loading
        targetPath = fileConfig["path"] # type: ignore
        
        # replaces placeholders with data, and composes absolute path
        targetPath = targetPath.format(**data)
        targetPath = os.path.join(basePath, targetPath)

        try:
            # downloads the file with the appropriate method, saving the result
            selector = fileConfig.get("selector", "")
            scrapedFiles[tag] = DownloadFile(driver, url, tagName, selector, targetPath)

        # returns error if something goes wrong
        except Exception as e:
            logger.error(f"Error downloading file '{tag}': {e}")
            scrapedFiles[tag] = {"url": url, "result": f"error: {e}"}
            continue

    return scrapedFiles
