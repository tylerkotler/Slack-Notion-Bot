# notion-analytics
## 2 scripts:
**1. notion_bot** -> it is a Flask app that takes in slash commands on Slack and makes changes on Notion, including moving stories and adding Changes data. It also runs the notion_data script when a card is moved to 13
**2. notion_data** -> it runs through all the changes in the Changes table, calculates status times, adds the data to csvs, and writes it to the HA Google Sheets

## Credentials:
**1. Notion token_v2**
  - Found by inspecting the HA Notion page and going to the Application tab
  - May need to substitute it in for the current token in config.py
  - Used to create a notion client in both the notion_data and notion_bot files
**2. Google Sheets**
  - All credentials are in Notion Changes Data.json that came directly from the Google Sheets API authorization process. This may require repeating for yourself.
  - Used to get access to HA Google Sheets in notion_data and write data into the sheets
**3. Slack**
 - Credentials are in the config file
 - These come from the Slack API through Tech and Marketing for Good's slack apps
