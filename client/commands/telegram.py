import os

def run_adb_command(command):
    os.system(command)

def launch_app():
    """ Launches an app using its package name. """
    run_adb_command("adb shell input keyevent KEYCODE_HOME")
    run_adb_command("adb shell monkey -p org.telegram.messenger.web -c android.intent.category.LAUNCHER 1")

def click_on_first_messager():
    """ Simulates a tap on the screen at the specified coordinates. """
    run_adb_command("adb shell input tap 428 358")

def type_message(message):
    """ Types a given message on the device. """
    # Replace spaces with '%s' for adb command compatibility
    run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")
    run_adb_command(f'adb shell input text "{message}"')

def send_message():
    """ Simulates a tap on the send button coordinates. """
    # Assuming the send button coordinates are fixed
    run_adb_command("adb shell input tap 987 2124")


def send_telegram_message(message, executed):
    launch_app()
    if not executed:
        click_on_first_messager()
    type_message(message)
    send_message()