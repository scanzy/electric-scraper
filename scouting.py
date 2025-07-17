"""Simple scraping test using selenium."""

from selenium import webdriver
from selenium.webdriver.common.by  import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support    import expected_conditions as EC


# test data (only for testing purposes)
URL = "https://www.molex.com/en-us/products/part-detail/{manuCode}"
TEST_PARTS = [428160212, 428160612, 428180512]

CSS_SELECTOR = "h1"
TIMEOUT = 10


# opens browser
driver = webdriver.Firefox()

for part in TEST_PARTS:

    # composes and opens url
    url = URL.format(manuCode=part)
    driver.get(url)

    # waits for page to load, up to 10 seconds
    wait = WebDriverWait(driver, timeout=TIMEOUT)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, CSS_SELECTOR)))

    # finds the element
    element = driver.find_element(By.CSS_SELECTOR, CSS_SELECTOR)

    # prints the text
    print(f"{part}: {element.text}")

# closes browser
driver.quit()
