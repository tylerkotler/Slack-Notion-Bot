from slack import WebClient
import sys, os
sys.path.append(os.path.realpath(".."))
from config import slack_token

slack_client = WebClient(slack_token)

#Returns the note text
def main(text):
    text_copy = text
    #replace all tags with the tag to send back to slack
    #IE: @tyler -> <@4625929>
    at_count = text.count("@")
    for i in range(0, at_count):
        if "@" in text_copy:
            user_start = text_copy.index("@")
        else:
            break
        user_end = user_start+1
        end = False
        while True:
            if user_end == len(text):
                end = True
                break
            if text[user_end]!=" " and text[user_end]!="@":
                user_end+=1
            else:
                break
        if end:
            user = text[user_start:]
        else:
            user = text[user_start:user_end]
        slack_users = slack_client.users_list()
        tag_string = ''
        for slack_user in slack_users["members"]:
            name = slack_user.get('name')
            if name == user.strip("@"):
                slack_id = slack_user.get('id')
                tag_string = f"<@{slack_id}>"
        text = text.replace(user, tag_string)
        tag_string = tag_string.replace("@", "$")
        text_copy = text_copy.replace(user, tag_string)

    return {'output': text}
