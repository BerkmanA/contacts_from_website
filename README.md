# contacts_from_website
Retrieve contact information from website

This script collects crawls through a given website and collects contact details displayed on the site.
The script finds phone numbers, email addresses and Telegram accounts.
After collecting the information, Maltego entities are created based on the findings including the Telegram profile pic and details.

Note, at this time, the script cannot overcome various tools that some website contain to prevent scraping.
In addition, I entertained the idea of limiting the scrape to URLs containing the original domain in order to avoid false positives, but as of now, the script does not contain this limitation because some websites will redirect the user to another domain when clicking on certain links, lie a payment link, and I prefered to receive the false positives rather than not receiving potentially valuable information.

The script is limited to 50 links, this number is adjustable within the script.
