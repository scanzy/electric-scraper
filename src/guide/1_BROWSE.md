# STEP 1/6: NAVIGATION TO COMPONENT PAGE

## Objective

Obtain preliminary information about the site to analyze:
- site domain
- manufacturer codes of 2 example components
- URL format (template or pattern)


## Instructions

1. Open Firefox browser with Selenium and navigate to duckduckgo.com
2. The user will need to navigate to the page of the site of interest
3. Use Selenium to get the URL of the page of the site the user navigated to
4. Focusing on the URL, identify the domain and the manufacturer code (manuCode), if present
5. Present the domain and component code to the user
6. Ask the user to navigate to the page of another component, repeating steps 2-5
7. Compare the 2 URLs to obtain either of these 2 strings:
    - URL template: to easily compose the URL of a page of the site of interest,
        by only replacing {manuCode} with the component code
    - URL pattern: to recognize the URL of a page of the site of interest,
        by inserting the wildcard(s) * where there is other info.
        Where possible, the URL pattern may include the {manuCode} placeholder,
        to be replaced with the component code.
8. Present the string to the user, explaining its meaning in a simple way
9. Ask the user to confirm "ok" before proceeding to the next step.
