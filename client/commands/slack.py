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
    await run_adb_command("adb shell monkey -p com.facebook.orca -c android.intent.category.LAUNCHER 1")

async def stop_messenger():
    await run_adb_command("adb shell am force-stop com.facebook.orca")

async def tap_first_groupchat():
    await run_adb_command("adb shell input tap 125 800")

async def tap_textbar():
    await run_adb_command("adb shell input tap 626 2136")

async def fill_textbar(text):
    await run_adb_command(f'adb shell input text "{text}"')

async def click_send_button():
    await run_adb_command("adb shell input tap 1009 1353")

async def press_back_button():
    await run_adb_command("adb shell input keyevent 4")

async def return_to_home_screen():
    await run_adb_command("adb shell input keyevent KEYCODE_HOME")

async def open_slack():
    await run_adb_command("adb shell am start -n com.Slack/slack.features.home.HomeActivity")

async def tap_dm_channel():
    await run_adb_command("adb shell input tap 330 2180")

async def tap_dm_search():
    await run_adb_command("adb shell input tap 572 403")

async def search_dm_channel(channel):
    formatted_channel = channel.replace(" ", "%s").replace("'", "\\'")
    await run_adb_command(f'adb shell input text "{formatted_channel}"')

async def open_general_channel():
    await run_adb_command("adb shell input tap 260 423")

async def hide_keyboard():
    await run_adb_command("adb shell input keyevent KEYCODE_BACK")
