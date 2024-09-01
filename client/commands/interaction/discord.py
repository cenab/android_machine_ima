import os

def launch_app():
    os.system("adb shell input keyevent KEYCODE_HOME")
    os.system("adb shell monkey -p com.discord -c android.intent.category.LAUNCHER 1")

def input_email(email="batu.bora389@gmail.com"):
    os.system(f'adb shell input text "{email}"')

def tap_login():
    os.system("adb shell input tap 550 2150")  # login

def tap_email():
    os.system("adb shell input tap 428 588")    # email

def tap_password():
    os.system("adb shell input tap 250 750")    # password

def tap_login_enter():
    os.system("adb shell input tap 531 1082")    # login_enter

def tap_click_on_server():
    os.system("adb shell input tap 90 343")      # click_on_server

def tap_click_on_channel():
    os.system("adb shell input tap 495 587")     # click_on_channel

def tap_click_on_message_box():
    os.system("adb shell input tap 444 2136")    # click_on_message_box

def tap_returning_back():
    os.system("adb shell input tap 531 1359")    # returning-back-from-home-screen-message-box
