# Commands handler

# Take in command and subcommand
# build array with subcommands that need to be executed in main commands file (like adding note)
# each has a variable/name -> then figure send it to the correct command py file handler
# maybe have dict of some sort

#Have dict like this: {tag: "[people being tagged]", message: "off"}

# rest of subcommands have their own files

# create folder called commands with py files of all main commands (change move_story to move)
# create folder called subcommands with py files of all subcommands
import importlib.util
from config import notion_token_v2
from notion.client import NotionClient

def main(command, command_info, subcommands):
    subcommand_info = get_subcommand_info(subcommands, command_info)
    command_file = module_from_file(f'{command}.py', f'{command}.py')
    command_file.main(command_info, subcommand_info)


def get_subcommand_info(subcommands, command_info):
    subcommand_info = {}
    for item in subcommands:
        subcommand = item.split(" ")[0]
        subcommand = check_alias(subcommand)
        if len(item.split(" ")) > 1:
            text = " ".join(item.split(" ")[1:])
        else:
            text = subcommand
        subcommand_file = module_from_file(f'{subcommand}.py', f'subcommands/{subcommand}.py')
        output = subcommand_file.main(text)
        if 'data' in output:
            data_needed = output.get('data')
            data_collected = {
                'text': text
            }
            for item in data_needed:
                data_collected[item] = command_info.get(item)
            subcommand_file.handler(data_collected)
        if 'output' in output:
            output_to_send = output.get('output')
        else:
            output_to_send = None
        subcommand_info[subcommand] = output_to_send
    return subcommand_info


def module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

aliases = {
    'mute': 'quiet'
}

def check_alias(alias):
    command = alias
    if alias in aliases:
        command = aliases.get(alias)
    return command


notion_client = NotionClient(token_v2=notion_token_v2)

def help(send_data):
    command = send_data.get('command')
    help_needed = send_data.get('help')
    page_link = "https://www.notion.so/humanagency/Slack-Bot-Dwayne-42cf24713efb437b9feeb2195c64491e"
    documentation = notion_client.get_block(page_link)

    if help_needed == 'subcommands':
        return get_subcommand_help(documentation, page_link)
    else:
        return get_command_help(command, page_link, documentation)
    

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