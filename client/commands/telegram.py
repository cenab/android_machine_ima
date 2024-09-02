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
    """Launches an app using its package name."""
    await run_adb_command("adb shell input keyevent KEYCODE_HOME")
    await run_adb_command("adb shell monkey -p org.telegram.messenger.web -c android.intent.category.LAUNCHER 1")

async def click_on_first_messager():
    """Simulates a tap on the screen at the specified coordinates."""
    await run_adb_command("adb shell input tap 428 358")

async def type_message(message):
    """Types a given message on the device."""
    await run_adb_command("adb shell input keycombination 113 29 && adb shell input keyevent 67")
    await run_adb_command(f'adb shell input text "{message}"')

async def send_message():
    """Simulates a tap on the send button coordinates."""
    await run_adb_command("adb shell input tap 987 2124")

async def send_telegram_message(message, executed):
    await launch_app()
    if not executed:
        await click_on_first_messager()
    await type_message(message)
    await send_message()