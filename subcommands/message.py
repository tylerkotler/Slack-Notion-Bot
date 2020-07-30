from slack import WebClient
import sys, os
sys.path.append(os.path.realpath(".."))
from config import slack_token

slack_client = WebClient(slack_token)

#replace all tags with the tag to send back to slack
#IE: @slavik -> <@U014ED431CK>
#Return the text
def main(text):
    #Use a copy of the text because when @slavik gets replaced with <@U014ED431CK>, 
    #we want to be able to find the next user using the search for the @ sign
    #Therefore, the text_copy updates but replaces <@U014ED431CK> with <$U014ED431CK>
    #just to avoid the @ sign. The real text with the replacements is sent back though.
    text_copy = text
    #Finds the number of tagged users
    at_count = text.count("@")

    #pylint: disable=unused-variable

    #Iterates for number of tagged users
    for i in range(0, at_count):
        #Finds the start index of the tagged user
        if "@" in text_copy:
            user_start = text_copy.index("@")
        else:
            break
        user_end = user_start+1
        end = False
        #Finds the end index of the tagged user
        while True:
            if user_end == len(text):
                end = True
                break
            if text[user_end]!=" " and text[user_end]!="@":
                user_end+=1
            else:
                break
        #If tagged user is the last part of the text:
        if end:
            user = text[user_start:]
        else:
            user = text[user_start:user_end]

        #Get slack IDs and build tag string based on Slack names
        slack_users = slack_client.users_list()
        tag_string = ''
        for slack_user in slack_users["members"]:
            name = slack_user.get('name')
            if name == user.strip("@"):
                slack_id = slack_user.get('id')
                tag_string = f"<@{slack_id}>"

        #Replace text with the tag string 
        text = text.replace(user, tag_string)

        #Replace copy with the edited tag string to avoid @ sign in search
        tag_string = tag_string.replace("@", "$")
        text_copy = text_copy.replace(user, tag_string)

    return {'output': text}
