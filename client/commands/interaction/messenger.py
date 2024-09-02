import os

def run_adb_command(command):
    os.system(command)

def start_messenger():
    """ Launches the Messenger app. """
    run_adb_command("adb shell input keyevent KEYCODE_HOME")
    run_adb_command("adb shell monkey -p com.facebook.orca -c android.intent.category.LAUNCHER 1")

def stop_messenger():
    """ Stops the Messenger app. """
    run_adb_command("adb shell am force-stop com.facebook.orca")

def tap_first_groupchat():
    """ Taps the first group chat. """
    run_adb_command("adb shell input tap 125 800")

def tap_textbar():
    """ Taps the text bar for input. """
    run_adb_command("adb shell input tap 626 2136")

def fill_textbar(text):
    """ Fills the text bar with the specified text. """
    run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")
    run_adb_command(f'adb shell input text "{text}"')

def click_send_button():
    """ Clicks the send button. """
    run_adb_command("adb shell input tap 1009 1353")

def press_back_button():
    """ Presses the back button. """
    run_adb_command("adb shell input keyevent 4")

def send_messenger_message(message, executed):
    start_messenger()
    if not executed:
        tap_first_groupchat()
    tap_textbar()
    fill_textbar(message)
    click_send_button()

