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

async def launch_app():
    """ Launches the Discord app. """
    await run_adb_command("adb shell input keyevent KEYCODE_HOME")
    await run_adb_command("adb shell monkey -p com.discord -c android.intent.category.LAUNCHER 1")

async def fill_textbar(text):
    """ Fills the textbar with the specified text. """
    await run_adb_command("adb shell input keyevent 67")  # Clear any existing text
    await run_adb_command(f'adb shell input text "{text}"')

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
    await run_adb_command("adb shell input keyevent 66")

async def send_discord_message(message, executed):
    """ Sends a message to the Discord channel. """
    try:
        await launch_app()
        if not executed:
            await tap_click_on_server()
            await tap_click_on_channel()
        await tap_click_on_message_box()
        await fill_textbar(message)
        await click_send_button()
        return True
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
        return False