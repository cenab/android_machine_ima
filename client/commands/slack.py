import asyncio
import logging

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

    await asyncio.sleep(0.5)  # Small delay to ensure the command has time to execute

async def start_messenger():
    await run_adb_command("adb shell input keyevent KEYCODE_HOME")
    await run_adb_command("adb shell am start -n com.Slack/.launch.StartActivity --activity-brought-to-front")

async def tap_first_groupchat():
    await run_adb_command("adb shell input tap 125 800")

async def tap_textbar():
    await run_adb_command("adb shell input tap 626 2136")

async def fill_textbar(text):
    """Fills the text bar with the specified text."""
    # Clear the current text (optional, based on your initial command)
    await run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")
    # Replace spaces with "\ " to properly handle them in ADB shell input
    formatted_text = text.replace(" ", "\\ ")
    # Send the formatted text to the device
    await run_adb_command(f'adb shell input text "{formatted_text}"')

async def open_general_channel():
    await run_adb_command("adb shell input tap 260 333")
    await run_adb_command("adb shell input text 'general'")
    await run_adb_command("adb shell input tap 420 335")

async def send_message():
    await run_adb_command("adb shell input tap 1000 2136")

async def send_slack_message(message, executed):
    try:
        await start_messenger()
        if not executed:
            await open_general_channel()
        await tap_textbar()
        await fill_textbar(message)
        await send_message()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
