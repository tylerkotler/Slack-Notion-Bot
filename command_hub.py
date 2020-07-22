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

def main(command, command_info, subcommands):
    subcommand_info = get_subcommand_info(subcommands)
    command_file = module_from_file(f'{command}.py', f'{command}.py')
    command_file.main(command_info, subcommand_info)


def get_subcommand_info(subcommands):
    subcommand_info = {}
    for item in subcommands:
        subcommand = item.split(": ")[0]
        text = item.split(": ")[1]
        subcommand_file = module_from_file(f'{subcommand}.py', f'subcommands/{subcommand}.py')
        output = subcommand_file.main(text)
        subcommand_info[subcommand] = output
    return subcommand_info


def module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

if __name__ == "__main__":
    command = "test_hub"
    command_info = {'story': "Zapier OAuth"}
    subcommands = ["note: my extra note"]
    main(command, command_info, subcommands)