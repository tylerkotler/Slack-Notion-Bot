import sys, os
sys.path.append(os.path.realpath(".."))
import move
import inspect
from slack import WebClient
from config import slack_token, notion_token_v2
#pylint: disable=import-error
from notion.client import NotionClient 


def main(text):
    output = {
        'data': ['story'],
        'output': 'Notion property'
    }
    return output

def assign(row, value):
    slack_client = WebClient(slack_token)

    users = value[value.index("@"):].split(" ")
    users = [s.strip("@") for s in users]
    slack_users = slack_client.users_list()
    slack_names = []
    for slack_user in slack_users["members"]:
        name = slack_user.get('name')
        if name in users:
            slack_names.append(slack_user.get('real_name'))

    notion_client = NotionClient(token_v2=notion_token_v2)

    users_cv = notion_client.get_collection_view("https://www.notion.so/humanagency/8daf88aa8e384105b1a8cab2c100b731?v=97fca2b55bea4173a8ec8bbba8c8ba49")
    assigned_users = []
    for user_row in users_cv.collection.get_rows():
        for slack_name in slack_names:
            if user_row.slack_real_name == slack_name:
                assigned_users.extend(user_row.notion_user)
    row.set_property("assign", assigned_users)

functions = {
    'assign': assign
}

def handler(data):
    story = data.get('story')
    subcommand_text = data.get('text')
    
    row = move.find_story(story)
    if " = " in subcommand_text:
        subcommand_text = subcommand_text.replace(" = ", "=")
    prop = subcommand_text.split("=")[0].lower()
    prop = prop.replace(" ", "_")
    value = subcommand_text.split("=")[1]

    if prop in functions:
        functions[prop](row, value)
    else:
        row.set_property(prop, value)


