import os

def run_adb_command(command):
    os.system(command)

def open_skype():
    """ Launches the Skype app. """
    run_adb_command("adb shell input keyevent KEYCODE_HOME")
    run_adb_command("adb shell monkey -p com.skype.raider -c android.intent.category.LAUNCHER 1")

def click_second_conversation():
    """ Clicks on the second conversation. """
    run_adb_command("adb shell input tap 480 1141")

def click_textbox():
    """ Clicks on the text box for input. """
    run_adb_command("adb shell input tap 340 2119")

def fill_textbox(text):
    """ Fills the text box with the specified text. """
    run_adb_command(f'adb shell input text "{text}"')

def click_send_button():
    """ Clicks the send button. """
    run_adb_command("adb shell input tap 1000 2127")

def click_back_button():
    """ Simulates pressing Ctrl+Backspace to delete text and then the Back key. """
    run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")

def send_skype_message(message, executed):
    open_skype()
    if not executed:
        click_second_conversation()
    click_textbox()
    fill_textbox(message)
    click_send_button()
