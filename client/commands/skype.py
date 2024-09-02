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

async def open_skype():
    """Launches the Skype app."""
    await run_adb_command("adb shell input keyevent KEYCODE_HOME")
    await run_adb_command("adb shell monkey -p com.skype.raider -c android.intent.category.LAUNCHER 1")

async def click_second_conversation():
    """Clicks on the second conversation."""
    await run_adb_command("adb shell input tap 480 1141")

async def click_textbox():
    """Clicks on the text box for input."""
    await run_adb_command("adb shell input tap 340 2119")

async def fill_textbox(text):
    """Fills the text box with the specified text."""
    await run_adb_command(f'adb shell input text "{text}"')

async def click_send_button():
    """Clicks the send button."""
    await run_adb_command("adb shell input tap 1000 2127")

async def click_back_button():
    """Simulates pressing Ctrl+Backspace to delete text and then the Back key."""
    await run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")

async def send_skype_message(message, executed):
    try:
        await open_skype()
        if not executed:
            await click_second_conversation()
        await click_textbox()
        await fill_textbox(message)
        await click_send_button()
        return True
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
        return False