# STEP 2/6: IDENTIFYING INFORMATION OF INTEREST

## Objective

Identify the fields to extract from component page, with their corresponding CSS selectors.
Test the CSS selectors with Selenium on the 2 example components.


## Instructions

1. Explain to the user that you will now identify together the information of interest to be extracted from the component page.
2. Ask the user to write in the chat the exact text of information visible on the page.
    Example: "Connector XYZ", "Voltage: 5 V", "Price: €12.50"
3. Search for the element that contains that exact text using Selenium tools
4. Once the element is found, get its CSS selector
5. Use Selenium to find the element via the identified CSS selector, getting the information of interest
6. Ask the user to confirm that the extracted text matches what is expected
7. If the information is not found, or is wrong, try to use a different CSS selector
8. Ask the user for the name to assign to this field in the configuration,
    recommending short but clear names, and suggesting 1-3 ideas, if you can.
    Examples: "connector_type", "voltage", "price"
9. Repeat steps 2-7 for each information of interest that the user wants to extract
10. Once the information collection is finished, navigate to the second component's page.
11. Ask the user for confirmation when the page has been completely loaded
12. Test on this second page the CSS selectors identified at previous steps,also on this page,
    using Selenium to find elements and extracting information of every field.
13. Ask the user to confirm "ok" before proceeding to the next step.
