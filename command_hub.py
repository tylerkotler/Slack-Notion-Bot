
import importlib.util
from config import notion_token_v2, slack_token
from notion.client import NotionClient
from slack import WebClient

#Commands handler
#All commands with subcommands are sent through here and then sent out to their respective files

#Takes in the command name, the info for that command, and all subcommands with their info attached
def main(command, command_info, subcommands):
    subcommand_info = get_subcommand_info(subcommands, command_info)
    command_file = module_from_file(f'{command}.py', f'commands/{command}.py')
    command_file.main(command_info, subcommand_info)

#Run through the subcommands, pull out the info after each subcommand
def get_subcommand_info(subcommands, command_info):
    subcommand_info = {}
    for item in subcommands:
        subcommand = item.split(" ")[0]
        subcommand = check_alias(subcommand)

        #Check if subcommand has any info that was inputted after the subcommand
        if len(item.split(" ")) > 1:
            text = " ".join(item.split(" ")[1:])
        else:
            text = subcommand

        #Dynamically find the subcommand and call its main function with the info 
        subcommand_file = module_from_file(f'{subcommand}.py', f'subcommands/{subcommand}.py')
        #Receive back the output from the subcommand file's main method
        output = subcommand_file.main(text)

        #If data in output, extra information is needed
        #That info is pulled from the command info and sent back to the subcommand file's handler
        #This is because there is some action that is executed for the subcommand that is external 
        #to the main command, such as adding the github pr to the card when a story is moved
        if 'data' in output:
            data_needed = output.get('data')
            data_collected = {
                'text': text
            }
            for item in data_needed:
                data_collected[item] = command_info.get(item)
            subcommand_file.handler(data_collected)
        
        #Output from the subcommand that is sent to the main command's file
        #This is because it is info that is executed internally to the main command's function, such as
        #adding a customized additional message to the bot's automatic message sent in Slack after a story
        #is moved
        if 'output' in output:
            output_to_send = output.get('output')
        
        else:
            output_to_send = None
        subcommand_info[subcommand] = output_to_send
    return subcommand_info

#helper function to dynamically find command and subcommand files
def module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

#Aliases for subcommands
#Add them here!
aliases = {
    'mute': 'quiet'
}

#Checks if subcommand is an alias -> if it is, send back the actual subcommand to help with 
#finding the file
def check_alias(alias):
    subcommand = alias
    if alias in aliases:
        subcommand = aliases.get(alias)
    return subcommand


notion_client = NotionClient(token_v2=notion_token_v2)

#Main help function -> receives input, and calls either the command help or subcommand help functions
#Sends back the information in Slack
def help(send_data):
    command = send_data.get('command')
    help_needed = send_data.get('help')
    page_link = "https://www.notion.so/humanagency/Slack-Bot-Dwayne-42cf24713efb437b9feeb2195c64491e"
    documentation = notion_client.get_block(page_link)

    slack_client = WebClient(slack_token)
    message_back = ''
    if help_needed == 'subcommands':
        message_back = get_subcommand_help(documentation, page_link)
    else:
        message_back = get_command_help(command, page_link, documentation)
    slack_client.chat_postMessage(
          channel=send_data.get('channel'),
          text=message_back
    )

#Gets help for the specific command entered
#Pulls it off the Slack Bot documentation page in Notion
#Uses the Summary section of the commands' documentation -> follows a block with children structure
#If the documentation is updated, make sure this still works
def get_command_help(command, page_link, documentation):
    help_output = ""
    for child in documentation.children:
        if f'/{command}' in child.title:
            for subchild in child.children:
                if 'Summary:' in subchild.title:
                    summary = subchild
                    help_output = help_output + subchild.title + "\n"
                    for summary_child in summary.children:
                        help_output = help_output + "\n -- " + summary_child.title + "\n"
    help_output = help_output + f"\n\nFind full documentation on `/{command}` command here: {page_link}"
    help_output = help_output + f"\n\nFor information on subcommands, input: `/{command} subcommands`"
    return help_output


#Gets help for the specific subcommand entered
#Pulls it off the Slack Bot documentation page in Notion
#Follows a block with children structure
#If the documentation is updated, make sure this still works
def get_subcommand_help(documentation, page_link):
    help_output = ""
    for child in documentation.children:
        if 'Subcommands' in child.title:
            for subchild in child.children:
                if 'Syntax' in subchild.title:
                    syntax = subchild
                    for item in syntax.children:
                        help_output = help_output + "_*" + item.title + "*_"
                        for example in item.children:
                            help_output = help_output + "\n ->" + example.title
                    help_output = help_output + "\n\n_*Subcommands:*_\n"
                if 'Subcommands' in subchild.title:
                    subcommands = subchild
                    subcommand_count = 1
                    for subcommand in subcommands.children:
                        title = subcommand.title.replace("**", "*")
                        title = title.replace("__", "*")
                        help_output = help_output + str(subcommand_count) + ". " + title
                        subcommand_count+=1
                        for subcommand_child in subcommand.children:
                            help_output = help_output + "\n -- " + subcommand_child.title
                            for subcommand_child2 in subcommand_child.children:
                                help_output = help_output + "\n    -- " + subcommand_child2.title
                        help_output = help_output + "\n"
    help_output = help_output + f"\n\nFind full documentation on subcommands here: {page_link}"

    return help_output