from config import notion_token_v2
from notion.client import NotionClient

notion_client = NotionClient(token_v2=notion_token_v2)

def main(command):
    documentation = notion_client.get_block("https://www.notion.so/humanagency/Slack-Bot-Dwayne-42cf24713efb437b9feeb2195c64491e")

    help_output = ""
    for child in documentation.children:
        if f'/{command}' in child.title:
            for subchild in child.children:
                if 'Summary:' in subchild.title:
                    summary = subchild
                    help_output = help_output + subchild.title
                    for summary_child in summary.children:
                        help_output = help_output + "\n - " + summary_child.title
    help_output = help_output + f"\n\nFor information on subcommands, input /{command} subcommands"
    return help_output