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
    run_adb_command(f'adb shell input text "{text}"')

def click_send_button():
    """ Clicks the send button. """
    run_adb_command("adb shell input tap 1009 1353")

def press_back_button():
    """ Presses the back button. """
    run_adb_command("adb shell input keyevent 4")

def return_to_home_screen():
    """ Returns to the home screen. """
    run_adb_command("adb shell input keyevent KEYCODE_HOME")

def open_slack():
    """ Launches the Slack app. """
    run_adb_command("adb shell am start -n com.Slack/slack.features.home.HomeActivity")

def tap_dm_channel():
    """ Taps the direct message channel. """
    run_adb_command("adb shell input tap 330 2180")

def tap_dm_search():
    """ Taps the direct message search bar. """
    run_adb_command("adb shell input tap 572 403")

def search_dm_channel(channel):
    """ Searches for a direct message channel. """
    formatted_channel = channel.replace(" ", "%s").replace("'", "\\'")
    run_adb_command(f'adb shell input text "{formatted_channel}"')

def open_general_channel():
    """ Opens the general channel. """
    run_adb_command("adb shell input tap 260 423")

def hide_keyboard():
    """ Hides the keyboard. """
    run_adb_command("adb shell input keyevent KEYCODE_BACK")