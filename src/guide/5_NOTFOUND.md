# STEP 5/6: MANAGING "PAGE NOT FOUND" ERROR

## Objective

Recognize the "page not found" error page of the site,
finding the CSS selector that identifies it, testing it with Selenium.


## Instructions

1. Explain to the user that you will now identify together how to recognize
    when a component doesn't exist on the site, analyzing the "page not found" error page.
2. Guess the code of a component that definitely doesn't exist.
    Try to follow the same coding convention of the example components.
    Examples: "111111111", "1234-5678", "NON_EXISTENT_COMPONENT_123"
3. Use the URL template identified in step 1 to navigate to the page of this non-existent component.
4. Analyze the resulting page, searching for texts or selectors like "404", "not found", "sorry",
    that should be present only on the error page, if possible.
5. Otherwise, ask the user to identify a distinctive element of this error page.
    Example: text "Product not found", "404", "Not available"
    NOTE: some sites don't have an error page, but show an empty page.
    Inform the user of this possibility, reassuring them that it's not a problem.
6. Ask the user to write in the chat:
    - the exact text of the distinctive element found, if present
    - to report that no distinctive element is present
7. If no distinctive element is present, explain to the user that the scraper:
    - won't be able to immediately recognize the "page not found" error
    - will wait for a fixed timeout (e.g. 10 seconds), without finding known elements
    - will then recognize the error, proceeding with the next step, without problems
8. If instead the user has identified the distinctive element, find it using Selenium tools.
9. Once the element is found, get its CSS selector.
10. Test the CSS selector using Selenium to verify that it's present in the error page.
11. Navigate again to an existing component's page and verify that this selector is NOT present.
12. Ask the user to confirm that this selector correctly identifies "not found" pages.
13. Ask the user to confirm "ok" before proceeding to the next step.
