# notion-analytics
## Structure:
**1. slack_bot** -> it is a Flask app that takes in slash commands on Slack and handles reqests through the front end webpage of the bot, which can be found at https://notion-slackbot.herokuapp.com/ . Here, the s3 files are listed and can be downloaded (instead of having to go through the aws website).

**2. move_story** -> its move_story method is called by the move_handler method in slack_bot, which moves a story to a new column on Notion, adds changes data on Notion, and sends back a response. If the story moves to column 13, it triggers the notion_data script.

**3. notion_data** -> it runs through all the changes in the Changes table, calculates status times, adds the data to csvs, and writes it to the HA Google Sheets. The csv files are stored in Amazon AWS S3 human-agency-slackbot bucket, along with the 2 jupyter notebook (ipynb) files that contain visualizations of the data.

## Documentation:
All documentation for the bot is on Notion in Tech -> Documentation -> Slack Bot

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
 
 
