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

async def fill_textbar(text):
    """Fills the text bar with the specified text."""
    # Clear the current text (optional, based on your initial command)
    await run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")
    # Replace spaces with "\ " to properly handle them in ADB shell input
    formatted_text = text.replace(" ", "\\ ")
    # Send the formatted text to the device
    await run_adb_command(f'adb shell input text "{formatted_text}"')

async def click_send_button():
    """Clicks the send button."""
    await run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")
    await run_adb_command("adb shell input tap 1000 2127")

async def send_skype_message(message, executed):
    try:
        await open_skype()
        if not executed:
            await click_second_conversation()
        await click_textbox()
        await fill_textbar(message)
        await click_send_button()
        return True
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
        return False