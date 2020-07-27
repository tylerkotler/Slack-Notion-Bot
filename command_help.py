from config import notion_token_v2
from notion.client import NotionClient

notion_client = NotionClient(token_v2=notion_token_v2)

def main(send_data):
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
                    help_output = help_output + subchild.title
                    for summary_child in summary.children:
                        help_output = help_output + "\n -- " + summary_child.title
    help_output = help_output + f"\n\nFind full documentation on /{command} command here: {page_link}"
    help_output = help_output + f"\n\nFor information on subcommands, input /{command} subcommands"
    return help_output

def get_subcommand_help(documentation, page_link):
    help_output = ""
    for child in documentation.children:
        if 'Subcommands' in child.title:
            for subchild in child.children:
                if 'Syntax' in subchild.title:
                    syntax = subchild
                    for item in syntax.children:
                        help_output = help_output + item.title
                        for example in item.children:
                            help_output = help_output + "\n -- " + example.title
                    help_output = help_output + "\n\nSubcommands:\n"
                if 'Subcommands' in subchild.title:
                    subcommands = subchild
                    subcommand_count = 1
                    for subcommand in subcommands.children:
                        help_output = help_output + str(subcommand_count) + ". " + subcommand.title
                        for subcommand_child in subcommand.children:
                            help_output = help_output + "\n -- " + subcommand_child.title
                            for subcommand_child2 in subcommand_child.children:
                                help_output = help_output + "\n    -- " + subcommand_child2.title
                        help_output = help_output + "\n"
    help_output = help_output + f"\n\nFind full documentation on subcommands here: {page_link}"
    return help_output

                