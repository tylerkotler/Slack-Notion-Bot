import move
from config import notion_token_v2, slack_token
from notion.client import NotionClient
from slack import WebClient

notion_client = NotionClient(token_v2=notion_token_v2)
slack_client = WebClient(slack_token)

def main(command_info, subcommand_info):
    story = command_info.get('story')
    slack_names = command_info.get('slack_names')
    user = command_info.get('user')

    users_cv = notion_client.get_collection_view("https://www.notion.so/humanagency/8daf88aa8e384105b1a8cab2c100b731?v=97fca2b55bea4173a8ec8bbba8c8ba49")
    assigned_users = []
    for row in users_cv.collection.get_rows():
        for slack_name in slack_names:
            if row.slack_real_name == slack_name:
                assigned_users.extend(row.notion_user)
    story_row = move.find_story(story)
    story_row.set_property("assign", assigned_users)
    url = notion_client.get_block(story_row.id).get_browseable_url()
    send_assign_message(story, slack_names, user, url, subcommand_info, "slack_bot_test")


def send_assign_message(story, slack_names, user, url, subcommand_info, channel):
    tag_string = move.get_tag_string(slack_names).strip("\n")
    user_id = slack_client.users_info(user=user)["user"]["id"]
    message_back = f"<@{user_id}> assigned " + tag_string + f"to *{story}*\n" + url
    if 'note' in subcommand_info:
        message_back = message_back + "\n" + "Note: " + subcommand_info.get('note')
    slack_client.chat_postMessage(
          channel=channel, 
          text=message_back
    )