# notion-analytics/bot
Created by Tyler Kotler (tylerk1004@gmail.com), Summer 2020

## Structure:
**1. slack_bot.py** -> It is a Flask app that takes in slash commands on Slack and handles reqests through the front end webpage of the bot, which can be found at https://notion-slackbot.herokuapp.com/ . Here, the s3 files are listed and can be downloaded (instead of having to go through the aws website).

**2. command_hub.py** -> It is the central hub for all commands. The slack_bot file takes in the commands and sends them to the command hub, where it parses out the subcommands and dynamically finds, sends, and receives information from the command and subcommand files. It also handles the "help" and "subcommands" inputs, sending back information from the bot's documentation on Notion.

**3. commands and subcommands folders** -> Each command and subcommand has it's own python file, which allows it to be dynamically located and called by the command hub. They handle receiving, executing, and sending back the information needed to complete the commands.

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
 
 
