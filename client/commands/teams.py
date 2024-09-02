import os

def run_adb_command(command):
    os.system(command)

def open_teams():
    """ Launches the Skype app. """
    run_adb_command("adb shell input keyevent KEYCODE_HOME")
    run_adb_command("adb shell monkey -p com.microsoft.teams -c android.intent.category.LAUNCHER 1")
    run_adb_command("adb pull $(adb shell uiautomator dump | grep -oP '[^ ]+.xml') /tmp/view.xml")
    coordiates = """coords=$(perl -ne 'printf "%d %d\n", ($1+$3)/2, ($2+$4)/2 if /text="OK"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"/' /tmp/view.xml)"""
    run_adb_command(coordiates)
    run_adb_command("adb shell input tap $coords")

def click_second_conversation():
    """ Clicks on the second conversation. """
    run_adb_command("adb shell input tap 480 646")

def click_textbox():
    """ Clicks on the text box for input. """
    run_adb_command("adb shell input tap 1038 2123")

def fill_textbox(text):
    """ Fills the text box with the specified text. """
    run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")
    run_adb_command(f'adb shell input text "{text}"')

def click_send_button():
    """ Clicks the send button. """
    run_adb_command("adb shell input tap 1000 2127")
    
def send_teams_message(message, executed):
    open_teams()
    if not executed:
        click_second_conversation()
    click_textbox()
    fill_textbox(message)
    click_send_button()
