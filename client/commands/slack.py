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
    await run_adb_command("adb shell input keyevent KEYCODE_HOME")
    await run_adb_command("adb shell am start -n com.Slack/slack.features.home.HomeActivity --activity-brought-to-front")

async def tap_textbar():
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

async def send_message():
    await run_adb_command("adb shell input tap 1000 2136")

async def send_slack_message(message, executed):
    try:
        await start_messenger()
        await tap_textbar()
        await fill_textbar(message)
        await send_message()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
