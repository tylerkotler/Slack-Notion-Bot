# notion-analytics
## 2 scripts:
**1. notion_bot** -> it is a Flask app that takes in slash commands on Slack and makes changes on Notion, including moving stories and adding Changes data. It also runs the notion_data script when a card is moved to 13

**2. notion_data** -> it runs through all the changes in the Changes table, calculates status times, adds the data to csvs, and writes it to the HA Google Sheets. The csv files are stored in Amazon AWS S3 human-agency-slackbot bucket, along with the 2 jupyter notebook (ipynb) files that contain visualizations of the data.

## Credentials:
All credentials are stored as config variables in the notion-slackbot app on Heroku, where the app is deployed. They are all obtained in the config file.

**1. Notion token_v2**
  - Found by inspecting the HA Notion page and going to the Application tab
  - Used to create a notion client in both the notion_data and notion_bot files
  
**2. Google Sheets**
  - All credentials came directly from the Google Sheets API authorization process
  - Used to get access to HA Google Sheets in notion_data and write data into the sheets
  
**3. Slack**
 - These come from the Slack API through Tech and Marketing for Good's slack apps
 
 **4. AWS S3**
  - There is a S3 Key and Secret thaat are found in the human-agency-slackbot bucket.
 
 
