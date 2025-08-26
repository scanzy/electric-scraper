"""Simple scraping test using selenium."""

from selenium import webdriver
from selenium.webdriver.common.by  import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support    import expected_conditions as EC
from selenium.common.exceptions    import NoSuchElementException


# test data (only for testing purposes)
URL = "https://www.molex.com/en-us/products/part-detail/{manuCode}"
TEST_PARTS = ["428160212", "428160612", "428180512", "02061101"]

# wait for page title to load, up to 10 seconds
WAIT_FOR = "h1"
TIMEOUT = 10

# css selectors for page elements
CSS_SELECTORS = {
    "title": "h1",
    "fileUL": "td[data-key='ul']",

    # only for contacts
    "AWG": "td[data-key='wireSizeAwg']",
    "mm2": "td[data-key='wireSizeMm']",

    # documentation files
    "datasheet": ".cmp-resourcelist__resources-item:first-of-type a.cmp-resourcelist__action-download",
    "drawing":   ".cmp-resourcelist__accordion__content a.cmp-resourcelist__action-download",
}


# opens browser
print("Opening browser...")
driver = webdriver.Firefox()
print("Browser opened.")

for part in TEST_PARTS:

    # composes and opens url
    url = URL.format(manuCode=part)
    driver.get(url)

    # waits for page to load, up to 10 seconds
    wait = WebDriverWait(driver, timeout=TIMEOUT)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, WAIT_FOR)))

    # finds the elements
    elements = {}
    for key, value in CSS_SELECTORS.items():
        try:
            elements[key] = driver.find_element(By.CSS_SELECTOR, value)
        except NoSuchElementException:
            elements[key] = None

    # prints the text
    print(f"{part}:")
    for key, element in elements.items():
        if element is None: continue
        print(f"- {key}: {element.text or element.get_attribute('href')}")

# closes browser
driver.quit()
