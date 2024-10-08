import asyncio
import logging
import re

logging.basicConfig(level=logging.INFO)

async def run_adb_command(command):
    logging.info(f"Executing: {command}")
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode == 0:
        logging.info(f"Command succeeded: {stdout.decode().strip()}")
    else:
        logging.error(f"Command failed: {stderr.decode().strip()}")

    await asyncio.sleep(2)  # Small delay to ensure the command has time to execute

async def launch_app():
    """ Launches the Discord app. """
    await run_adb_command("adb shell input keyevent KEYCODE_HOME")
    await run_adb_command("adb shell am start -n com.discord/.main.MainActivity --activity-brought-to-front")

async def tap_textbar():
    """Taps the text bar for input."""
    await asyncio.sleep(2)
    await run_adb_command("adb shell input tap 626 2136")

async def fill_textbar(text):
    """Fills the text bar with the specified text."""
    # Clear the current text (optional, based on your initial command)
    await run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")
    # Replace spaces with "\ " to properly handle them in ADB shell input
    formatted_text = re.sub(r'[^a-zA-Z ]', '', text).replace(" ", "\\ ")
    # Send the formatted text to the device
    await run_adb_command(f'adb shell input text "{formatted_text}"')
    await asyncio.sleep(2)

async def tap_click_on_server():
    """ Taps to click on the server. """
    await run_adb_command("adb shell input tap 90 343")

async def tap_click_on_channel():
    """ Taps to click on the channel. """
    await run_adb_command("adb shell input tap 495 587")

async def tap_click_on_message_box():
    """ Taps to click on the message box. """
    await run_adb_command("adb shell input tap 444 2136")

async def click_send_button():
    """ Sends message by pressing enter. """
    await run_adb_command("adb shell input tap 987 2124")

async def send_discord_message(message, executed):
    """ Sends a message to the Discord channel. """
    try:
        await launch_app()
        await tap_click_on_message_box()
        await fill_textbar(message)
        await click_send_button()
        return True
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
        return False