"""Browser operations."""

import tempfile
import logging

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


# Configure logging
logger = logging.getLogger(__name__)


# browser configuration
SHOW_BROWSER = True
BROWSER_TIMEOUT = 20

# these MIME types will be downloaded
DOWNLOAD_FILES = ",".join([
    "application/pdf",

    # BUG: these types are not downloaded...
    # TODO: complete the workaround using js
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "image/webp",
    "image/svg+xml"
])

# browser driver instance
browser = None
downloadPath = ""


def GetDownloadPath() -> str:
    return downloadPath


def GetBrowser() -> webdriver.Firefox:
    """Gets a browser, opening it if needed."""
    global browser
    if browser is None or not browser.service.process:
        logger.info("Opening new browser...")
        browser = OpenBrowser()
        logger.info("New browser opened")
    else:
        logger.info("Reusing existing browser")
    return browser


def OpenBrowser() -> webdriver.Firefox:
    """Opens a browser configured for downloading files to a temporary directory."""

    # headless mode, if configured
    options = webdriver.FirefoxOptions()
    if not SHOW_BROWSER:
        options.add_argument('--headless')
    
    # temporary directory for downloaded files
    global downloadPath
    downloadPath = tempfile.mkdtemp()
    logger.info(f"Download path: {downloadPath}")

    # configures browser to download files
    options.set_preference('browser.download.folderList', 2)
    options.set_preference('browser.download.manager.showWhenStarting', False)
    options.set_preference('browser.download.dir', downloadPath)
    options.set_preference('browser.helperApps.neverAsk.saveToDisk', DOWNLOAD_FILES)
    options.set_preference('pdfjs.disabled', True)

    # opens browser
    return webdriver.Firefox(options=options)


def WaitElement(driver: webdriver.Firefox, selector: str) -> None:
    """Waits for an element to be present in the browser."""

    logger.info(f"Waiting for element: {selector}")
    wait = WebDriverWait(driver, BROWSER_TIMEOUT)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))


def CloseBrowser() -> None:
    """Closes the browser."""
    global browser
    if browser is not None:
        browser.quit()
        browser = None
        logger.info("Browser closed")
