"""Simple image scraping test using selenium."""

# NOTE: this solution works only for images that are loaded from the same domain
# otherwise, browser CORS policy will block the request, and canvas.toDataURL will fail

import json
import base64

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


# test page settings
TEST_PART = "428160212"
URL = "https://www.molex.com/en-us/products/part-detail/{manuCode}"
TIMEOUT = 10

# image settings
IMG_SELECTOR = ".pdp-mediagallery__image img"
TARGET_PATH = __file__.replace(".py", ".png")


# opens page
driver = webdriver.Firefox()
driver.get(URL.format(manuCode=TEST_PART))

# waits for image to load
wait = WebDriverWait(driver, timeout=TIMEOUT)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, IMG_SELECTOR)))


# injects js to get image
js = """
function imgToBase64(img) {

  // creates a canvas to convert the image
  const canvas = document.createElement('canvas');
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;

  // draws image on canvas
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0, img.naturalWidth, img.naturalHeight);

  // converts canvas to base64
  return canvas.toDataURL('image/png'); // or 'image/jpeg'
}

// gets image and converts it to base64
const img = document.querySelector(IMG_SELECTOR);
const base64 = imgToBase64(img);
return base64;
"""

# replaces IMG_SELECTOR with the actual selector
# NOTE: json.dumps is used to escape the selector and avoid malicious code injection
completeJs = js.replace("IMG_SELECTOR", json.dumps(IMG_SELECTOR))

# executes js, getting the base64 string, with prefix
imgBase64 = driver.execute_script(completeJs)
print(f"Base64 length: {len(imgBase64)}")
print(f"Base64 string (first 100 chars): {imgBase64[:100]}")

# saves image to file, decoding base64
# (removing the data:image/png;base64, prefix)
with open(TARGET_PATH, "wb") as f:
    imgBytes = base64.b64decode(imgBase64.split(",")[1])
    f.write(imgBytes)

# opens image in browser
driver.get(f"file://{TARGET_PATH}")
