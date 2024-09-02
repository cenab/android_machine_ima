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

async def open_teams():
    """Launches the Teams app and handles the 'OK' button click if necessary."""
    await run_adb_command("adb shell input keyevent KEYCODE_HOME")
    await run_adb_command("adb shell monkey -p com.microsoft.teams -c android.intent.category.LAUNCHER 1")
    await run_adb_command("adb pull $(adb shell uiautomator dump | grep -oP '[^ ]+.xml') /tmp/view.xml")
    
    coordinates_script = (
        "coords=$(perl -ne 'printf \"%d %d\\n\", ($1+$3)/2, ($2+$4)/2 "
        "if /text=\"OK\"[^>]*bounds=\"\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]\"/' /tmp/view.xml)"
    )
    await run_adb_command(coordinates_script)
    await run_adb_command("adb shell input tap $coords")

async def click_second_conversation():
    """Clicks on the second conversation."""
    await run_adb_command("adb shell input tap 480 646")

async def click_textbox():
    """Clicks on the text box for input."""
    await run_adb_command("adb shell input tap 1038 2123")

async def fill_textbox(text):
    """Fills the text box with the specified text."""
    await run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")
    await run_adb_command(f'adb shell input text "{text}"')

async def click_send_button():
    """Clicks the send button."""
    await run_adb_command("adb shell input tap 1000 2127")
    
async def send_teams_message(message, executed):
    await open_teams()
    if not executed:
        await click_second_conversation()
    await click_textbox()
    await fill_textbox(message)
    await click_send_button()