import os

def run_adb_command(command):
    os.system(command)

def launch_app():
    """ Launches the Discord app. """
    run_adb_command("adb shell input keyevent KEYCODE_HOME")
    run_adb_command("adb shell monkey -p com.discord -c android.intent.category.LAUNCHER 1")

def fill_textbar(text):
    """ Fills the textbar with the specified text. """
    run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")
    run_adb_command(f'adb shell input text "{text}"')

def tap_click_on_server():
    """ Taps to click on the server. """
    run_adb_command("adb shell input tap 90 343")

def tap_click_on_channel():
    """ Taps to click on the channel. """
    run_adb_command("adb shell input tap 495 587")

def tap_click_on_message_box():
    """ Taps to click on the message box. """
    run_adb_command("adb shell input tap 444 2136")

def tap_send():
    """ Taps to return back from the home screen message box. """
    run_adb_command("adb shell input tap 531 1359")

def click_send_button():
    """ Sends message by pressing enter. """
    run_adb_command("adb shell input keyevent 66")

def send_discord_message(message, executed):
    """ Sends a message to the Discord channel. """
    launch_app()
    if not executed:
        tap_click_on_server()
        tap_click_on_channel()
    tap_click_on_message_box()
    fill_textbar(message)
    click_send_button()