from slack import WebClient
from config import slack_token

def main(text):
    slack_client = WebClient(slack_token)
    users = text[text.index("@"):].split(" ")
    users = [s.strip("@") for s in users]
    slack_users = slack_client.users_list()
    slack_names = []
    for slack_user in slack_users["members"]:
        name = slack_user.get('name')
        if name in users:
            slack_names.append(slack_user.get('real_name'))
    return {'output': slack_names}