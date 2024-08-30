import subprocess
import shlex

def call_shell_function(function_name, *args):
    script_path = '/Users/batu/Desktop/project_dal/android_pcap_data_collection_and_analysis/user_interaction/user_interaction_functions.sh'
    # Properly escape all arguments to safely include them in a shell command
    escaped_args = ' '.join(shlex.quote(str(arg)) for arg in args)
    command = f'source {script_path}; {function_name} {escaped_args}'
    result = subprocess.run(['bash', '-c', command], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error executing {function_name}: {result.stderr}")
    else:
        print(f"{function_name} executed successfully: {result.stdout}")
    return result.stdout, result.stderr

#TODO: Implement the following functions better for extensive management of the user interaction functions
def open_general_chat_from_home_screen(channel):
    return call_shell_function('openGeneralChatFromHomeScreen', channel)

def post_message_to_the_chat(message):
    return call_shell_function('postMessageToTheChat', message)

def return_to_home_screen():
    return call_shell_function('returnToHomeScreen')
