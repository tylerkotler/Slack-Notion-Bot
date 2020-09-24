# Slack-Notion-Bot
Created by Tyler Kotler (tylerk1004@gmail.com), Summer 2020


**Description**

I created this Slack bot for the development team for Human Agency, the start-up I interned for during the summer of 2020. The bot is a Python Flask app that is deployed on Heroku. The team uses Notion to keep track of their stories. The purpose of the bot was to help automate the team's workflow, making moving and manipulating stories on Notion easier while also collecting data to understand how long stories were taking in each stage of production.

**Details of Use/Operation**

Using the Slack API, the Slack bot recognizes commands sent in Slack and uses the Notion API to automate moving and manipulating stories on the team's Notion dashboard. It parses the command's message, accesses the story on Notion, and makes the necessary change. It sends back messages in Slack to update the team of the movement or change, including adding relevant links, notes, and tags of people. I also created a library of subcommands that can be added onto main commands, such as adding your own note to the bot's automated message back in Slack, editing a detail of the story on Notion, or even turning off the message sent back in Slack. With each movement into a new stage of production, the bot is also collecting data on times of movements in order to calculate hours spent in each stage of production. When a story is completed (moved into the last column), the time data is calculated into hours, updated, and directly added to a Google Sheet using the Sheets API. Finally, I created a front end webpage for the app that allows for visualizing the data for times spent in each stage of production and accessing files of time data. 


## Structure:
(Note: Everything from here to the bottom is from the README I wrote up for the Human Agency repo)

**1. slack_bot.py** -> It is a Flask app that takes in slash commands on Slack and handles reqests through the front end webpage of the bot. Here, the s3 files are listed and can be downloaded (instead of having to go through the aws website).

**2. command_hub.py** -> It is the central hub for all commands. The slack_bot file takes in the commands and sends them to the command hub, where it parses out the subcommands and dynamically finds, sends, and receives information from the command and subcommand files. It also handles the "help" and "subcommands" inputs, sending back information from the bot's documentation on Notion.

**3. commands and subcommands folders** -> Each command and subcommand has it's own python file, which allows it to be dynamically located and called by the command hub. They handle receiving, executing, and sending back the information needed to complete the commands.

**4. data folder** -> It has the notion_data script, which is run every time a story moves to column 13. This script pulls the changes data off Notion, calculates status times, and uploads it to csvs in AWS s3 and Google Sheets. It also has the display data script, which has a scatter function to build the bokeh plots of hours over time in each status that are on the webpage.

## Documentation:
All documentation for using the bot is on Notion in Tech -> Documentation -> Slack Bot

## Credentials:
All credentials are stored as config variables in the notion-slackbot app on Heroku, where the app is deployed. They are all obtained in the config file.

**1. Notion token_v2**
  - Found by inspecting the HA Notion page and going to the Application tab
  
**2. Google Sheets**
  - All credentials came directly from the Google Sheets API authorization process
  - Used to get access to HA Google Sheets in notion_data and write data into the sheets
  
**3. Slack**
 - These come from the Slack API through Tech and Marketing for Good's slack apps
 
 **4. AWS S3**
  - There is a S3 Key and Secret that are found in the human-agency-slackbot bucket.
 
 
