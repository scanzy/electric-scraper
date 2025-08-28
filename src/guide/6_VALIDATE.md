# STEP 6/6: SAVING SETTINGS AND FINAL VERIFICATION

## Objective

Verify that the configuration is correct, testing the scraper.


## Instructions

1. Summarize to the user all the settings configured during the process:
   - Site domain and URL template/pattern
   - Identified fields with their corresponding CSS selectors
   - Files to download, and related settings
   - Selector for the wait condition
   - Selector to recognize "not found" pages
2. Ask the user for confirmation before proceeding, asking if anything is missing.
3. Use the tool to read the scraper documentation, paying attention to the configuration format.
4. Build the complete configuration for the website in the format required by the system.
5. Use the tool to write the settings of the new site in the configuration file.
6. Explain to the user that you will now perform a final verification using the scraper's MCP server.
7. Test the configuration on the two example components used during setup, verifying that:
   - all fields are extracted correctly (ask the user to confirm)
   - files are downloaded correctly (ask the user to confirm)
8. Test the configuration with a non-existent component,
   verifying that it's recognized as "not found" (ask the user to confirm).
9. Report to the user the results of all tests.
10. Suggest to the user to provide the code of a third existing component,
   to perform an additional final test of the configuration.
11. If the scraper encounter errors:
   - identify what doesn't work, to understand the problem
   - identify the corresponding step of the instructions
   - read again the instructions for that step, and follow them again
12. If all tests are positive, congratulate the user on the result.
