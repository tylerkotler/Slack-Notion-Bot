from slackeventsapi import SlackEventAdapter
import json
import csv
from config import *
from flask import Flask, request, Response, make_response, render_template
from slack import WebClient
from slack.errors import SlackApiError
from notion.client import NotionClient
from notion.collection import CollectionRowBlock
import threading
import requests
import notion_data
import validators
import re


app = Flask(__name__)

slack_client = WebClient(slack_token)
notion_client = NotionClient(token_v2=notion_token_v2)

statuses = {'0. On deck for Brendan': ['Brendan Lind'], 
            '1. Verify Story Need': [],
            '2. Verify Story Structure': [],
            '3. Design Story': [],
            '4. Review Story Design': [],
            '5. Add Top Stories To Estimate Time of Story Week': [],
            '6. Estimate Time of Story': [],
            '7. Verify & Add Top Bugs': [],
            '8. Start This Week (Next up)': [],
            '9. Finish This Week (In Progress)': [],
            '10. Code Review': ['Mike Menne'],
            '11. QA Review': ['Tyler Kotler', 'Slavik'],
            '12. PO Verify (Test UX & Push)': ['Ben', 'Volodymyr Solin'],
            '13. Complete! (On Live)': []
}

@app.route("/slack/move", methods=['POST'])
def move_handler():
    token = request.form.get('token')
    if token == slack_verification_token:
        text = request.form.get('text')
        res = [i for i in range(len(text)) if text.startswith("to ", i)] 
        last_to = res[-1]
        story = str(text[0:(last_to-1)])
        status = ''
        status_num = text.split(" ")[-1]
        for key in statuses.keys():
            if key.startswith(status_num):
                status = key
                break
        if validators.url(story):
            block = notion_client.get_block(story)
            story = block.title
        user = request.form.get('user_id')
        #Use threading to allow move_story and all functions after to execute, but code can return
        #response to slack within 3 seconds to avoid the timeout error
        t = threading.Thread(target=move_story, args=[story, status, user])
        t.setDaemon(False)
        t.start()
        data = {
            "text": f"Moving {story}",
            "response_type": 'in_channel'
        }
        return Response(response=json.dumps(data), status=200, mimetype="application/json")



def move_story(story, status, user):
    row = find_story(story)
    row.set_property('status', status)
    url = notion_client.get_block(row.id).get_browseable_url()
    send_move_message(row, story, status, user, url, "notion_bot_test")
    add_changes_data(story, status, user, row)
    #If the story is completed, trigger the notion_data script to calculate all the
    #status times and update the spreadsheet
    if status.startswith('13'):
        print("Running notion data calculations")
        print()
#         notion_data.main()

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


def add_changes_data(story, status, user, row):
    change_made_by = slack_client.users_info(user=user)["user"]["real_name"]
    changeView = notion_client.get_collection_view("https://www.notion.so/humanagency/a11ad18166f445e694c64037fbfd7d5b?v=67d6efa07c224fdc89603e1d9eb6ad5d")
    change_row = changeView.collection.add_row()
    change_row.title = f"{story} to {status}"
    change_row.status = status
    change_row.change_made_by = change_made_by
    story_block = notion_client.get_block(row.id)
    new_CR_block = CollectionRowBlock(notion_client, story_block.id)
    change_row.story = new_CR_block


def send_move_message(row, story, status, user, url, channel):
    additional_string = add_to_message(row, story, status)
    user_id = slack_client.users_info(user=user)["user"]["id"]
    status_names = statuses.get(status)
    slack_users = slack_client.users_list()
    tag_string = ''
    for slack_user in slack_users["members"]:
        real_name = slack_user.get('real_name')
        if real_name in status_names:
            slack_id = slack_user.get('id')
            tag_string = tag_string+f"<@{slack_id}>"+" "
    message_back = f"<@{user_id}> moved {story} to {status} " + tag_string + "\n" + url
    if additional_string!="":
        message_back = message_back + "\n" + additional_string
    slack_client.chat_postMessage(
          channel=channel,
          text=message_back
    )

#Customizeable additions to the message sent in slack based on the column its moving to
def add_to_message(row, story, status):
    #10 -> Gets github pull request
    additional_info = ""
    if status.startswith("10") or status.startswith("12"):
        pr = row.get_property("github_pull_requests_2")
        additional_info = additional_info + pr.split("]")[0][1:] + " "
    #11 -> Gets review app link
    if status.startswith("11"):
        review_app = row.get_property("review_app_link")
        additional_info = additional_info + review_app.split("]")[0][1:] + " "
    return additional_info


@app.route("/slack/authorize", methods=['GET'])
def authenticate():
    return render_template("authorize.html")

# Start the server on port 3000
if __name__ == "__main__":
  app.run()
