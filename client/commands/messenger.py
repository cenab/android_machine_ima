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

async def start_messenger():
    """Launches the Messenger app."""
    await run_adb_command("adb shell input keyevent KEYCODE_HOME")
    await run_adb_command("adb shell am start -n com.facebook.orca/.auth.StartScreenActivity --activity-brought-to-front")

async def tap_textbar():
    """Taps the text bar for input."""
    await asyncio.sleep(2)
    await run_adb_command("adb shell input tap 550 2146")

async def fill_textbar(text):
    """Fills the text bar with the specified text."""
    # Clear the current text (optional, based on your initial command)
    await run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")
    # Replace spaces with "\ " to properly handle them in ADB shell input
    formatted_text = re.sub(r'[^a-zA-Z ]', '', text).replace(" ", "\\ ")
    # Send the formatted text to the device
    await run_adb_command(f'adb shell input text "{formatted_text}"')
    await asyncio.sleep(2)


async def click_send_button():
    """Clicks the send button."""
    await run_adb_command("adb shell input tap 1009 2136")

async def send_messenger_message(message, executed):
    await start_messenger()
    await tap_textbar()
    await fill_textbar(message)
    await click_send_button()
