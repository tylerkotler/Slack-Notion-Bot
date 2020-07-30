import sys, os
sys.path.append(os.path.realpath(".."))
#pylint: disable=import-error
from config import slack_token, notion_token_v2
from data import notion_data
import slack_bot
from notion.client import NotionClient
from notion.collection import CollectionRowBlock
from notion.collection import NotionDate
from slack import WebClient
from slack.errors import SlackApiError
import datetime
import re
import csv

slack_client = WebClient(slack_token)
notion_client = NotionClient(token_v2=notion_token_v2)

#Receives command and subcommand info
def main(command_info, subcommand_info):
    story = command_info.get('story')
    status = command_info.get('status')
    user = command_info.get('user')

    #Gets the Notion API row structure of the story
    row = find_story(story)
    #Changes the status -> moves the story
    row.set_property('status', status)
    url = notion_client.get_block(row.id).get_browseable_url()

    #If quiet is not in subcommand info, automatic message will be sent
    if 'quiet' not in subcommand_info:
        #Moved card to status 6-13 -> send message to dev-experience
        if int(status.split(".")[0])>=6:
            channel = "dev-experience"
            send_move_message(row, story, status, user, url, subcommand_info, channel)
        #Moved card to status 3 -> send message to mnm-humanagency
        elif int(status.split(".")[0])==3:
            channel = "mnm-humanagency"
            send_move_message(row, story, status, user, url, subcommand_info, channel)
        #Moved card to status 0-2, 4-5 -> send message to design-review-ha
        else:
            channel = "design-review-ha"
            send_move_message(row, story, status, user, url, subcommand_info, channel)
    else:
        print("Message in slack turned off")
    
    #Add the changes data in the Changes Table
    add_changes_data(story, status, user, row)

    #If the story is completed, trigger the notion_data script to calculate all the
    #status times and update the spreadsheet
    #Also update the ship date to today
    if status.startswith('13'):
        today = datetime.date.today()
        date_obj = NotionDate(start=today)
        row.set_property('ship_date', date_obj)
        print("Running notion data calculations")
        print()
        notion_data.main()

#Searches through the Notion Product Lineup to find the story
def find_story(story):
    cv = notion_client.get_collection_view("https://www.notion.so/humanagency/53a3254e681e4eb6ab53e037d0b2f451?v=68afa83bf93f4c57aa38ffd807eb3bf1")
    story_changed = remove_chars(story)
    for row in cv.collection.get_rows():
        row_story = str(row.story)
        row_story = remove_chars(row_story)
        if row_story == story_changed:
            return row

#Function to remove all non-alphanumeric characters from the story name
#This is because if a story included quotes in its name, python's strings compare was not 
#recognizing slack's and notion's strings of the story name to be the same (slack's quotes are italicized)
#Removing just the quotes failed because python couldn't recognize slack's qoutes
#Thus, the code removes all non-alphanumeric characters, which was able to remove slack's quotes
def remove_chars(story):
    pattern = re.compile(r'[\W_]+')
    story = pattern.sub('', story)
    return story

#Add the changes data -> creates new row in the table
def add_changes_data(story, status, user, row):
    change_made_by = slack_client.users_info(user=user)["user"]["real_name"]
    changeView = notion_client.get_collection_view("https://www.notion.so/humanagency/a11ad18166f445e694c64037fbfd7d5b?v=67d6efa07c224fdc89603e1d9eb6ad5d")
    change_row = changeView.collection.add_row()
    change_row.title = f"{story} to {status}"
    change_row.status = status
    change_row.change_made_by = change_made_by
    story_block = notion_client.get_block(row.id)
    #Notion API Collection Row Block is created in order to get the linked story in the Story column
    new_CR_block = CollectionRowBlock(notion_client, story_block.id)
    change_row.story = new_CR_block

#Sends the automatic message in Slack
def send_move_message(row, story, status, user, url, subcommand_info, channel):
    user_id = slack_client.users_info(user=user)["user"]["id"]
    #Gets the automatically tagged people
    status_names = slack_bot.statuses.get(status)
    
    #get assigned developers on Notion card if story moves to 9
    if status.startswith("9"): 
        assigned = row.get_property("assign")
        users_cv = notion_client.get_collection_view("https://www.notion.so/humanagency/8daf88aa8e384105b1a8cab2c100b731?v=97fca2b55bea4173a8ec8bbba8c8ba49")
        for user in assigned:
            for row in users_cv.collection.get_rows():
                if row.title == user.full_name:
                    status_names.append(row.slack_real_name)
    
    tag_string = ''
    if status_names:
        #Get the string of users who should be tagged -> uses their ID's instead of Slack real name
        tag_string = get_tag_string(status_names)
    
    message_back = f"<@{user_id}> moved:\n*{story}*\nto _*{status}*_" + tag_string 

    #Add to message sent in Slack
    if 'message' in subcommand_info:
        message_back = message_back + "\n" + subcommand_info.get('message')

    message_back = message_back + "\n" + url

    #Get additional info sent in message, such as github pr or review app
    additional_string = add_to_message(row, story, status)
    if additional_string!="":
        message_back = message_back + "\n" + additional_string

    #Send back message
    slack_client.chat_postMessage(
          channel=channel,
          text=message_back
    )

#Takes in slack real names and formats string with their IDs to tag them in Slack message
def get_tag_string(status_names):
    firstTag = True
    slack_users = slack_client.users_list()
    tag_string = ''
    for slack_user in slack_users["members"]:
        real_name = slack_user.get('real_name')
        if real_name in status_names:
            if firstTag:
                tag_string = tag_string + "\n"
                firstTag = False
            slack_id = slack_user.get('id')
            tag_string = tag_string+f"<@{slack_id}>"+" "
    return tag_string

#Customizeable additions to the message sent in slack based on the column its moving to
def add_to_message(row, story, status):
    #10 -> Gets github pull request
    additional_info = ""
    if status.startswith("10") or status.startswith("12"):
        pr = row.get_property("github_pr")
        if pr != "":
            additional_info = additional_info + pr.split("]")[0][1:] + " "
        else:
            additional_info = additional_info + ":warning: Github PR is missing :warning:"
    #11 -> Gets review app link
    if status.startswith("11"):
        review_app = row.get_property("review_app")
        if review_app != "":
            additional_info = additional_info + review_app.split("]")[0][1:] + " "
        else:
            additional_info = additional_info + ":warning: Review app link is missing :warning:"
    if status.startswith("13"):
        additional_info = additional_info + ":bangbang::smiley::robot_face::tada::rocket::fire::bangbang:"
    return additional_info
