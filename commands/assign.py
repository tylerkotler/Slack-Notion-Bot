import sys, os
sys.path.append(os.path.realpath(".."))
#pylint: disable=import-error
from commands import move
from config import notion_token_v2, slack_token
from notion.client import NotionClient
from slack import WebClient

notion_client = NotionClient(token_v2=notion_token_v2)
slack_client = WebClient(slack_token)

#Receives command and subcommand info for assign command
def main(command_info, subcommand_info):
    story = command_info.get('story')
    slack_names = command_info.get('slack_names')
    user = command_info.get('user')

    users_cv = notion_client.get_collection_view("https://www.notion.so/humanagency/8daf88aa8e384105b1a8cab2c100b731?v=97fca2b55bea4173a8ec8bbba8c8ba49")
    
    assigned_users = []
    #Gets the Notion User objects based on Slack names
    for row in users_cv.collection.get_rows():
        for slack_name in slack_names:
            if row.slack_real_name == slack_name:
                assigned_users.extend(row.notion_user)
    #Find story row object from Notion API
    story_row = move.find_story(story)
    #Assign users
    story_row.set_property("assign", assigned_users)
    url = notion_client.get_block(story_row.id).get_browseable_url()

    #Send back automatic message in Slack
    if 'quiet' not in subcommand_info:
        send_assign_message(story, slack_names, user, url, subcommand_info, "dev-experience")
    else:
        print("Message in slack turned off")

#Sends automatic message in Slack
def send_assign_message(story, slack_names, user, url, subcommand_info, channel):
    tag_string = move.get_tag_string(slack_names).strip("\n")
    user_id = slack_client.users_info(user=user)["user"]["id"]
    message_back = f"<@{user_id}> assigned " + tag_string + f"to *{story}*"

    #Adds additional info to message
    if 'message' in subcommand_info:
        message_back = message_back + "\n" + subcommand_info.get('message')
    
    message_back = message_back + "\n" + url
    
    slack_client.chat_postMessage(
          channel=channel, 
          text=message_back
    )
