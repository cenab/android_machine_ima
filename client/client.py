import socketio
import json
import uuid
import asyncio
from typing import Dict, Any
import os

from .commands.discord import send_discord_message
from .commands.messenger import send_messenger_message
from .commands.signal import send_signal_message
from .commands.skype import send_skype_message
from .commands.slack import send_slack_message
from .commands.teams import send_teams_message
from .commands.telegram import send_telegram_message
from .commands.rocket import send_rocketchat_message
from .collectors.tcp.tcp_dump_manager import TcpDumpManager
from .collectors.ports.network_stats_collector import NetworkStatsCollector

EXECUTED_LIST: Dict[str, bool] = {
    'discord': True,
    'messenger': True,
    'signal': True,
    'skype': True,
    'slack': True,
    'teams': True,
    'telegram': True,
    'rocketchat': True
}

sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("Connected to server")
    await sio.emit('ready', json.dumps({"event": "ready", "data": {"status": "ready"}}))

@sio.event
async def disconnect():
    print("Disconnected from server")

@sio.event
async def execute_command(data: Dict[str, Any]):
    try:
        command_data = data['data']
        command_id = command_data['command_id']
        command = command_data['command']
        result = await execute_command_impl(command)
        await sio.emit('command_result', {
            "device_id": device_id,
            "command_id": command_id,
            "result": result
        })
        # Wait for the specified time before processing the next command
        wait_time = command.get('wait_time', 5)
        await asyncio.sleep(wait_time)
    except Exception as e:
        print(f"An error occurred: {str(e)}")

async def execute_command_impl(command: Dict[str, Any]) -> Dict[str, Any]:
    try:
        platform = command.get('platform')
        character = command.get('character', '')
        dialogue = command.get('dialogue', '')
        if platform and dialogue:
            message = f"{character}: {dialogue}"
            result = await post_message_to_the_chat(message, platform)
            return {"status": "success", "output": result.stdout if result else ""}
        else:
            return {"status": "failure", "error": "Invalid command structure"}
    except Exception as e:
        return {"status": "failure", "error": str(e)}

async def post_message_to_the_chat(message: str, platform: str):
    executed = EXECUTED_LIST[platform]
    platform_functions = {
        'discord': send_discord_message,
        'messenger': send_messenger_message,
        'signal': send_signal_message,
        'skype': send_skype_message,
        'slack': send_slack_message,
        'teams': send_teams_message,
        'telegram': send_telegram_message,
        'rocketchat': send_rocketchat_message
    }
    if platform in platform_functions:
        result = await platform_functions[platform](message, executed)
        EXECUTED_LIST[platform] = True
        return result
    else:
        print("Unsupported platform")
        return None

def stop_collectors(port_collector: NetworkStatsCollector, tcpdump_manager: TcpDumpManager):
    port_collector.stop()
    tcpdump_manager.stop_tcpdump()

async def main():
    print("Starting client")
    global device_id
    device_id = str(uuid.uuid4())
    port_collector = NetworkStatsCollector()
    tcpdump_manager = TcpDumpManager()

    # Start collectors
    port_collector.start()
    tcpdump_manager.run_tcpdump()

    # Connect to the server via SocketIO
    server_ip = os.environ.get('SERVER_IP', 'default_ip_here')
    await sio.connect(f'ws://{server_ip}:5000?device_id={device_id}')
    await sio.wait()

    # Stop collectors on exit
    stop_collectors(port_collector, tcpdump_manager)

if __name__ == "__main__":
    asyncio.run(main())